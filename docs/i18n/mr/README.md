<!-- i18n-src:12b97259721e -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एक एजंट प्रगती न करता शेकडो टूल कॉल्स करू शकतो.** ClawMetry
तुमचे कोडिंग एजंट्स आधीच लिहीत असलेल्या सेशन फाइल्स वाचते, आणि टाइमलाइन,
टूल कॉल्स आणि रनटाइम उघड करेल तेवढा टोकन व कॉस्ट डेटा एका
व्ह्यूमध्ये आणते — जेणेकरून तुम्हाला एक दीर्घ रन काम करत आहे की अडकली आहे हे सांगता येईल.

**31 AI एजंट रनटाइम्स** सोबत काम करते — Claude Code, OpenAI Codex, Hermes, OpenClaw आणि इतर 27. तुमच्या संपूर्ण एजंट फ्लीटसाठी एक डॅशबोर्ड. ([संपूर्ण यादी](SUPPORTED_RUNTIMES.txt), कॅटलॉगमधून जनरेट केलेली.)

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही स्वयंचलितपणे शोधते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीपासून असलेले एजंट रनटाइम्स ते शोधते, त्यांना फक्त-वाचनीय पद्धतीने वाचते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इन्स्टॉल करण्याआधी

| | |
|---|---|
| **हे काय करते** | तुमचे एजंट्स आधीच लिहीत असलेल्या सेशन फाइल्स आणि लॉग्ज वाचते. कोणतेही SDK नाही, कोड बदल नाही, तुमच्या अॅपमध्ये इन्स्ट्रुमेंटेशन नाही. |
| **तुम्हाला काय दिसते** | सेशन टाइमलाइन, टूल-बाय-टूल रिप्ले, टोकन आणि कॉस्ट ब्रेकडाउन, आणि ट्रॅजेक्टरी सिग्नल्स (लूपिंग, पुनरावृत्त अपयश) — प्रत्येक रनटाइमसाठी. |
| **काय मोफत आहे** | `pip install clawmetry` कोणत्याही अकाउंट, की किंवा नेटवर्क कॉलशिवाय **OpenClaw, NVIDIA NemoClaw आणि Goose** वाचते. इतर 27 — Claude Code, Codex, Cursor आणि उर्वरित — क्लोज्ड-सोर्स `clawmetry-pro` कंपॅनियनद्वारे वाचले जातात, जे 7-दिवसांच्या ट्रायल किंवा प्लॅनसह येते — नेमकी विभागणी पाहण्यासाठी [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) पहा. |
| **कसे सुरू करावे** | `pip install clawmetry && clawmetry`, नंतर localhost:8900 उघडा. या मशीनवर अजून एजंट्स नाहीत? `clawmetry --sample` तीन लेबल केलेल्या सिंथेटिक सेशन्सवर उघडते. |
| **तुमच्या मशीनमधून काय बाहेर जाते** | कोणताही सेशन डेटा जात नाही, जोपर्यंत तुम्ही `clawmetry connect` चालवत नाही. दोन गोष्टी डीफॉल्टने चालतात, दोन्ही ऑप्ट-आउट करण्यायोग्य आणि कोणतीही सेशन कंटेंट न वाहून नेणाऱ्या: एक अनामिक इन्स्टॉल पिंग आणि एक PyPI व्हर्जन तपासणी. प्रत्येक डेस्टिनेशन [docs/EGRESS.md](docs/EGRESS.md) मध्ये सूचीबद्ध आहे, टिप्पण्या वाचण्याऐवजी वायर कॅप्चरमधून पुन्हा तयार केलेले. |

आउटपुटचा न्याय करण्याआधी जाणून घेण्यासारख्या दोन मर्यादा: रनटाइम्स अगदी वेगळा
डेटा उघड करतात (काही मुळीच कॉस्ट प्रकाशित करत नाहीत — [मॅट्रिक्स](docs/compatibility.md)
प्रत्येक रनटाइमबद्दल सांगते), आणि एखादी क्रिया पाहणे म्हणजे ती
थांबवता येणे असे नाही ([कोणते नियंत्रण प्रत्यक्षात कार्य करतात, प्रत्येक रनटाइमसाठी](docs/APPROVALS.md)).


