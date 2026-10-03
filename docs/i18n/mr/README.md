<!-- i18n-src:c99ac0512cae -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एखादा एजंट प्रगती न करताच शंभर टूल कॉल्स करू शकतो.** ClawMetry
तुमचे कोडिंग एजंट्स आधीच लिहित असलेल्या सेशन फाइल्स वाचते, आणि टाइमलाइन,
टूल कॉल्स, आणि रनटाइम जे काही टोकन आणि खर्चाचा डेटा उघड करतो तो सर्व एका
दृश्यात आणते — जेणेकरून तुम्ही काम करत असलेली दीर्घ धावण आणि अडकलेली धावण यांच्यात फरक करू शकाल.

**३३ AI एजंट रनटाइम्स** सोबत काम करते — Claude Code, OpenAI Codex, Hermes, OpenClaw आणि आणखी २९. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड. ([संपूर्ण यादी](SUPPORTED_RUNTIMES.txt), कॅटलॉगवरून जनरेट केलेली.)

> 🌐 **हे वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप शोधते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीच असलेले एजंट रनटाइम्स ते शोधते,
त्यांना फक्त वाचते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इन्स्टॉल करण्याआधी

| | |
|---|---|
| **हे काय करते** | तुमचे एजंट्स आधीच लिहित असलेल्या सेशन फाइल्स आणि लॉग्स वाचते. कोणताही SDK नाही, कोड बदल नाही, तुमच्या अॅपमध्ये इन्स्ट्रुमेंटेशन नाही. |
| **तुम्हाला काय दिसते** | सेशन टाइमलाइन, टूल-बाय-टूल रिप्ले, टोकन आणि खर्चाचे विभाजन, आणि ट्रॅजेक्टरी सिग्नल्स (लूपिंग, वारंवार अपयश) — प्रत्येक रनटाइमनुसार. |
| **काय मोफत आहे** | `pip install clawmetry` हे **OpenClaw, NVIDIA NemoClaw, Goose आणि Qwen Code** कोणत्याही खाते, की किंवा नेटवर्क कॉलशिवाय वाचते. इतर २८ — Claude Code, Codex, Cursor आणि बाकीचे — क्लोज्ड-सोर्स `clawmetry-pro` कम्पॅनियनद्वारे वाचले जातात, जे ७ दिवसांच्या ट्रायलसह किंवा एखाद्या प्लॅनसह मिळते — नेमके विभाजन पाहण्यासाठी [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) पहा. |
| **कसे सुरू करावे** | `pip install clawmetry && clawmetry`, नंतर localhost:8900 उघडा. या मशीनवर अजून एजंट्स नाहीत? `clawmetry --sample` तीन लेबल केलेल्या सिंथेटिक सेशन्सवर उघडते. |
| **तुमच्या मशीनमधून काय बाहेर जाते** | तुम्ही `clawmetry connect` चालवल्याशिवाय कोणताही सेशन डेटा बाहेर जात नाही. डीफॉल्टने दोन गोष्टी चालतात, दोन्ही ऑप्ट-आउट करता येण्याजोग्या आणि दोन्हीमध्ये सेशन कंटेंट नसते: एक अनामिक इन्स्टॉल पिंग आणि एक PyPI व्हर्जन तपासणी. प्रत्येक गंतव्यस्थान [docs/EGRESS.md](docs/EGRESS.md) मध्ये सूचीबद्ध आहे, जे टिप्पण्या वाचण्याऐवजी वायर कॅप्चरवरून पुन्हा तयार केले आहे. |

निकाल समजून घेण्याआधी दोन मर्यादा लक्षात घेण्यासारख्या आहेत: रनटाइम्स खूप
वेगवेगळा डेटा उघड करतात (काही तर खर्चच प्रकाशित करत नाहीत — कोणता रनटाइम
काय करतो ते [मॅट्रिक्स](docs/compatibility.md) सांगतो), आणि एखादी क्रिया पाहणे
म्हणजे ती रोखता येणे असे नाही ([कोणते नियंत्रण खरे आहेत, प्रत्येक रनटाइमनुसार](docs/APPROVALS.md)).


