<!-- i18n-src:a855a14295b0 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एखादा एजंट प्रगती न करता शेकडो टूल कॉल्स करू शकतो.** ClawMetry
तुमचे कोडिंग एजंट आधीच लिहीत असलेल्या सेशन फाइल्स वाचते, आणि टाइमलाइन,
टूल कॉल्स आणि रनटाइम जे काही टोकन व खर्चाचा डेटा उघड करतो तो सर्व एका
दृश्यात आणते — जेणेकरून काम करत असलेली दीर्घ रन आणि अडकलेली रन यातील फरक तुम्ही ओळखू शकता.

**32 AI एजंट रनटाइम्ससोबत** काम करते — Claude Code, OpenAI Codex, Hermes, OpenClaw आणि आणखी 28. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड. ([संपूर्ण यादी](SUPPORTED_RUNTIMES.txt), कॅटलॉगमधून तयार केलेली.)

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीपासून असलेले एजंट
रनटाइम्स ते शोधते, ते फक्त-वाचनासाठी वाचते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इन्स्टॉल करण्यापूर्वी

| | |
|---|---|
| **हे काय करते** | तुमचे एजंट आधीच लिहीत असलेल्या सेशन फाइल्स आणि लॉग्स वाचते. कोणतेही SDK नाही, कोड बदल नाही, तुमच्या ॲपमध्ये इन्स्ट्रुमेंटेशन नाही. |
| **तुम्ही काय पाहता** | सेशन टाइमलाइन, टूल-बाय-टूल रिप्ले, टोकन व खर्चाचे विभाजन, आणि ट्रॅजेक्टरी सिग्नल्स (लूपिंग, वारंवार अपयश) — प्रत्येक रनटाइमनुसार. |
| **काय मोफत आहे** | `pip install clawmetry` कोणत्याही खाते, की किंवा नेटवर्क कॉलशिवाय **OpenClaw, NVIDIA NemoClaw आणि Goose** वाचते. इतर 27 — Claude Code, Codex, Cursor आणि बाकीचे — क्लोज्ड-सोर्स `clawmetry-pro` कंपॅनियनद्वारे वाचले जातात, जे 7-दिवसांच्या ट्रायल किंवा प्लॅनसोबत येते — नेमके विभाजन पाहण्यासाठी [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) पहा. |
| **कशी सुरुवात करावी** | `pip install clawmetry && clawmetry`, नंतर localhost:8900 उघडा. या मशीनवर अजून एजंट नाहीत? `clawmetry --sample` तीन लेबल असलेल्या कृत्रिम सेशन्ससह उघडते. |
| **तुमच्या मशीनमधून काय बाहेर जाते** | `clawmetry connect` चालवल्याशिवाय कोणताही सेशन डेटा बाहेर जात नाही. डीफॉल्टनुसार दोन गोष्टी चालतात, दोन्ही ऑप्ट-आउट करण्यायोग्य आणि दोन्हीमध्ये सेशन कंटेंट नसतो: एक निनावी इन्स्टॉल पिंग आणि एक PyPI व्हर्जन तपासणी. प्रत्येक गंतव्यस्थानाची नोंद [docs/EGRESS.md](docs/EGRESS.md) मध्ये आहे, जी टिप्पण्या वाचण्याऐवजी वायर कॅप्चरवरून पुन्हा तयार केली आहे. |

आउटपुटचा न्याय करण्यापूर्वी जाणून घेण्यासारख्या दोन मर्यादा: रनटाइम्स खूप
वेगवेगळा डेटा उघड करतात (काही तर खर्चच प्रकाशित करत नाहीत — [मॅट्रिक्स](docs/compatibility.md)
प्रत्येक रनटाइमनुसार कोणते ते सांगते), आणि एखादी कृती पाहणे म्हणजे ती
रोखता येणे असे नाही ([कोणते नियंत्रण खरे आहेत, प्रत्येक रनटाइमनुसार](docs/APPROVALS.md)).


## 32 एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स ॲपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**सशुल्क प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडर
स्विचर प्रत्येक टॅबला त्यापैकी एका रनटाइमवर पुन्हा-स्कोप करतो.

