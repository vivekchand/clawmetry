<!-- i18n-src:d21bea5161e0 -->
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

**तुमचा एजंट कसा विचार करतो ते पहा.** **३० AI एजंट रनटाइम्स**साठी रिअल-टाइम ऑब्झर्व्हॅबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी २६. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एकच कमांड. शून्य कॉन्फिगरेशन. सर्वकाही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीपासून असलेले एजंट रनटाइम्स ते शोधते,
त्यांना फक्त वाचण्यापुरते (read-only) वापरते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ३० एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स ॲपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**सशुल्क योजनेवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडरमधील स्विचर
प्रत्येक टॅबला त्यांपैकी एकावर पुन्हा केंद्रित करतो.

SDK वापरून स्वतःचा एजंट बनवला आहे? इंटरसेप्टर त्याच्याही LLM कॉल्सचा मागोवा घेतो.
पहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टर्न-बाय-टर्न, रिप्लेसह
- **खर्च आणि टोकन्स**: रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, विसंगती (anomaly) फ्लॅग्ससह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या संदेशांचा लाईव्ह डायग्राम
- **ब्रेन**: घडत असतानाच रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोव्हायडरनुसार आकारलेली विंडो युटिलायझेशन, compaction विरुद्ध बळजबरीने overflow, तसेच आपण प्रत्येक रनटाइमसाठी काय *पाहू शकत नाही* याचा नकाशा ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने खरोखर लोड केलेल्या फाइल्स आणि स्किल्स
- **आरोग्य आणि लॉग्स**: डिस्क, मेमरी, एरर रेट्स, रेट लिमिट्स, लाईव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे रूट केलेले
- **अप्रूव्हल्स**: जोखमीचे टूल कॉल्स चालण्या*आधी* थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाची किंमत

कोणतेही एजंट-तुलना करणारे साधन विश्वास ठेवण्याआधी उत्तर देण्यासारखे दोन प्रश्न.

**ते रनटाइम्समध्ये कॉन्टेक्स्ट-विंडो ब्लोआउट कसे हाताळते?**

युटिलायझेशन टक्केवारी ही ती ज्याने भागली जाते तितकीच प्रामाणिक असते. ClawMetry
प्रत्येक प्रोव्हायडरनुसार विंडोचा आकार [तुम्ही वाचू आणि PR करू शकता अशा टेबलमधून](clawmetry/context_windows.py)
ठरवते, ज्यात Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama आणि GLM समाविष्ट आहेत.
हे सर्व २६ रनटाइम्सना एकाच वेंडरच्या मोजपट्टीने मोजत नाही. हे महत्त्वाचे आहे: Anthropic च्या
200K च्या तुलनेत मोजलेला 300K GPT-5 चा टर्न ">100%, blown" वाटतो, जेव्हा तो प्रत्यक्षात GPT-5
च्या 400K पैकी 75% असतो. तीच मोजपट्टी खरोखर overflow झालेल्या 130K DeepSeek टर्नला आरामदायक
65% म्हणून लपवते.

प्रत्येक विंडो तिच्या स्रोतासह (provenance) येते: `model_table`, `explicit_marker`,
`observed_floor`, किंवा मॉडेल माहीत नसताना प्रामाणिक `default`. अंदाजावर बांधलेला गेज कधीही
लूकअपवर बांधलेल्या गेजइतक्या अधिकाराने रेंडर होत नाही.

ClawMetry काही रनटाइम्सवरच compaction इव्हेंट्स पाहू शकते. म्हणून `GET /api/context-coverage`
प्रत्येक रनटाइमसाठी सांगते की **शून्य म्हणजे "स्वच्छ चालले" की "आपण अंध आहोत"**. जो `0` खरोखर अंध
असल्याचे सूचित करतो, तो तसे सांगतो. [संपूर्ण तपशील](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनचा खर्च किती?**

| मार्ग | तुमच्या एजंटमध्ये जोडले | डीफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व ३० रनटाइम्स) | **0**. वेगळी प्रोसेस, तुमच्या एजंटमध्ये ClawMetry कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलसाठी **+0.44 ms**, म्हणजे 5s कॉलच्या 0.009% | बंद |
| Pre-tool हुक गेट (वॉर्म कॅशे) | 36 ms इंटरप्रीटर फ्लोअरच्या वर, गेटेड टूल कॉलसाठी **+44 ms** | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलसाठी **+9.7 ms** | बंद |