## ३३ एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स अॅपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**पेड प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडर
स्विचर प्रत्येक टॅबला त्यांच्यापैकी एकावर पुन्हा स्कोप करतो.

SDK वापरून स्वतःचा एजंट बनवला आहे? इंटरसेप्टर त्याचे LLM कॉल्सही ट्रॅक करतो.
पहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टर्न-बाय-टर्न, रिप्लेसह
- **खर्च आणि टोकन्स**: रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, अॅनोमली फ्लॅग्ससह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या मेसेजेसचा लाइव्ह डायग्राम
- **ब्रेन**: रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम जसजसे घडते तसतसे
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोव्हायडरनुसार मोजलेली विंडो युटिलायझेशन, कॉम्पॅक्शन विरुद्ध फोर्स्ड ओव्हरफ्लो, तसेच आम्हाला *दिसत नाही* ते प्रत्येक रनटाइमनुसार दाखवणारा नकाशा ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **हेल्थ आणि लॉग्स**: डिस्क, मेमरी, एरर दर, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email वर राउट केलेले
- **मंजुरी (Approvals)**: जोखमीचे टूल कॉल्स चालण्याआधीच थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाची किंमत

कोणत्याही एजंट-तुलना टूलवर विश्वास ठेवण्याआधी उत्तर देण्यासारखे दोन प्रश्न.

**ते वेगवेगळ्या रनटाइम्समध्ये कॉन्टेक्स्ट-विंडो ब्लोआउट कसे हाताळते?**

युटिलायझेशन टक्केवारी तितकीच प्रामाणिक असते जितका तो भाग ज्याने विभागला जातो.
ClawMetry Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral,
Llama आणि GLM यांचा समावेश असलेल्या [तुम्ही वाचू आणि PR करू शकता अशा
टेबल](clawmetry/context_windows.py) वरून प्रोव्हायडरनुसार विंडो मोजते. ते
सर्व ३३ रनटाइम्सना एकाच व्हेंडरच्या मोजपट्टीने मोजत नाही. हे महत्त्वाचे
आहे: ३००K GPT-5 टर्न Anthropic च्या २००K विरुद्ध मोजला तर ">१००%, उडाला" असे
वाचते, जेव्हा खरेतर तो GPT-5 च्या ४००K पैकी ७५% असतो. तीच मोजपट्टी खरोखर
ओव्हरफ्लो झालेला १३०K DeepSeek टर्न आरामदायी ६५% म्हणून लपवते.

प्रत्येक विंडो तिच्या प्रोव्हेनन्ससह येते: `model_table`, `explicit_marker`,
`observed_floor`, किंवा आम्हाला मॉडेल माहीत नसताना प्रामाणिक `default`.
अंदाजावर बनलेला गेज कधीही लुकअपवर बनलेल्या गेजइतक्या अधिकाराने दाखवला जात
नाही.

ClawMetry काही रनटाइम्सवर फक्त कॉम्पॅक्शन इव्हेंट्स पाहू शकते. त्यामुळे
`GET /api/context-coverage` प्रत्येक रनटाइमनुसार **शून्याचा अर्थ "स्वच्छ
चालले" की "आम्हाला दिसत नाही"** हे नोंदवतो. खरोखर आंधळा असलेला `0` तसे
सांगतो. [संपूर्ण तपशील](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनची किंमत काय आहे?**

| पद्धत | तुमच्या एजंटमध्ये जोडले जाणारे | डीफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व ३३ रनटाइम्स) | **०**. वेगळी प्रक्रिया, तुमच्या एजंटमध्ये ClawMetry कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलला **+०.४४ ms**, म्हणजे ५s कॉलच्या ०.००९% | बंद |
| प्री-टूल हुक गेट (वॉर्म कॅशे) | ३६ ms इंटरप्रीटर फ्लोअरवर, प्रत्येक गेटेड टूल कॉलला **+४४ ms** | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलला **+९.७ ms** | बंद |