एखाद्या SDK वर स्वतःचा एजंट तयार केला आहे का? इंटरसेप्टर त्याचेही LLM कॉल्स
ट्रॅक करतो. पहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टप्प्याटप्प्याने, रिप्लेसह
- **खर्च आणि टोकन्स**: प्रत्येक रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, विसंगती चिन्हांसह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या मेसेजेसचा लाइव्ह डायग्राम
- **ब्रेन**: घडत असतानाचा रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम
- **कॉन्टेक्स्ट ब्लोआउट**: प्रत्येक प्रोव्हायडरनुसार आकारलेला विंडो वापर, कॉम्पॅक्शन वि. सक्तीचा ओव्हरफ्लो, तसेच आपल्याला *काय दिसत नाही* याचा प्रत्येक रनटाइमनुसार नकाशा ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **आरोग्य आणि लॉग्स**: डिस्क, मेमरी, एरर दर, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट मर्यादा, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे राउट केलेले
- **मंजुरी**: जोखमीचे टूल कॉल्स *चालण्यापूर्वीच* थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाची किंमत

कोणतेही एजंट-तुलना टूल विश्वास ठेवण्यायोग्य आहे की नाही हे ठरवण्याआधी उत्तर देण्यासारखे दोन प्रश्न.

**हे रनटाइम्समधील कॉन्टेक्स्ट-विंडो ब्लोआउट कसे हाताळते?**

वापर टक्केवारी ज्याने भागाकार केला जातो तितकीच प्रामाणिक असते. ClawMetry
[तुम्ही वाचू आणि PR करू शकता अशा टेबलमधून](clawmetry/context_windows.py) प्रत्येक
प्रोव्हायडरनुसार विंडो आकारते, ज्यात Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama आणि GLM यांचा समावेश आहे. ते सर्व 32
रनटाइम्सना एकाच वेंडरच्या मोजपट्टीने मोजत नाही. हे महत्त्वाचे आहे: Anthropic च्या
200K विरुद्ध मोजलेला 300K GPT-5 टर्न ">100%, blown" असे दाखवतो जेव्हा तो प्रत्यक्षात
GPT-5 च्या 400K पैकी 75% असतो. तीच मोजपट्टी खरोखर ओव्हरफ्लो झालेला 130K
DeepSeek टर्न आरामशीर 65% म्हणून लपवते.

प्रत्येक विंडोसोबत तिचे मूळ दिले जाते: `model_table`, `explicit_marker`,
`observed_floor`, किंवा मॉडेल माहीत नसताना प्रामाणिक `default`. अंदाजावर
बांधलेला गेज कधीही लूकअपवर बांधलेल्या गेजइतक्या अधिकाराने रेंडर होत नाही.

ClawMetry काही रनटाइम्सवरच कॉम्पॅक्शन इव्हेंट्स पाहू शकते. त्यामुळे
`GET /api/context-coverage` प्रत्येक रनटाइमनुसार सांगते की **शून्य म्हणजे
"स्वच्छ चालले" की "आम्हाला दिसत नाही"**. ज्याचा खरा अर्थ अंध आहे तो `0` तसे सांगतो.
[संपूर्ण तपशील](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनची किंमत काय आहे?**

| मार्ग | तुमच्या एजंटमध्ये जोडलेले | डीफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व 32 रनटाइम्स) | **0**. वेगळी प्रक्रिया, तुमच्या एजंटमध्ये ClawMetry कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलसाठी **+0.44 ms**, म्हणजे 5s कॉलच्या 0.009% | बंद |
| प्री-टूल हुक गेट (वॉर्म कॅशे) | 36 ms इंटरप्रीटर फ्लोअरच्या वर, प्रत्येक गेटेड टूल कॉलसाठी **+44 ms** | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलसाठी **+9.7 ms** | बंद |