डिमन होस्ट खर्च: **2,762 इव्हेंट्स/सेकंद** इनजेस्ट, डिस्कवर **710 बाइट्स/इव्हेंट**
(100k इव्हेंट्ससाठी 67.7 MB), आणि व्यस्त इन्स्टॉलवर सस्टेन्ड **एका कोरच्या सुमारे 12%**. हा शेवटचा
आकडा आमच्या स्वतःच्या नमूद केलेल्या 5-10% बजेटपेक्षा जास्त आहे, त्यामुळे तो पानावरून वगळण्याऐवजी
पाठलाग करायच्या बगच्या रूपात प्रकाशित केला आहे.

Apple M2 Pro वर `benchmarks/overhead.py` वापरून मोजले. हार्नेस प्रत्येक कंडिशन वेगळ्या प्रोसेसमध्ये
चालवतो, त्यांचा क्रम बदलतो, आणि **राउंड्सचे चिन्ह जुळत नसेल तर आकडा छापण्यास नकार देतो**. तुमच्या
स्वतःच्या मशीनवर एका मिनिटात चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हुक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस CI मध्ये Linux, macOS
आणि Windows वर चालतो. जाणून घेण्यासारखे दोन निकाल: Windows वर प्रॉक्सीची किंमत Linux पेक्षा सुमारे
सातपट जास्त आहे, आणि डिमन सध्या आमच्या स्वतःच्या 5-10% बजेटपेक्षा जास्त, एका कोरच्या सुमारे 12%
सस्टेन करतो. रॉ JSON, पद्धत, आणि अजून काय मोजलेले नाही ते [docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| योजना | यात काय समाविष्ट आहे | किंमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूर्ण डॅशबोर्ड, फक्त लोकल | $0 |
| **Starter** | वरील इतर सर्व रनटाइम्स, फ्लीट व्ह्यू, क्लाउड सिंक | प्रति नोड / महिना $9 |
| **Pro** | Starter + नियंत्रण आणि मूल्यांकन: अप्रूव्हल्स, टूल-रिस्क पॉलिसीज, evals, विसंगती शोध, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, टँपर-एव्हिडंट ऑडिट लॉग | प्रति नोड / महिना $19 |

वार्षिक योजना, Enterprise आणि सध्याचे आकडे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** येथे आहेत. सेल्फ-होस्टेड
लायसन्स की क्लाउडशिवाय काम करतात (`clawmetry license`). नक्की मोफत/सशुल्क विभागणी
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्याच मशीनवर राहतो

ClawMetry लोकल सेशन फाइल्स आणि लॉग्स वाचते. **तुम्ही `clawmetry connect` चालवत नाही तोपर्यंत कोणताही
सेशन डेटा तुमच्या बॉक्सबाहेर जात नाही** — कोणतेही प्रॉम्प्ट्स, रिप्लाय, टूल आर्ग्युमेंट्स, फाइल कंटेंट
किंवा लॉग लाईन्स नाहीत. तुम्ही कनेक्ट केल्यावर, स्नॅपशॉट अशा कीने एंड-टू-एंड एन्क्रिप्ट केला जातो जी
तुमच्या मशीनवरून कधीही बाहेर जात नाही, आणि तुमच्या ब्राउझरमध्ये डिक्रिप्ट केली जाते. नोडकडे की
नसल्यास, अपलोड स्पष्ट (unencrypted) पाठवण्याऐवजी वगळला जातो, आणि कोणताही सर्व्हर प्रतिसाद हे बंद करू शकत नाही.

तुम्ही कनेक्ट करण्यापूर्वी डीफॉल्टनुसार दोन गोष्टी चालतात, दोन्ही ऑप्ट-आउट करण्यायोग्य आणि कोणत्याही
सेशन डेटाशिवाय: एक निनावी इन्स्टॉल पिंग आणि PyPI विरुद्ध एक व्हर्जन तपासणी. डीफॉल्ट इन्स्टॉल स्टार्टअप
बॅनर लाईनसाठी तुमचा पब्लिक IP देखील एकदा शोधतो. प्रत्येक डेस्टिनेशन, ती काय वाहून नेते आणि ती कशी बंद
करायची याची यादी [docs/EGRESS.md](docs/EGRESS.md) मध्ये आहे; सेल्फ-होस्टेड, रीपॉइंटेड आणि एअर-गॅप्ड
इन्स्टॉल्स कोणतेही ऐच्छिक आउटबाउंड कॉल्स करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये, आम्ही तुम्हाला पुरवलेल्या कोडमध्ये होते. आधी हे फक्त एक आश्वासन होते;
आता तुम्ही ते तपासू शकता. तुमच्या कीला स्पर्श करणारी प्रत्येक ओळ एकाच वाचनीय फाइलमध्ये आहे,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), जी wheel च्या आत शिप होते आणि जशीच्या
तशी सर्व्ह केली जाते, Subresource Integrity हॅशसह पिन केलेली. ब्राउझर आम्ही प्रकाशित केलेलेच चालवतो
याची खात्री करण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: फाइल लोड करणारे पान आम्ही सर्व्ह करतो, त्यामुळे आम्ही वेगळे पान सर्व्ह करू शकतो.
इंटिग्रिटी हॅश तुम्हाला तडजोड झालेल्या CDN पासून सुरक्षित ठेवतात, वेंडरपासून नाही. तुम्हाला जे मिळते ते
म्हणजे कोणताही बदल जाणीवपूर्वक, पान सोर्समध्ये दृश्यमान, आणि कोणीही मिळवू शकेल अशा PyPI वरील आर्टिफॅक्टपेक्षा
वेगळा असावा लागतो. सेल्फ-होस्टिंग किंवा फक्त लोकल राहिल्याने हे अवलंबित्व पूर्णपणे काढून टाकले जाते.