डीमन होस्ट किंमत: **२,७६२ इव्हेंट्स/सेकंद** इनजेस्ट, डिस्कवर **७१० बाइट्स/इव्हेंट**
(१,००,००० इव्हेंट्ससाठी ६७.७ MB), आणि व्यस्त इन्स्टॉलवर सातत्याने
**एका कोरच्या ~१२%**. तो शेवटचा आकडा आमच्याच सांगितलेल्या ५-१०% बजेटपेक्षा
जास्त आहे, त्यामुळे पानावरून काढून टाकण्याऐवजी पाठलाग करण्यासारखा बग म्हणून
प्रकाशित केला आहे.

Apple M2 Pro वर `benchmarks/overhead.py` ने मोजले. हार्नेस प्रत्येक स्थिती
वेगळ्या प्रक्रियेत चालवतो, त्यांचा क्रम बदलतो, आणि **फेऱ्यांमध्ये चिन्हावर
मतभेद असल्यास आकडा छापण्यास नकार देतो**. तुमच्या स्वतःच्या मशीनवर एका
मिनिटात चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हुक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस
CI मध्ये Linux, macOS आणि Windows वर चालतो. माहीत असण्यासारखे दोन निकाल:
प्रॉक्सीची किंमत Windows वर Linux पेक्षा सुमारे सातपट जास्त आहे, आणि डीमन
सध्या आमच्याच ५-१०% बजेटपेक्षा जास्त, एका कोरच्या सुमारे १२% सातत्याने
वापरतो. कच्चा JSON, पद्धत, आणि अजून न मोजलेले काय आहे ते
[docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| प्लॅन | यात काय समाविष्ट आहे | किंमत |
|---|---|---|
| **फ्री** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, संपूर्ण डॅशबोर्ड, फक्त लोकल | $0 |
| **स्टार्टर** | वरील इतर प्रत्येक रनटाइम, फ्लीट व्ह्यू, क्लाउड सिंक | $9 प्रति नोड / महिना |
| **Pro** | स्टार्टर + नियंत्रण आणि मूल्यांकन: मंजुरी, टूल-रिस्क पॉलिसीज, evals, अॅनोमली डिटेक्शन, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, टँपर-एव्हिडंट ऑडिट लॉग | $19 प्रति नोड / महिना |

वार्षिक प्लॅन्स, Enterprise आणि सध्याचे आकडे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** वर आहेत. सेल्फ-होस्टेड
लायसन्स की क्लाउडशिवाय काम करतात (`clawmetry license`). नेमके मोफत/पेड विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्या मशीनवरच राहतो

ClawMetry लोकल सेशन फाइल्स आणि लॉग्स वाचते. **तुम्ही `clawmetry connect`
चालवल्याशिवाय तुमच्या बॉक्समधून कोणताही सेशन डेटा बाहेर जात नाही** — कोणतेही
प्रॉम्प्ट्स, उत्तरे, टूल आर्ग्युमेंट्स, फाइल कंटेंट किंवा लॉग लाइन्स नाहीत.
तुम्ही कनेक्ट केल्यावर, स्नॅपशॉट अशा कीने एंड-टू-एंड एन्क्रिप्टेड असतो जी
तुमच्या मशीनमधून कधीही बाहेर जात नाही, आणि तुमच्या ब्राउझरमध्ये डिक्रिप्ट
केली जाते. एखाद्या नोडकडे की नसेल तर, अपलोड उघडपणे पाठवण्याऐवजी वगळला
जातो, आणि कोणताही सर्व्हर रिस्पॉन्स ते बंद करू शकत नाही.

तुम्ही कनेक्ट करण्याआधी डीफॉल्टने दोन गोष्टी चालतात, दोन्ही ऑप्ट-आउट
करता येण्याजोग्या आणि दोन्हीत सेशन डेटा नसतो: एक अनामिक इन्स्टॉल पिंग आणि
PyPI विरुद्ध एक व्हर्जन तपासणी. डीफॉल्ट इन्स्टॉल स्टार्टअप बॅनर लाइनसाठी
तुमचा सार्वजनिक IP एकदा शोधतो. प्रत्येक गंतव्यस्थान, त्यात काय असते आणि ते
कसे बंद करायचे ते [docs/EGRESS.md](docs/EGRESS.md) मध्ये सूचीबद्ध आहे;
सेल्फ-होस्टेड, पुनर्निर्देशित आणि एअर-गॅप्ड इन्स्टॉल्स कोणतेही ऐच्छिक
आउटबाउंड कॉल्स करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये, आम्ही तुम्हाला पुरवलेल्या कोडमध्ये होते.
हे आधी एक वचन होते; आता ती एक पडताळता येणारी गोष्ट आहे. तुमच्या कीला
स्पर्श करणारी प्रत्येक ओळ एका वाचनीय फाइलमध्ये राहते,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), जी व्हीलच्या
आत येते आणि Subresource Integrity हॅशसह पिन केलेली, जशीच्या तशी दिली जाते.
ब्राउझर आम्ही प्रकाशित केलेलेच चालवतो याची खात्री करण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: आम्ही फाइल लोड करणारे पान सर्व्ह करतो, त्यामुळे आम्ही
वेगळे पान सर्व्ह करू शकतो. इंटिग्रिटी हॅशेस तुम्हाला तडजोड झालेल्या CDN
पासून वाचवतात, व्हेंडरपासून नाही. तुम्हाला जे मिळते ते म्हणजे कोणताही बदल
जाणीवपूर्वक, पानाच्या सोर्समध्ये दिसणारा, आणि कुणीही मिळवू शकेल अशा PyPI
वरील आर्टिफॅक्टपेक्षा वेगळा असावा लागतो. सेल्फ-होस्टिंग किंवा फक्त
लोकल राहणे ही अवलंबित्वच पूर्णपणे काढून टाकते.