डिमन होस्ट खर्च: इनजेस्ट **2,762 इव्हेंट्स/सेकंद**, डिस्कवर **710 बाइट्स/इव्हेंट**
(100k इव्हेंट्सला 67.7 MB), आणि व्यस्त इन्स्टॉलवर सतत **एका कोरचा सुमारे 12%**.
ती शेवटची संख्या आमच्याच नमूद केलेल्या 5-10% बजेटपेक्षा जास्त आहे, त्यामुळे ती
पानावरून वगळण्याऐवजी पाठलाग करण्यासारखी बग म्हणून प्रकाशित केली आहे.

Apple M2 Pro वर `benchmarks/overhead.py` वापरून मोजले. हार्नेस प्रत्येक
अट वेगळ्या प्रक्रियेत चालवतो, त्यांचा क्रम बदलत राहतो, आणि **राऊंड्सचे चिन्ह
जुळत नसेल तर संख्या छापण्यास नकार देतो**. तुमच्या स्वतःच्या मशीनवर एका मिनिटात चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हुक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस
Linux, macOS आणि Windows वर CI मध्ये चालतो. जाणून घेण्यासारखे दोन निकाल:
Windows वर प्रॉक्सीची किंमत Linux च्या तुलनेत सुमारे सात पट जास्त आहे, आणि
डिमन सध्या एका कोरचा सुमारे 12% वापर सतत करतो, जो आमच्याच 5-10% बजेटपेक्षा
जास्त आहे. कच्चा JSON, पद्धत, आणि अजूनही न मोजलेले काय आहे ते
[docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| प्लॅन | यात काय समाविष्ट आहे | किंमत |
|---|---|---|
| **मोफत** | OpenClaw + NVIDIA NemoClaw + Goose, संपूर्ण डॅशबोर्ड, फक्त स्थानिक | $0 |
| **स्टार्टर** | वरील इतर प्रत्येक रनटाइम, फ्लीट व्ह्यू, क्लाउड सिंक | $9 प्रति नोड / महिना |
| **Pro** | स्टार्टर + नियंत्रण आणि मूल्यांकन: मंजुरी, टूल-जोखीम धोरणे, इव्हॅल्स, विसंगती शोध, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, टँपर-एव्हिडंट ऑडिट लॉग | $19 प्रति नोड / महिना |

वार्षिक प्लॅन्स, एंटरप्राइझ आणि सध्याचे आकडे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** वर आहेत. सेल्फ-होस्टेड
लायसन्स की क्लाउडशिवाय काम करतात (`clawmetry license`). अचूक मोफत/सशुल्क विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्याच मशीनवर राहतो

ClawMetry स्थानिक सेशन फाइल्स आणि लॉग्स वाचते. **तुम्ही `clawmetry connect`
चालवल्याशिवाय कोणताही सेशन डेटा तुमच्या मशीनबाहेर जात नाही** — प्रॉम्प्ट्स,
प्रतिसाद, टूल आर्ग्युमेंट्स, फाइल कंटेंट किंवा लॉग लाइन्स काहीही नाही. तुम्ही
कनेक्ट केल्यावर, स्नॅपशॉट एंड-टू-एंड एन्क्रिप्टेड असतो अशा कीसह जी तुमच्या
मशीनबाहेर कधीच जात नाही, आणि तुमच्या ब्राउझरमध्ये डिक्रिप्ट केली जाते. एखाद्या
नोडकडे की नसेल तर, अपलोड स्पष्ट स्वरूपात पाठवण्याऐवजी वगळले जाते, आणि कोणताही
सर्व्हर प्रतिसाद ते बंद करू शकत नाही.

तुम्ही कनेक्ट करण्यापूर्वी डीफॉल्टनुसार दोन गोष्टी चालतात, दोन्ही ऑप्ट-आउट
करण्यायोग्य आणि दोन्हीमध्ये सेशन डेटा नसतो: एक निनावी इन्स्टॉल पिंग आणि
PyPI विरुद्ध एक व्हर्जन तपासणी. डीफॉल्ट इन्स्टॉल स्टार्टअप बॅनर लाइनसाठी
तुमचा सार्वजनिक IP देखील एकदा शोधतो. प्रत्येक गंतव्यस्थान, ते काय वाहून
नेते आणि कसे बंद करावे याची यादी [docs/EGRESS.md](docs/EGRESS.md) मध्ये आहे;
सेल्फ-होस्टेड, रीपॉइंटेड आणि एअर-गॅप्ड इन्स्टॉल्स कोणतेही ऐच्छिक आउटबाउंड कॉल्स
करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये होते, आम्ही तुम्हाला दिलेल्या कोडमध्ये. आधी हे
एक वचन होते; आता ती तुम्ही तपासू शकता अशी गोष्ट आहे. तुमच्या कीला स्पर्श
करणारी प्रत्येक ओळ एका वाचनीय फाइलमध्ये आहे,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), जी
व्हीलच्या आत येते आणि जशीच्या तशी सर्व्ह केली जाते, Subresource Integrity
हॅशसह पिन केलेली. ब्राउझर आम्ही प्रकाशित केलेलेच चालवतो हे पडताळण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: आम्ही फाइल लोड करणारे पान सर्व्ह करतो, त्यामुळे आम्ही
वेगळे पान सर्व्ह करू शकतो. इंटिग्रिटी हॅशेस तुम्हाला तडजोड झालेल्या CDN पासून
वाचवतात, विक्रेत्यापासून नाही. तुम्हाला जे मिळते ते म्हणजे कोणतीही बदली मुद्दाम,
पेज सोर्समध्ये दृश्यमान, आणि PyPI वरील कोणीही मिळवू शकेल अशा आर्टिफॅक्टपेक्षा
वेगळी असावी लागते. सेल्फ-होस्टिंग किंवा फक्त-स्थानिक राहणे ही अवलंबित्व
संपूर्णपणे काढून टाकते.