## इन्स्टॉल

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा वन-लायनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ हवे, आणि त्याच मशीनवर किमान एक एजंट रनटाइम हवे.
Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

## डॉक्स

| | |
|---|---|
| [रनटाइम सुसंगतता](docs/compatibility.md) | प्रत्येक अ‍ॅडॅप्टर काय वाचतो, आणि रनटाइम कसे जोडायचे |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोव्हायडर विंडो, compaction विरुद्ध overflow, प्रति-रनटाइम कव्हरेज |
| [ओव्हरहेड](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनची किंमत किती, मोजलेली, ती पुन्हा तयार करण्याच्या हार्नेससह |
| [एन्टायटलमेंट्स](docs/ENTITLEMENTS.md) | मोफत विरुद्ध सशुल्क, टियर मॅट्रिक्स, लायसन्स CLI |
| [अप्रूव्हल्स आणि पॉलिसीज](docs/APPROVALS.md) | प्री-एक्झिक्युशन गेटिंग, रिस्क स्कोअरिंग, फोन अप्रूव्हल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कुठेही ट्रेसेस एक्सपोर्ट करा, कशाहीमधून OTLP इनजेस्ट करा |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः बनवलेल्या एजंट्ससाठी कॉस्ट अट्रिब्युशन |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | Flow मध्ये दाखवलेले चॅट अ‍ॅडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | आतमध्ये हे कसे काम करते; सोर्समधून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | निनावी इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्स, आणि त्या कशा बंद करायच्या |

## स्क्रीनशॉट्स

खालील प्रत्येक आकडा एका खऱ्या मशीनवरचा, read-only, काहीही seed न करता घेतलेला आहे.

**काहीतरी चुकीचे झाल्यावर ते सांगते, फक्त काय झाले ते नाही.**
वर दोन विसंगती बॅनर: दैनिक सरासरीच्या 7x खर्च चालू आहे, आणि 4.2x कॉस्ट स्पाइक. त्याखाली,
अलीकडील 667 पैकी 324 सेशन्स वेस्ट सिग्नल घेऊन आहेत, कारणानुसार यादीबद्ध.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले ते प्रत्येक विंडोमध्ये दाखवते.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, प्रत्येकामागील टोकन्ससह आणि तुमची
सबस्क्रिप्शन आधीच किती कव्हर करते यासह. त्याखाली, सुमारे $1,128/महिना पुनर्प्राप्त करण्यायोग्य म्हणून
आणि कॅशे रीयूजने आधीच वाचवलेले $17,256/महिना.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**संदेश उत्तर कसा बनतो ते रेखाटते.**
लाईव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवर आला ते, गेटवे, आत्ता उत्तर देणारा मॉडेल, आणि त्याने
वापरलेले प्रत्येक टूल. काम त्यांच्यामधून जाताना नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एकाच टेबलमध्ये.**
तो काय चालवतो, गेल्या 24 तासांत आणि आयुष्यभरात त्याची किंमत काय, तो शेवटचा कधी दिसला, कोणाच्या
मालकीचा आहे, आणि सबस्क्रिप्शन बिल कव्हर करत आहे का. इथे 14 एजंट्स, 3 सेशन्स काम करत आहेत, 13 शांत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**एका टर्नचा वेळ आणि पैसा टूल-बाय-टूल कुठे गेला ते दाखवते.**
एका खऱ्या सेशनचा एक टर्न: $1.16 मध्ये 11.2 मिनिटांत 11 टूल्स. प्रत्येक Bash कॉल आणि मॉडेल कॉलला
टाइमलाइनवर स्वतःची बार मिळते, त्यामुळे 4.1 मिनिटे चाललेली कमांड आणि 226ms चाललेली कमांड एका
नजरेत वेगळी ओळखता येते.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**काम मूल्यांकित करते, फक्त खर्च नाही.**
या आठवड्यात A: 54 कामे स्वच्छ पूर्ण झाली, 2 अवघड कामांची किंमत $48.57 झाली, आणि निर्णय
घेण्याइतकी क्रिया नसलेल्या रन्सना विजय म्हणून मोजण्याऐवजी ग्रेडमधून वगळले जाते. प्रत्येक अवघड रन
त्याच्या ट्रेसकडे लिंक करतो.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो सतत का भरत राहते ते दाखवते.**
शेवटच्या टर्नवर 1M-टोकन विंडोपैकी 715K, 83.3% पीक, overflow वर नाही तर proactively फायर झालेली
4 compactions, आणि त्यामागील प्रत्येक टर्नचे युटिलायझेशन.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता डिटेक्शन चालते.**
इन्स्टॉलपासूनच बिल्ट-इन डिटेक्टर्स चालू आहेत: एजंट शांत झाला, टेलिमेट्री फीड थांबला, कॉस्ट स्पाइक,
टोकन बर्स्ट, एरर्स वाढत आहेत, एरर स्पाइक, बजेट थ्रेशोल्ड, थ्रेट सिग्नेचर जुळला, सिक्युरिटी टूल फाइंडिंग,
सिक्युरिटी पोश्चर बदलला. तुमचे स्वतःचे नियम त्यावर पर्यायी आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीचा कॉल थांबवणे ऑप्ट-इन आहे, आणि बंद अवस्थेत शिप होते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुश, sudo, सिक्रेट्स, पॅकेज इन्स्टॉल्स आणि आउटबाउंड कॉल्स — प्रत्येकाला
तुम्ही चालू करू शकता असा नियम आहे. तुम्ही तो चालू करेपर्यंत, ClawMetry फक्त पाहते आणि काहीही बदलत
नाही. एकदा चालू केल्यावर, जुळणारे कॉल्स इथे (किंवा तुमच्या फोनवर) मंजुरी किंवा नकारासाठी थांबतात.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रति रनटाइम: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## स्टार इतिहास

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## परवाना

MIT · [@vivekchand](https://github.com/vivekchand) यांनी बनवले · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
