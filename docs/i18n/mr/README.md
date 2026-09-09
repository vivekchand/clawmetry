<!-- i18n-src:61beb8393e2f -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एखादा एजंट प्रगती न करता शंभर टूल कॉल्स करू शकतो.** ClawMetry
तुमचे कोडिंग एजंट आधीच लिहीत असलेल्या सेशन फाइल्स वाचते, आणि टाइमलाइन,
टूल कॉल्स आणि रनटाइम जे काही टोकन व खर्चाचा डेटा उघड करतो तो सर्व एका
दृश्यात आणते — जेणेकरून काम करत असलेली दीर्घ चालणारी रन आणि अडकलेली रन यांत तुम्हाला फरक करता येईल.

**30 AI एजंट रनटाइम्ससोबत** कार्य करते — Claude Code, OpenAI Codex, Hermes, OpenClaw व आणखी 26. तुमच्या संपूर्ण एजंट फ्लीटसाठी एक डॅशबोर्ड. ([संपूर्ण यादी](SUPPORTED_RUNTIMES.txt), कॅटलॉगमधून जनरेट केलेली.)

> 🌐 **हे यात वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप शोधते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** येथे उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीच असलेले एजंट रनटाइम्स ते शोधते,
त्यांना फक्त-वाचनीय (read-only) पद्धतीने वाचते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इन्स्टॉल करण्यापूर्वी

| | |
|---|---|
| **हे काय करते** | तुमचे एजंट आधीच लिहीत असलेल्या सेशन फाइल्स आणि लॉग्ज वाचते. कोणतेही SDK नाही, कोड बदल नाही, तुमच्या अ‍ॅपमध्ये कोणतेही इन्स्ट्रुमेंटेशन नाही. |
| **तुम्हाला काय दिसते** | सेशन टाइमलाइन, टूल-दर-टूल रिप्ले, टोकन व खर्चाचे विभाजन, आणि ट्रॅजेक्टरी सिग्नल्स (लूपिंग, वारंवार होणारे अपयश) — प्रत्येक रनटाइमनुसार. |
| **काय मोफत आहे** | `pip install clawmetry` हे **OpenClaw, NVIDIA NemoClaw आणि Goose** कोणत्याही खात्याशिवाय, की (key) शिवाय आणि नेटवर्क कॉलशिवाय वाचते. उर्वरित 27 — Claude Code, Codex, Cursor आणि बाकीचे — क्लोज्ड-सोर्स `clawmetry-pro` सोबतच्या अ‍ॅपद्वारे वाचले जातात, जे 7-दिवसांच्या ट्रायलसोबत किंवा एखाद्या प्लॅनसोबत येते — नेमकी विभागणी पाहण्यासाठी [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) पहा. |
| **कसे सुरू करावे** | `pip install clawmetry && clawmetry`, त्यानंतर localhost:8900 उघडा. या मशीनवर अजून कोणतेही एजंट नाहीत? `clawmetry --sample` तीन लेबल केलेल्या सिंथेटिक सेशन्सवर उघडते. |
| **तुमच्या मशीनमधून काय बाहेर जाते** | तुम्ही `clawmetry connect` चालवल्याशिवाय कोणताही सेशन डेटा जात नाही. डिफॉल्टनुसार दोनच गोष्टी चालतात, दोन्ही opt-out आहेत आणि दोन्हीत सेशन कंटेंट नसतो: एक अनामिक (anonymous) इन्स्टॉल पिंग आणि एक PyPI व्हर्जन चेक. प्रत्येक गंतव्यस्थान [docs/EGRESS.md](docs/EGRESS.md) मध्ये सूचीबद्ध आहे, जे टिप्पण्या वाचण्याऐवजी वायर कॅप्चरवरून पुन्हा बांधलेले आहे. |

तुम्ही निकालाचा न्याय करण्यापूर्वी जाणून घेण्यासारख्या दोन मर्यादा: रनटाइम्स खूप
वेगवेगळा डेटा उघड करतात (काही तर खर्चच प्रकाशित करत नाहीत — कोणता ते
[matrix](docs/compatibility.md) मध्ये, प्रत्येक रनटाइमनुसार), आणि एखादी क्रिया पाहणे
म्हणजे ती थांबवता येणे असे नाही ([कोणती नियंत्रणे खरी आहेत, प्रत्येक रनटाइमनुसार](docs/APPROVALS.md)).