## इन्स्टॉल

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आणि त्याच मशीनवर किमान एक एजंट
रनटाइम आवश्यक आहे. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

किंवा एजंटला तुमच्यासाठी सेटअप करू द्या. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot किंवा OpenCode यांना
ClawMetry इन्स्टॉल करणे, मशीनवरील एजंट्स काय करत आहेत आणि किती खर्च करत
आहेत ते सांगणे, विनंतीनुसार एखादे सेशन थांबवणे, आणि जोखमीचे टूल कॉल्स
मंजुरीसाठी थांबवणे शिकवते:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## डॉक्युमेंटेशन

| | |
|---|---|
| [रनटाइम सुसंगतता](docs/compatibility.md) | प्रत्येक अडॅप्टर काय वाचतो, आणि रनटाइम कसे जोडावे |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रत्येक प्रोव्हायडरनुसार विंडो, कॉम्पॅक्शन वि. ओव्हरफ्लो, प्रत्येक रनटाइमनुसार कव्हरेज |
| [ओव्हरहेड](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनची किंमत काय आहे, मोजलेली, तेच पुन्हा तयार करण्यासाठीच्या हार्नेससह |
| [एन्टायटलमेंट्स](docs/ENTITLEMENTS.md) | मोफत वि. सशुल्क, टियर मॅट्रिक्स, लायसन्स CLI |
| [मंजुरी आणि धोरणे](docs/APPROVALS.md) | पूर्व-अंमलबजावणी गेटिंग, जोखीम स्कोअरिंग, फोन मंजुरी |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेसेस कुठेही एक्सपोर्ट करा, कशाहीमधून OTLP इनजेस्ट करा |
| [तुमचा स्वतःचा एजंट आणा](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सुरुवातीपासून शेवटपर्यंत, चालवण्यायोग्य उदाहरणांसह |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः तयार केलेल्या एजंट्ससाठी खर्च वाटप |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | Flow मध्ये दाखवलेले चॅट अडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोझ, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | आतून हे कसे काम करते; सोर्समधून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | निनावी इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्स, आणि त्या कशा बंद कराव्यात |

## स्क्रीनशॉट्स

खालील प्रत्येक संख्या एका खऱ्या मशीनवरून आहे, फक्त-वाचनासाठी, काहीही आधीपासून न भरता.

**काहीतरी चुकीचे असल्याचे सांगते, फक्त काय घडले ते नाही.**
शीर्षस्थानी दोन विसंगती बॅनर्स: दैनंदिन सरासरीच्या 7 पट खर्च, आणि
4.2 पट खर्च स्पाइक. त्यांच्या खाली, अलीकडील 667 सेशन्सपैकी 324 मध्ये
वाया जाण्याचे सिग्नल आढळले, कारणानुसार विभागलेले.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले ते दाखवते, प्रत्येक विंडोमध्ये.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, प्रत्येकामागील
टोकन्ससह आणि तुमचे सबस्क्रिप्शन त्यातील किती भाग आधीच कव्हर करते तेही. त्याखाली,
सुमारे $1,128/महिना पुनर्प्राप्त करण्यायोग्य म्हणून वेगळे केलेले आणि कॅशे
पुनर्वापरामुळे आधीच $17,256/महिना बचत झालेली.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**मेसेज उत्तर कसे बनते ते रेखाटते.**
लाइव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवर आला तो चॅनेल, गेटवे, सध्या
उत्तर देणारा मॉडेल, आणि त्याने वापरलेले प्रत्येक टूल. काम त्यांच्यामधून
जाताना नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एका टेबलमध्ये.**
तो काय चालवतो, गेल्या 24 तासांत आणि आयुष्यभरात त्याची किंमत काय आहे,
तो शेवटचा केव्हा दिसला, कोणाच्या मालकीचा आहे, आणि सबस्क्रिप्शन बिल कव्हर
करत आहे का. इथे 14 एजंट्स, 3 सेशन्स काम करत आहेत, 13 शांत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**एका टर्नचा वेळ आणि पैसा टूल-बाय-टूल कुठे गेला ते दाखवते.**
एका खऱ्या सेशनचा एक टर्न: $1.16 मध्ये 11.2 मिनिटांत 11 टूल्स. प्रत्येक
Bash कॉल आणि मॉडेल कॉलला टाइमलाइनवर स्वतःचा बार मिळतो, त्यामुळे 4.1
मिनिटे चाललेली कमांड आणि 226ms चाललेली कमांड एका नजरेत ओळखता येतात.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**काम मोजते, फक्त खर्च नाही.**
या आठवड्यात A: 54 कामे स्वच्छपणे परत आली, 2 खडतर कामांची किंमत $48.57
होती, आणि निर्णयासाठी अपुरी क्रियाकलाप असलेल्या रन्सना विजय म्हणून
मोजण्याऐवजी ग्रेडमधून वगळले जाते. प्रत्येक खडतर रन त्याच्या ट्रेसकडे लिंक करते.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो का भरत राहते ते दाखवते.**
शेवटच्या टर्नमध्ये 1M-टोकन विंडोपैकी 715K, 83.3% पीक, 4 कॉम्पॅक्शन्स
जे सर्व ओव्हरफ्लोवर नव्हे तर सक्रियपणे झाले, आणि त्यामागील प्रत्येक टर्नचा वापर.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता शोध चालतो.**
इन्स्टॉलपासूनच बिल्ट-इन डिटेक्टर्स चालू आहेत: एजंट शांत झाला, टेलिमेट्री फीड
थांबला, खर्च स्पाइक, टोकन बर्स्ट, वाढत्या एरर्स, एरर स्पाइक, बजेट थ्रेशोल्ड,
थ्रेट सिग्नेचर जुळले, सिक्युरिटी टूल फाइंडिंग, सिक्युरिटी पोश्चर बदलले.
वर तुमचे स्वतःचे नियम ऐच्छिक आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीचा कॉल थांबवणे ऐच्छिक आहे, आणि बंद पाठवले जाते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुश, sudo, सिक्रेट्स, पॅकेज इन्स्टॉल्स आणि आउटबाउंड
कॉल्स यांपैकी प्रत्येकाला तुम्ही चालू करू शकता असा नियम आहे. तुम्ही तसे
करेपर्यंत, ClawMetry फक्त पाहते आणि काहीही बदलत नाही. एकदा चालू केल्यावर,
जुळणारे कॉल्स इथे (किंवा तुमच्या फोनवर) मंजुरी किंवा नकारासाठी थांबतात.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रत्येक रनटाइमनुसार: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ओळख

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## स्टार हिस्टरी

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