## इन्स्टॉल

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा एक-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आवश्यक आहे, आणि त्याच मशीनवर
किमान एक एजंट रनटाइम. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

किंवा एजंटला तुमच्यासाठी ते सेटअप करू द्या. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot किंवा OpenCode ला
ClawMetry इन्स्टॉल करायला, मशीनवरील एजंट्स काय करत आहेत आणि किती खर्च करत
आहेत ते सांगायला, विनंतीनुसार एखादे सेशन थांबवायला, आणि जोखमीचे टूल कॉल्स
मंजुरीसाठी थांबवून ठेवायला शिकवते:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## कागदपत्रे

| | |
|---|---|
| [रनटाइम सुसंगतता](docs/compatibility.md) | प्रत्येक अडॅप्टर काय वाचतो, आणि रनटाइम कसा जोडायचा |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रोव्हायडरनुसार विंडो, कॉम्पॅक्शन विरुद्ध ओव्हरफ्लो, प्रत्येक रनटाइमनुसार कव्हरेज |
| [ओव्हरहेड](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनची किंमत काय आहे, मोजलेली, ती पुन्हा तयार करण्यासाठी हार्नेससह |
| [एन्टायटलमेंट्स](docs/ENTITLEMENTS.md) | मोफत विरुद्ध पेड, टायर मॅट्रिक्स, लायसन्स CLI |
| [मंजुरी आणि पॉलिसीज](docs/APPROVALS.md) | प्री-एक्झिक्युशन गेटिंग, रिस्क स्कोअरिंग, फोन मंजुरी |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कुठेही ट्रेसेस एक्सपोर्ट करा, कुठूनही OTLP इनजेस्ट करा |
| [स्वतःचा एजंट आणा](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain शेवटपर्यंत, चालवता येणाऱ्या उदाहरणांसह |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः बनवलेल्या एजंट्ससाठी खर्चाचे श्रेय |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | फ्लोमध्ये दाखवलेले चॅट अडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | हे आतून कसे काम करते; सोर्सवरून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | अनामिक इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्स, आणि त्या कशा बंद करायच्या |

## स्क्रीनशॉट्स

खालील प्रत्येक आकडा एका खऱ्या मशीनवरून आहे, फक्त-वाचन, काहीही पेरलेले नाही.

**काहीतरी चुकले आहे हे ते सांगते, फक्त काय घडले ते नाही.**
वर दोन अॅनोमली बॅनर्स: दैनंदिन सरासरीच्या ७ पट खर्च चालू आहे, आणि ४.२ पट
कॉस्ट स्पाइक. त्यांच्याखाली, अलीकडील ६६७ पैकी ३२४ सेशन्स वाया जाण्याचा
सिग्नल घेऊन आहेत, कारणानुसार विभागलेले.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले ते ते दाखवते, प्रत्येक विंडोत.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, प्रत्येकामागील
टोकन्ससह आणि तुमचे सबस्क्रिप्शन त्यातील किती भाग आधीच कव्हर करते यासह.
त्याखाली, सुमारे $1,128/महिना परत मिळवता येण्याजोगे आणि कॅशे पुनर्वापराने
आधीच वाचवलेले $17,256/महिना.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**मेसेज उत्तर कसा बनतो ते ते दाखवते.**
लाइव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवरून आला तो, गेटवे, आत्ता उत्तर
देणारा मॉडेल, आणि त्याने वापरलेले प्रत्येक टूल. काम त्यांच्यामधून जाताना
नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एका टेबलमध्ये.**
ते काय चालवते, गेल्या २४ तासांत आणि आजीवन त्याची किंमत किती, शेवटचे कधी
दिसले, कोणाच्या मालकीचे आहे, आणि सबस्क्रिप्शन बिल कव्हर करत आहे का. इथे
१४ एजंट्स, ३ सेशन्स काम करत आहेत, १३ शांत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**एका टर्नचा वेळ आणि पैसा कुठे गेला, टूल-बाय-टूल ते दाखवते.**
एका खऱ्या सेशनचा एक टर्न: ११.२ मिनिटांत ११ टूल्स, $1.16 ला. प्रत्येक Bash
कॉल आणि मॉडेल कॉलला टाइमलाइनवर स्वतःची बार मिळते, त्यामुळे ४.१ मिनिटे
चाललेली कमांड आणि २२६ms चाललेली कमांड एका नजरेत वेगळी ओळखता येते.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ते काम तपासते, फक्त खर्च नाही.**
या आठवड्यात A ग्रेड: ५४ कामे स्वच्छ पूर्ण झाली, २ अवघड कामांना $48.57 खर्च
आला, आणि ग्रेड करण्याइतपत क्रियाकलाप नसलेल्या धावणी विजय म्हणून मोजण्याऐवजी
वगळल्या जातात. प्रत्येक अवघड धावण तिच्या ट्रेसशी लिंक्ड आहे.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो का भरत राहते ते ते दाखवते.**
शेवटच्या टर्नवर १M-टोकन विंडोपैकी ७१५K, ८३.३% शिखर, ४ कॉम्पॅक्शन्स जी सर्व
ओव्हरफ्लोवर नव्हे तर प्रो-अॅक्टिव्हली फायर झाली, तसेच त्यामागील प्रत्येक
टर्नचे युटिलायझेशन.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता डिटेक्शन चालते.**
इन-बिल्ट डिटेक्टर्स इन्स्टॉलपासूनच चालू आहेत: एजंट शांत झाला, टेलिमेट्री
फीड थांबली, कॉस्ट स्पाइक, टोकन बर्स्ट, एरर्स वाढत आहेत, एरर स्पाइक, बजेट
थ्रेशोल्ड, थ्रेट सिग्नेचर जुळले, सिक्युरिटी टूल फाइंडिंग, सिक्युरिटी
पोश्चर बदलली. तुमचे स्वतःचे नियम वरती ऐच्छिक आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीचा कॉल थांबवणे ऐच्छिक आहे, आणि बंद अवस्थेत येते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुश, sudo, सिक्रेट्स, पॅकेज इन्स्टॉल्स आणि
आउटबाउंड कॉल्स यापैकी प्रत्येकासाठी तुम्ही चालू करू शकता असा नियम आहे.
तुम्ही तो चालू करेपर्यंत, ClawMetry फक्त पाहते आणि काहीही बदलत नाही.
एकदा चालू केल्यावर, जुळणारे कॉल्स इथे (किंवा तुमच्या फोनवर) मंजुरी किंवा
नकारासाठी थांबतात.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रत्येक रनटाइमनुसार: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ओळख

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star इतिहास

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## परवाना

MIT · [@vivekchand](https://github.com/vivekchand) यांनी तयार केले · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