## 30 एजंट रनटाइम्ससोबत कार्य करते

**ओपन सोर्स अ‍ॅपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडर
स्विचर प्रत्येक टॅबची व्याप्ती त्यांपैकी एकावर पुन्हा निश्चित करतो.

तुम्ही स्वतःचा एजंट एखाद्या SDK वर बांधला आहे का? इंटरसेप्टर त्याचे LLM कॉल्सही
ट्रॅक करतो. पहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टप्प्याटप्प्याने, रिप्लेसह
- **खर्च आणि टोकन्स**: रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, अनोमली फ्लॅग्जसह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या मेसेजेसचा लाइव्ह डायग्राम
- **ब्रेन**: रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम, तो घडत असतानाच
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोव्हायडरनुसार आकारलेले विंडो युटिलायझेशन, कॉम्पॅक्शन विरुद्ध फोर्स्ड ओव्हरफ्लो, तसेच आपण काय *पाहू शकत नाही* याचा प्रत्येक रनटाइमनुसार नकाशा ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **आरोग्य आणि लॉग्ज**: डिस्क, मेमरी, एरर रेट्स, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे रूट केलेले
- **मान्यता (Approvals)**: जोखमीचे टूल कॉल्स चालण्या*आधी* थांबवा आणि तुमच्या फोनवरून मान्य करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाची किंमत

कोणत्याही एजंट-तुलना करणाऱ्या टूलवर विश्वास ठेवण्यापूर्वी उत्तर देण्यासारखे दोन प्रश्न.

**रनटाइम्समध्ये कॉन्टेक्स्ट-विंडो ब्लोआउट ते कसे हाताळते?**

युटिलायझेशन टक्केवारी ती ज्याने भागली जाते तितकीच प्रामाणिक असते. ClawMetry
[तुम्ही वाचू आणि PR करू शकता अशा टेबलवरून](clawmetry/context_windows.py) प्रत्येक प्रोव्हायडरनुसार
विंडो आकार ठरवते, ज्यात Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama आणि GLM यांचा समावेश आहे. ते सर्व 30
रनटाइम्स एकाच व्हेंडरच्या मोजपट्टीने मोजत नाही. हे महत्त्वाचे आहे: Anthropic च्या
200K विरुद्ध मोजलेला 300K GPT-5 टर्न ">100%, फुगलेला" असे दाखवतो, जेव्हा तो
प्रत्यक्षात GPT-5 च्या 400K पैकी 75% असतो. तीच मोजपट्टी खरोखर ओव्हरफ्लो झालेल्या
130K DeepSeek टर्नला आरामदायक 65% म्हणून लपवते.

प्रत्येक विंडो तिच्या स्रोतासह (provenance) येते: `model_table`, `explicit_marker`,
`observed_floor`, किंवा मॉडेल माहीत नसताना एक प्रामाणिक `default`. अंदाजावर
बनवलेला गेज कधीही लूकअपवर बनवलेल्या गेजइतक्या अधिकाराने दाखवला जात नाही.

ClawMetry काही रनटाइम्सवर फक्त कॉम्पॅक्शन इव्हेंट्स पाहू शकते. त्यामुळे
`GET /api/context-coverage` प्रत्येक रनटाइमनुसार अहवाल देते की **शून्य म्हणजे
"स्वच्छ चालले" की "आम्ही अंध आहोत"**. ज्याचा खरा अर्थ अंध असतो असे `0` तसे सांगते.
[सविस्तर माहिती](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनची किंमत काय आहे?**

| मार्ग | तुमच्या एजंटमध्ये जोडलेले | डिफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व 30 रनटाइम्स) | **0**. वेगळी प्रोसेस, तुमच्या एजंटमध्ये ClawMetry कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलसाठी **+0.44 ms**, म्हणजे 5s कॉलच्या 0.009% | बंद |
| प्री-टूल हुक गेट (वॉर्म कॅशे) | प्रत्येक गेटेड टूल कॉलसाठी **+44 ms**, 36 ms इंटरप्रिटर फ्लोरच्या वर | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलसाठी **+9.7 ms** | बंद |