## 31 एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स अॅपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडर
स्विचर प्रत्येक टॅबची व्याप्ती त्यांतील एकावर पुन्हा सेट करतो.

SDK वर स्वतःचा एजंट बनवला आहे? इंटरसेप्टर त्याच्या LLM कॉल्सचाही मागोवा घेतो.
[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) पहा.

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टर्न-बाय-टर्न, रिप्लेसह
- **कॉस्ट आणि टोकन्स**: प्रत्येक रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, अनोमली फ्लॅग्जसह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून हलणाऱ्या मेसेजेसचे लाइव्ह डायग्राम
- **ब्रेन**: रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम जसा घडतो तसा
- **कॉन्टेक्स्ट ब्लोआउट**: प्रत्येक प्रोव्हायडरनुसार साइझ केलेली विंडो उपयोग, कॉम्पॅक्शन विरुद्ध सक्तीचा ओव्हरफ्लो, आणि आपल्याला *काय* दिसत नाही याचा प्रत्येक रनटाइमचा मॅप ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **हेल्थ आणि लॉग्ज**: डिस्क, मेमरी, एरर रेट्स, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे रूट केलेले
- **अप्रूव्हल्स**: जोखमीचे टूल कॉल्स *चालण्याआधी* थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाचा खर्च किती

कोणतेही एजंट-तुलना टूल विश्वास ठेवण्याआधी उत्तर देण्यासारखे दोन प्रश्न.

**रनटाइम्समध्ये कॉन्टेक्स्ट-विंडो ब्लोआउट कसे हाताळले जाते?**

एक उपयोगिता टक्केवारी ती ज्याने भागली जाते तितकीच प्रामाणिक असते. ClawMetry
[तुम्ही वाचू आणि PR करू शकता अशा टेबलमधून](clawmetry/context_windows.py) प्रत्येक प्रोव्हायडरनुसार
विंडो साइझ करते, ज्यात Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama आणि GLM समाविष्ट आहेत. ते सर्व 31
रनटाइम्स एका विक्रेत्याच्या पट्टीने मोजत नाही. ते महत्त्वाचे आहे: Anthropic च्या
200K वर मोजलेला 300K GPT-5 टर्न ">100%, ब्लोन" असे दाखवतो, जेव्हा तो प्रत्यक्षात
GPT-5 च्या 400K च्या 75% वर असतो. तीच पट्टी खरोखर ओव्हरफ्लो झालेल्या 130K DeepSeek
टर्नला आरामदायक 65% म्हणून लपवते.

प्रत्येक विंडो तिच्या स्रोतासह येते: `model_table`, `explicit_marker`,
`observed_floor`, किंवा मॉडेल माहीत नसल्यास प्रामाणिक `default`. अंदाजावर बांधलेला
गेज लूकअपवर बांधलेल्या गेजसारखा अधिकारवाणीने कधीही दिसत नाही.

ClawMetry काही रनटाइम्सवरच कॉम्पॅक्शन इव्हेंट्स पाहू शकते. त्यामुळे
`GET /api/context-coverage` प्रत्येक रनटाइमसाठी अहवाल देते की **शून्य म्हणजे
"स्वच्छ चालले" की "आम्हाला दिसत नाही"**. एक `0` ज्याचा प्रत्यक्षात अर्थ आंधळेपणा
आहे तो तसे सांगतो. [संपूर्ण तपशील](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनचा खर्च किती?**

| मार्ग | तुमच्या एजंटमध्ये जोडले | डीफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व 31 रनटाइम्स) | **0**. वेगळी प्रक्रिया, तुमच्या एजंटमध्ये ClawMetry कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलला **+0.44 ms**, म्हणजे 5s कॉलचा 0.009% | बंद |
| प्री-टूल हूक गेट (वॉर्म कॅशे) | प्रत्येक गेटेड टूल कॉलला **+44 ms**, 36 ms इंटरप्रेटर फ्लोअरवर | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलला **+9.7 ms** | बंद |