डिमन होस्ट खर्च: **2,762 इव्हेंट्स/सेकंद** इनजेस्ट, डिस्कवर **710 बाइट्स/इव्हेंट**
(100k इव्हेंट्ससाठी 67.7 MB), आणि व्यस्त इन्स्टॉलवर सस्टेन्ड **~12% एक कोर**. तो
शेवटचा आकडा आमच्या स्वतःच्या नमूद केलेल्या 5-10% बजेटपेक्षा जास्त आहे, त्यामुळे तो
पानावरून काढून टाकण्याऐवजी पाठलाग करण्यासारखा बग म्हणून प्रकाशित केला आहे.

Apple M2 Pro वर `benchmarks/overhead.py` सह मोजलेले. हार्नेस प्रत्येक स्थिती
वेगळ्या प्रोसेसमध्ये चालवतो, त्यांचा क्रम बदलतो, आणि **राऊंड्स त्याच्या चिन्हावर सहमत
नसल्यास आकडा छापण्यास नकार देतो**. तुमच्या स्वतःच्या मशीनवर एका मिनिटात चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हुक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस
CI मध्ये Linux, macOS आणि Windows वर चालतो. जाणून घेण्यासारखे दोन निकाल: Windows वर
प्रॉक्सीची किंमत Linux पेक्षा सुमारे सात पट जास्त आहे, आणि डिमन सध्या आमच्या
स्वतःच्या 5-10% बजेटपेक्षा जास्त, सुमारे एक कोरच्या 12% इतका सस्टेन करतो. रॉ JSON,
पद्धत, आणि अजून काय मोजलेले नाही ते [docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| प्लॅन | यात काय समाविष्ट आहे | किंमत |
|---|---|---|
| **मोफत** | OpenClaw + NVIDIA NemoClaw + Goose, संपूर्ण डॅशबोर्ड, फक्त स्थानिक | $0 |
| **Starter** | वरील प्रत्येक इतर रनटाइम, फ्लीट व्ह्यू, क्लाउड सिंक | $9 प्रति नोड / महिना |
| **Pro** | Starter + नियंत्रण आणि मूल्यांकन: मान्यता (approvals), टूल-रिस्क धोरणे, इव्हल्स, अनोमली डिटेक्शन, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, टॅम्पर-एव्हिडंट ऑडिट लॉग | $19 प्रति नोड / महिना |

वार्षिक प्लॅन्स, एंटरप्राइझ आणि सध्याचे आकडे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** येथे आहेत. सेल्फ-होस्टेड लायसन्स
की क्लाउडशिवायही काम करतात (`clawmetry license`). नेमकी मोफत/पेड विभागणी
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्या मशीनवरच राहतो

ClawMetry स्थानिक सेशन फाइल्स आणि लॉग्ज वाचते. तुम्ही `clawmetry connect` चालवल्याशिवाय
**तुमच्या बॉक्समधून कोणताही सेशन डेटा बाहेर जात नाही** — कोणतेही प्रॉम्प्ट्स, उत्तरे,
टूल आर्ग्युमेंट्स, फाइल कंटेंट किंवा लॉग लाइन्स नाहीत. जेव्हा तुम्ही कनेक्ट करता, तेव्हा
स्नॅपशॉट तुमच्या मशीनमधून कधीही न जाणाऱ्या कीने एंड-टू-एंड एन्क्रिप्ट केलेला असतो, आणि
तुमच्या ब्राउझरमध्ये डिक्रिप्ट केला जातो. जर एखाद्या नोडकडे की नसेल, तर अपलोड
स्पष्ट मजकुरात पाठवण्याऐवजी वगळला जातो, आणि कोणताही सर्व्हर रिस्पॉन्स ते बंद करू शकत नाही.

कनेक्ट करण्यापूर्वी डिफॉल्टनुसार दोन गोष्टी चालतात, दोन्ही opt-out आणि कोणतेही
सेशन डेटा वाहून न नेणाऱ्या: एक अनामिक इन्स्टॉल पिंग आणि PyPI विरुद्ध एक व्हर्जन चेक.
डिफॉल्ट इन्स्टॉल स्टार्टअप बॅनर लाइनसाठी तुमचा पब्लिक IP देखील एकदा लूकअप करतो. प्रत्येक
गंतव्यस्थान, ते काय वाहून नेते आणि ते कसे बंद करावे हे
[docs/EGRESS.md](docs/EGRESS.md) मध्ये सूचीबद्ध आहे; सेल्फ-होस्टेड, रीपॉइंटेड आणि एअर-गॅप्ड
इन्स्टॉल्स अजिबात ऐच्छिक (discretionary) आउटबाउंड कॉल्स करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये, आम्ही तुम्हाला दिलेल्या कोडमध्ये होते. आधी हे एक
वचन होते; आता ते तुम्ही तपासू शकता अशी गोष्ट आहे. तुमच्या कीला स्पर्श करणारी प्रत्येक
लाइन एकाच वाचनीय फाइलमध्ये आहे, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
जी व्हीलच्या आत शिप होते आणि जशीच्या तशी सर्व्ह केली जाते, Subresource
Integrity हॅशने पिन केलेली. ब्राउझर आम्ही प्रकाशित केलेलेच चालवतो याची खात्री करण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: आम्ही ती फाइल लोड करणारे पान सर्व्ह करतो, त्यामुळे आम्ही वेगळे
पान सर्व्ह करू शकतो. इंटिग्रिटी हॅशेस तुमचे संरक्षण compromised CDN पासून करतात,
वेंडरपासून नाही. तुम्हाला जे मिळते ते म्हणजे कोणताही बदल हेतुपुरस्सर, पान सोर्समध्ये
दृश्यमान, आणि कोणालाही मिळवता येणाऱ्या PyPI वरील आर्टिफॅक्टपेक्षा वेगळा असावा लागतो.
सेल्फ-होस्टिंग किंवा फक्त-स्थानिक राहणे ही अवलंबित्व पूर्णपणे काढून टाकते.

## इन्स्टॉल

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा एक-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ हवे, आणि त्याच मशीनवर किमान एक एजंट
रनटाइम. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

किंवा एजंटलाच ते तुमच्यासाठी सेट करू द्या. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot किंवा OpenCode ला
ClawMetry इन्स्टॉल करणे, मशीनवरील एजंट्स काय करत आहेत आणि किती खर्च करत आहेत ते सांगणे,
विनंतीनुसार एखादे सेशन थांबवणे, आणि जोखमीचे टूल कॉल्स मान्यतेसाठी थांबवणे शिकवते:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तऐवजीकरण

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | प्रत्येक अ‍ॅडॅप्टर काय वाचतो, आणि रनटाइम कसा जोडावा |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | प्रोव्हायडरनुसार विंडोज, कॉम्पॅक्शन विरुद्ध ओव्हरफ्लो, रनटाइमनुसार कव्हरेज |
| [Overhead](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनची किंमत काय, मोजलेली, ती पुन्हा तयार करण्यासाठीच्या हार्नेससह |
| [Entitlements](docs/ENTITLEMENTS.md) | मोफत विरुद्ध पेड, टियर मॅट्रिक्स, लायसन्स CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एक्झिक्युशन गेटिंग, रिस्क स्कोअरिंग, फोन मान्यता |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेसेस कुठेही एक्सपोर्ट करा, कशाहीमधून OTLP इनजेस्ट करा |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सुरुवातीपासून शेवटपर्यंत, चालवण्यायोग्य उदाहरणांसह |
| [SDK tracking](docs/SDK_TRACKING.md) | तुम्ही स्वतः बनवलेल्या एजंट्ससाठी खर्चाचे श्रेय |
| [Chat channels](docs/CHANNELS.md) | Flow मध्ये दाखवलेले चॅट अ‍ॅडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोझ, व्हॉल्यूम माउंट्स |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | आतून हे कसे काम करते; सोर्सवरून चालवणे |
| [Telemetry](docs/TELEMETRY.md) | अनामिक इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्ज, आणि त्या कशा बंद कराव्यात |

## स्क्रीनशॉट्स

खालील प्रत्येक आकडा एका खऱ्या मशीनवरून, फक्त-वाचनीय, काहीही सीड न करता आहे.

**काहीतरी चुकीचे असल्याचे हे सांगते, फक्त काय घडले तेच नाही.**
वर दोन अनोमली बॅनर्स: सरासरी दैनंदिन खर्चाच्या 7 पट खर्च चालू आहे, आणि
4.2 पट कॉस्ट स्पाइक. त्यांच्या खाली, अलीकडील 667 पैकी 324 सेशन्समध्ये कारणानुसार
वर्गीकृत केलेला वाया गेल्याचा (waste) सिग्नल आहे.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले हे प्रत्येक विंडोमध्ये दाखवते.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, प्रत्येकामागील
टोकन्ससह आणि तुमचे सबस्क्रिप्शन त्यातील किती आधीच कव्हर करते. त्याखाली,
सुमारे $1,128/महिना पुनर्प्राप्त करण्यायोग्य म्हणून सूचीबद्ध आणि कॅशे पुनर्वापरामुळे
आधीच $17,256/महिना वाचवलेले.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**मेसेज उत्तर कसा बनतो हे हे रेखाटते.**
लाइव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवर आला तो चॅनेल, गेटवे, आत्ता
उत्तर देणारे मॉडेल, आणि त्याने वापरलेले प्रत्येक टूल. काम त्यांतून पुढे सरकत असताना
नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एका टेबलमध्ये.**
तो काय चालवतो, गेल्या 24 तासांत आणि त्याच्या संपूर्ण आयुष्यात त्याचा खर्च किती,
शेवटचा कधी दिसला, त्याचा मालक कोण, आणि सबस्क्रिप्शन बिल कव्हर करत आहे का. इथे 14
एजंट्स, 3 सेशन्स काम करत आहेत, 13 शांत आहेत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**एका टर्नचा वेळ आणि पैसा टूल-दर-टूल कुठे गेला हे हे दाखवते.**
एका खऱ्या सेशनचा एक टर्न: $1.16 मध्ये 11.2 मिनिटांत 11 टूल्स. प्रत्येक Bash
कॉल आणि मॉडेल कॉलला टाइमलाइनवर स्वतःची बार मिळते, त्यामुळे 4.1 मिनिटे चाललेली
कमांड आणि 226ms चाललेली कमांड एका दृष्टिक्षेपात वेगळी ओळखता येते.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**हे फक्त खर्चच नाही, कामाला गुण देते.**
या आठवड्यात A: 54 कामे स्वच्छ पूर्ण झाली, 2 खडबडीत कामांना $48.57 खर्च आला,
आणि मूल्यमापन करण्याइतकी पुरेशी क्रिया नसलेल्या रन्स विजय म्हणून मोजण्याऐवजी गुणांकनातून
वगळल्या आहेत. प्रत्येक खडबडीत रन तिच्या ट्रेसकडे लिंक होते.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो का भरत राहते हे हे दाखवते.**
शेवटच्या टर्नमध्ये 1M-टोकन विंडोपैकी 715K, 83.3% पीक, ओव्हरफ्लोऐवजी सक्रियपणे
(proactively) झालेले 4 कॉम्पॅक्शन्स, आणि त्यामागील प्रत्येक टर्नचे युटिलायझेशन.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता डिटेक्शन चालते.**
इन्स्टॉलपासूनच बिल्ट-इन डिटेक्टर्स चालू असतात: एजंट शांत झाला, टेलिमेट्री फीड
थांबली, कॉस्ट स्पाइक, टोकन बर्स्ट, एरर्स वाढत आहेत, एरर स्पाइक, बजेट
थ्रेशोल्ड, थ्रेट सिग्नेचर जुळला, सिक्युरिटी टूल फाइंडिंग, सिक्युरिटी पोश्चर
बदलले. तुमचे स्वतःचे नियम त्यावर ऐच्छिक (optional) आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीचा कॉल थांबवणे opt-in आहे, आणि बंद अवस्थेत शिप होते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुश, sudo, सिक्रेट्स, पॅकेज इन्स्टॉल्स आणि आउटबाउंड
कॉल्स यांना प्रत्येकाला तुम्ही चालू करू शकता असा नियम आहे. तुम्ही तो चालू करेपर्यंत,
ClawMetry फक्त पाहते आणि काहीही बदलत नाही. एकदा एक चालू केला, की जुळणारे कॉल्स
इथे (किंवा तुमच्या फोनवर) मान्यता किंवा नकारासाठी थांबतात.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रत्येक रनटाइमनुसार: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ओळख

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लायसन्स

MIT · [@vivekchand](https://github.com/vivekchand) द्वारे तयार · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