डिमन होस्ट खर्च: **2,762 इव्हेंट्स/सेकंड** इनजेस्ट, डिस्कवर **710 बाइट्स/इव्हेंट**
(प्रति 100k इव्हेंट्स 67.7 MB), आणि व्यस्त इन्स्टॉलवर सतत **एका कोरचा ~12%**.
तो शेवटचा आकडा आमच्याच नमूद केलेल्या 5-10% बजेटपेक्षा जास्त आहे, म्हणून तो
पानावरून काढण्याऐवजी पाठलाग करण्यासारखी बग म्हणून प्रकाशित केला आहे.

Apple M2 Pro वर `benchmarks/overhead.py` सह मोजलेले. हार्नेस प्रत्येक
कंडिशन वेगळ्या प्रक्रियेत चालवतो, त्यांचा क्रम बदलतो, आणि **राऊंड्सचे चिन्ह
जुळत नसल्यास आकडा छापण्यास नकार देतो**. एका मिनिटात ते तुमच्या स्वतःच्या
मशीनवर चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हूक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस
CI मध्ये Linux, macOS आणि Windows वर चालतो. जाणून घेण्यासारखे दोन निकाल:
Windows वर प्रॉक्सीचा खर्च Linux पेक्षा सुमारे सातपट जास्त आहे, आणि डिमन
सध्या एका कोरचा सुमारे 12% सतत वापरतो, जे आमच्याच 5-10% बजेटपेक्षा जास्त आहे.
कच्चा JSON, पद्धत, आणि अजून काय मोजलेले नाही ते [docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| प्लॅन | यामध्ये काय समाविष्ट आहे | किंमत |
|---|---|---|
| **मोफत** | OpenClaw + NVIDIA NemoClaw + Goose, संपूर्ण डॅशबोर्ड, फक्त लोकल | $0 |
| **स्टार्टर** | वरील इतर सर्व रनटाइम्स, फ्लीट व्ह्यू, क्लाउड सिंक | प्रति नोड / महिना $9 |
| **Pro** | स्टार्टर + नियंत्रण आणि मूल्यमापन: अप्रूव्हल्स, टूल-रिस्क पॉलिसीज, इव्हल्स, अनोमली डिटेक्शन, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, टॅम्पर-एव्हिडेंट ऑडिट लॉग | प्रति नोड / महिना $19 |

वार्षिक प्लॅन्स, एंटरप्राइझ आणि सध्याचे आकडे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** येथे आहेत. सेल्फ-होस्टेड लायसन्स
की क्लाउडशिवाय काम करतात (`clawmetry license`). नेमकी मोफत/पेड विभागणी
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्याच मशीनवर राहतो

ClawMetry लोकल सेशन फाइल्स आणि लॉग्ज वाचते. **तुम्ही `clawmetry connect` चालवत
नाही तोपर्यंत कोणताही सेशन डेटा तुमच्या मशीनबाहेर जात नाही** — प्रॉम्प्ट्स, उत्तरे,
टूल आर्ग्युमेंट्स, फाइल कंटेंट किंवा लॉग लाइन्स नाही. तुम्ही कनेक्ट केल्यावर, स्नॅपशॉट
अशा कीने एंड-टू-एंड एन्क्रिप्टेड असतो जी तुमच्या मशीनबाहेर कधीही जात नाही, आणि तुमच्या
ब्राउझरमध्ये डिक्रिप्ट केली जाते. एखाद्या नोडकडे की नसेल, तर अपलोड साध्या स्वरूपात
पाठवण्याऐवजी वगळला जातो, आणि कोणताही सर्व्हर रिस्पॉन्स ते बंद करू शकत नाही.

तुम्ही कनेक्ट करण्याआधी दोन गोष्टी डीफॉल्टने चालतात, दोन्ही ऑप्ट-आउट करण्यायोग्य आणि
कोणताही सेशन डेटा न वाहून नेणाऱ्या: एक अनामिक इन्स्टॉल पिंग आणि PyPI विरुद्ध व्हर्जन
तपासणी. डीफॉल्ट इन्स्टॉल एक स्टार्टअप बॅनर लाइनसाठी तुमचा पब्लिक IP देखील एकदा पाहते.
प्रत्येक डेस्टिनेशन, ते काय वाहून नेते आणि ते कसे बंद करावे हे [docs/EGRESS.md](docs/EGRESS.md)
मध्ये सूचीबद्ध आहे; सेल्फ-होस्टेड, रीपॉइंटेड आणि एअर-गॅप्ड इन्स्टॉल्स मुळीच स्वेच्छेने
बाह्य कॉल्स करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये, आम्ही तुम्हाला दिलेल्या कोडमध्ये होते. ते आधी एक
वचन होते; आता ते तुम्ही तपासू शकता अशी गोष्ट आहे. तुमच्या कीला स्पर्श करणारी प्रत्येक
लाइन एका वाचनीय फाइलमध्ये आहे, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
जी व्हील (wheel) च्या आत येते आणि जशी आहे तशी सर्व्ह केली जाते, Subresource
Integrity हॅशने पिन केलेली. ब्राउझर आम्ही प्रकाशित केलेली गोष्टच चालवतो याची पुष्टी करण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: आम्ही ती फाइल लोड करणारे पान सर्व्ह करतो, त्यामुळे आम्ही वेगळे
पान सर्व्ह करू शकतो. इंटिग्रिटी हॅशेस तुम्हाला तडजोड झालेल्या CDN पासून संरक्षण देतात,
विक्रेत्यापासून नाही. तुम्हाला जे मिळते ते हे की कोणताही बदल जाणीवपूर्वक, पान सोर्समध्ये
दृश्यमान, आणि कोणीही मिळवू शकेल अशा PyPI वरील आर्टिफॅक्टपेक्षा वेगळा असणे आवश्यक आहे.
सेल्फ-होस्टिंग किंवा फक्त-लोकल राहणे ही निर्भरता संपूर्णपणे काढून टाकते.

## इन्स्टॉल करा

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आवश्यक आहे, आणि त्याच मशीनवर किमान एक
एजंट रनटाइम. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

किंवा एजंटला तुमच्यासाठी सेटअप करू द्या. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot किंवा OpenCode ला ClawMetry
इन्स्टॉल करण्यास, मशीनवरील एजंट्स काय करत आहेत आणि किती खर्च करत आहेत याचा अहवाल
देण्यास, विनंतीनुसार एक सेशन थांबवण्यास, आणि मंजुरीसाठी जोखमीचे टूल कॉल्स थांबवून
ठेवण्यास शिकवते:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## डॉक्स

| | |
|---|---|
| [रनटाइम कम्पॅटिबिलिटी](docs/compatibility.md) | प्रत्येक अडॅप्टर काय वाचतो, आणि रनटाइम कसा जोडावा |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रत्येक प्रोव्हायडरनुसार विंडोज, कॉम्पॅक्शन विरुद्ध ओव्हरफ्लो, प्रत्येक रनटाइमची कव्हरेज |
| [ओव्हरहेड](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनचा खर्च किती, मोजलेला, तो पुन्हा तयार करण्यासाठी हार्नेससह |
| [एन्टायटलमेंट्स](docs/ENTITLEMENTS.md) | मोफत विरुद्ध पेड, टियर मॅट्रिक्स, लायसन्स CLI |
| [अप्रूव्हल्स आणि पॉलिसीज](docs/APPROVALS.md) | प्री-एक्झिक्युशन गेटिंग, रिस्क स्कोअरिंग, फोन अप्रूव्हल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कुठेही ट्रेसेस एक्सपोर्ट करा, कोणाकडूनही OTLP इनजेस्ट करा |
| [स्वतःचा एजंट आणा](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सुरुवातीपासून शेवटपर्यंत, चालवण्यायोग्य उदाहरणांसह |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः बनवलेल्या एजंट्ससाठी कॉस्ट अट्रिब्यूशन |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | फ्लोमध्ये दिसणारे चॅट अडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोझ, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | आतून कसे काम करते; सोर्समधून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | अनामिक इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्ज, आणि ते कसे बंद करावे |

## स्क्रीनशॉट्स

खालील प्रत्येक आकडा एका खऱ्या मशीनवरून आहे, फक्त-वाचनीय, काहीही सीड न करता.

**काहीतरी चुकीचे असल्यास ते तुम्हाला सांगते, फक्त काय घडले हे नाही.**
शीर्षस्थानी दोन अनोमली बॅनर्स: खर्च दैनिक सरासरीच्या 7x वेगाने चालणे, आणि
4.2x कॉस्ट स्पाइक. त्यांच्याखाली, 667 पैकी 324 अलीकडील सेशन्समध्ये कारणानुसार
सूचीबद्ध वेस्ट सिग्नल आहे.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले हे प्रत्येक विंडोमध्ये दाखवते.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, प्रत्येकामागील
टोकन्ससह आणि तुमचे सबस्क्रिप्शन त्यातील किती आधीच कव्हर करते. त्याखाली, सुमारे
$1,128/महिना पुनर्प्राप्त करण्यायोग्य म्हणून आणि कॅशे रीयूजने आधीच वाचवलेले
$17,256/महिना, आयटमवाइज.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**एक मेसेज उत्तर कसे बनतो हे ते दाखवते.**
लाइव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवर आला तो चॅनेल, गेटवे, आत्ता उत्तर देणारे
मॉडेल, आणि त्याने वापरलेले प्रत्येक टूल. काम त्यांतून जात असताना नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एका टेबलमध्ये.**
तो काय चालवतो, गेल्या 24 तासांत आणि आयुष्यभरात त्याचा खर्च किती, तो शेवटचा कधी
दिसला, तो कोणाचा आहे, आणि सबस्क्रिप्शन बिल कव्हर करते का. येथे 14 एजंट्स,
3 सेशन्स काम करत आहेत, 13 शांत आहेत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**टर्नचा वेळ आणि पैसे कुठे गेले हे टूल-बाय-टूल दाखवते.**
खऱ्या सेशनचा एक टर्न: 11.2 मिनिटांत 11 टूल्स, $1.16 साठी. प्रत्येक Bash
कॉल आणि मॉडेल कॉलला टाइमलाइनवर स्वतःचा बार मिळतो, त्यामुळे 4.1 मिनिटे चाललेला
कमांड आणि 226ms चालणारा कमांड एका नजरेत ओळखता येतो.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**काम मोजते, फक्त खर्च नाही.**
या आठवड्यात A: 54 कामे स्वच्छपणे परत आली, 2 खडतर कामांचा खर्च $48.57 झाला, आणि
न्याय करण्यासाठी खूप कमी अॅक्टिव्हिटी असलेले रन्स विजय म्हणून मोजण्याऐवजी ग्रेडमधून
वगळले जातात. प्रत्येक खडतर रन त्याच्या ट्रेसशी लिंक करतो.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो का भरत राहते हे ते दाखवते.**
नवीनतम टर्नवर 1M-टोकन विंडोपैकी 715K, 83.3% शिखर, ओव्हरफ्लोवर न होता सक्रियपणे
फायर झालेली 4 कॉम्पॅक्शन्स, आणि त्यामागील प्रत्येक टर्नची उपयोगिता.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता डिटेक्शन चालते.**
इनबिल्ट डिटेक्टर्स इन्स्टॉलपासूनच चालू आहेत: एजंट शांत झाला, टेलिमेट्री फीड बंद
झाली, कॉस्ट स्पाइक, टोकन बर्स्ट, एरर्स वाढत आहेत, एरर स्पाइक, बजेट थ्रेशोल्ड,
थ्रेट सिग्नेचर जुळली, सिक्युरिटी टूल फाइंडिंग, सिक्युरिटी पोश्चर बदलली. तुमचे
स्वतःचे नियम त्यावर पर्यायी आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीचा कॉल थांबवणे ऑप्ट-इन आहे, आणि बंद असून येते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुश, sudo, सिक्रेट्स, पॅकेज इन्स्टॉल्स आणि आउटबाउंड कॉल्स
यांतील प्रत्येकाला तुम्ही चालू करू शकाल असा नियम मिळतो. तुम्ही तो चालू करेपर्यंत,
ClawMetry फक्त पाहते आणि काहीही बदलत नाही. एकदा चालू केल्यावर, जुळणारे कॉल्स
येथे (किंवा तुमच्या फोनवर) मंजुरी किंवा नकारासाठी थांबतात.

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

MIT · [@vivekchand](https://github.com/vivekchand) यांनी तयार केले · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
