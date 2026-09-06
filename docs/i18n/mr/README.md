<!-- i18n-src:88be2deff5d5 -->
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

**तुमचा एजंट कसा विचार करतो ते पहा.** **30 AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी 26. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीपासून असलेले एजंट रनटाइम्स ते शोधते, त्यांना फक्त-वाचनीय पद्धतीने वाचते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स अ‍ॅपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाचवेळी अनेक चालवा आणि हेडर स्विचर प्रत्येक टॅबचा स्कोप पुन्हा त्यांच्यापैकी एकावर सेट करतो.

एखाद्या SDK वर स्वतःचा एजंट बनवला आहे? इंटरसेप्टर त्याच्या LLM कॉल्सचाही मागोवा घेतो. पहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टर्न-दर-टर्न, रिप्लेसह
- **खर्च आणि टोकन्स**: प्रत्येक रनटाइम, मॉडेल, सेशन आणि दिवसासाठी, अ‍ॅनोमली फ्लॅग्जसह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या मेसेजेसचे लाईव्ह डायग्राम
- **ब्रेन**: घडत असतानाच रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम
- **कॉन्टेक्स्ट ब्लोआउट**: प्रत्येक प्रोव्हायडरनुसार आकारलेली विंडो युटिलायझेशन, कॉम्पॅक्शन विरुद्ध सक्तीचा ओव्हरफ्लो, तसेच आपण काय *पाहू शकत नाही* याचा प्रत्येक रनटाइमनुसार नकाशा ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **आरोग्य आणि लॉग्स**: डिस्क, मेमरी, एरर रेट्स, रेट लिमिट्स, लाईव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email वर पाठवले जाणारे
- **अ‍ॅप्रूव्हल्स**: जोखमीचे टूल कॉल्स *चालण्यापूर्वी* थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाचा खर्च किती

कोणतेही एजंट-तुलना टूल विश्वासात घेण्यापूर्वी उत्तर देण्यायोग्य असे दोन प्रश्न.

**ते वेगवेगळ्या रनटाइम्समध्ये कॉन्टेक्स्ट-विंडो ब्लोआउट कसे हाताळते?**

युटिलायझेशन टक्केवारी ही ती ज्याने भागली जाते तितकीच प्रामाणिक असते. ClawMetry प्रत्येक प्रोव्हायडरनुसार विंडोचा आकार [तुम्ही वाचू आणि PR करू शकता अशा टेबलमधून](clawmetry/context_windows.py) ठरवते, ज्यात Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama आणि GLM समाविष्ट आहेत. ते सर्व 30 रनटाइम्स एकाच वेंडरच्या मापदंडाने मोजत नाही. हे महत्त्वाचे आहे: Anthropic च्या 200K विरुद्ध मोजलेला 300K GPT-5 टर्न ">100%, blown" असे दाखवतो जेव्हा तो प्रत्यक्षात GPT-5 च्या 400K पैकी 75% वर असतो. तोच मापदंड प्रत्यक्षात ओव्हरफ्लो झालेल्या 130K DeepSeek टर्नला आरामदायक 65% म्हणून लपवतो.

प्रत्येक विंडो तिच्या उगमासह येते: `model_table`, `explicit_marker`, `observed_floor`, किंवा मॉडेल माहीत नसताना प्रामाणिक `default`. अंदाजावर आधारित गेज कधीच लूकअपवर आधारित गेजइतक्या अधिकाराने दिसत नाही.

ClawMetry ला काही रनटाइम्सवर फक्त कॉम्पॅक्शन इव्हेंट्स दिसू शकतात. म्हणून `GET /api/context-coverage` प्रत्येक रनटाइमसाठी अहवाल देते की **शून्य म्हणजे "स्वच्छ चालले" की "आम्हाला दिसत नाही"**. जो `0` खरोखर आंधळेपणा दर्शवतो, तो तसे स्पष्ट सांगतो.
[संपूर्ण तपशील](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनचा खर्च किती?**

| मार्ग | तुमच्या एजंटमध्ये जोडले जाणारे | डिफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व 30 रनटाइम्स) | **0**. वेगळी प्रोसेस, तुमच्या एजंटमध्ये कोणताही ClawMetry कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलसाठी **+0.44 ms**, म्हणजे 5s कॉलच्या 0.009% | बंद |
| प्री-टूल हुक गेट (वॉर्म कॅशे) | प्रत्येक गेटेड टूल कॉलसाठी **+44 ms**, 36 ms इंटरप्रिटर फ्लोरच्या वर | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलसाठी **+9.7 ms** | बंद |

डिमन होस्ट खर्च: **2,762 इव्हेंट्स/सेकंद** इनजेस्ट, डिस्कवर **710 बाइट्स/इव्हेंट** (1 लाख इव्हेंट्सला 67.7 MB), आणि एका व्यस्त इन्स्टॉलवर सतत **एका कोरचा ~12%**. ती शेवटची संख्या आमच्या स्वतःच्या 5-10% बजेटपेक्षा जास्त आहे, म्हणून ती पानावरून काढून टाकण्याऐवजी पाठलाग करण्यायोग्य बग म्हणून प्रकाशित केली आहे.

Apple M2 Pro वर `benchmarks/overhead.py` वापरून मोजलेले. हार्नेस प्रत्येक कंडिशन वेगळ्या प्रोसेसमध्ये चालवते, त्यांचा क्रम बदलत राहते, आणि **राऊंड्समध्ये चिन्हाबाबत मतभेद असेल तर संख्या छापण्यास नकार देते**. एका मिनिटात तुमच्या स्वतःच्या मशीनवर चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हुक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस CI मध्ये Linux, macOS आणि Windows वर चालतो. जाणून घेण्यासारखे दोन निकाल: प्रॉक्सीचा खर्च Linux पेक्षा Windows वर सुमारे सातपट जास्त आहे, आणि डिमन सध्या एका कोरच्या सुमारे 12% इतका सतत वापर करतो, जो आमच्या स्वतःच्या 5-10% बजेटपेक्षा जास्त आहे. कच्चा JSON, पद्धत, आणि अजून काय मोजलेले नाही, ते [docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| प्लॅन | काय समाविष्ट आहे | किंमत |
|---|---|---|
| **मोफत** | OpenClaw + NVIDIA NemoClaw + Goose, पूर्ण डॅशबोर्ड, फक्त लोकल | $0 |
| **स्टार्टर** | वरील इतर प्रत्येक रनटाइम, फ्लीट व्ह्यू, क्लाउड सिंक | $9 प्रति नोड / महिना |
| **Pro** | स्टार्टर + नियंत्रण आणि मूल्यमापन: अ‍ॅप्रूव्हल्स, टूल-रिस्क पॉलिसीज, इव्हॅल्स, अ‍ॅनोमली डिटेक्शन, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, टँपर-एव्हिडंट ऑडिट लॉग | $19 प्रति नोड / महिना |

वार्षिक प्लॅन्स, एंटरप्राइझ आणि सद्य आकडे **[clawmetry.com/pricing](https://clawmetry.com/pricing)** वर आहेत. सेल्फ-होस्टेड लायसन्स की क्लाउडशिवायही काम करतात (`clawmetry license`). नेमकी मोफत/पेड विभागणी [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्याच मशीनवर राहतो

ClawMetry लोकल सेशन फाइल्स आणि लॉग्स वाचते. **तुम्ही `clawmetry connect` चालवत नाही तोपर्यंत कोणताही सेशन डेटा तुमच्या मशीनबाहेर जात नाही** — कोणतेही प्रॉम्प्ट्स, रिप्लाय्ज, टूल आर्ग्युमेंट्स, फाइल कंटेंट किंवा लॉग लाइन्स नाहीत. जेव्हा तुम्ही कनेक्ट करता, तेव्हा स्नॅपशॉट एंड-टू-एंड एन्क्रिप्टेड असतो अशा कीने जी तुमच्या मशीनबाहेर कधीच जात नाही, आणि ती तुमच्या ब्राउझरमध्ये डिक्रिप्ट केली जाते. जर एखाद्या नोडकडे की नसेल, तर अपलोड साध्या स्वरूपात पाठवण्याऐवजी वगळला जातो, आणि कोणताही सर्व्हर रिस्पॉन्स हे बंद करू शकत नाही.

तुम्ही कनेक्ट करण्यापूर्वी दोन गोष्टी डिफॉल्टने चालतात, दोन्ही ऑप्ट-आउट करण्यायोग्य आणि दोन्हीमध्ये कोणताही सेशन डेटा नसतो: एक अनामिक इन्स्टॉल पिंग आणि PyPI विरुद्ध व्हर्जन चेक. डिफॉल्ट इन्स्टॉल स्टार्टअप बॅनर लाइनसाठी एकदा तुमचा पब्लिक IP देखील शोधतो. प्रत्येक डेस्टिनेशन, ते काय वाहून नेते आणि ते कसे बंद करायचे, हे [docs/EGRESS.md](docs/EGRESS.md) मध्ये सूचीबद्ध आहे; सेल्फ-होस्टेड, रीपॉइंटेड आणि एअर-गॅप्ड इन्स्टॉल्स कोणतेही ऐच्छिक आउटबाउंड कॉल्स करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये, आम्ही तुम्हाला देत असलेल्या कोडमध्ये होते. पूर्वी हे एक वचन होते; आता ती अशी गोष्ट आहे जी तुम्ही तपासू शकता. तुमच्या कीला स्पर्श करणारी प्रत्येक ओळ एकाच वाचनीय फाइलमध्ये आहे, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), जी व्हीलमध्ये पाठवली जाते आणि जशीच्या तशी सर्व्ह केली जाते, Subresource Integrity हॅशने पिन केलेली. ब्राउझर आम्ही प्रकाशित केलेलेच चालवतो याची खात्री करण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: फाइल लोड करणारे पान आम्हीच सर्व्ह करतो, त्यामुळे आम्ही वेगळे पानही सर्व्ह करू शकतो. इंटिग्रिटी हॅशेस तुमचे कॉम्प्रोमाइज्ड CDN पासून संरक्षण करतात, वेंडरपासून नाही. तुम्हाला जे मिळते ते म्हणजे कोणताही बदल मुद्दाम, पेज सोर्समध्ये दिसणारा, आणि कोणीही मिळवू शकेल अशा PyPI वरील आर्टिफॅक्टपेक्षा वेगळा असणे आवश्यक आहे. सेल्फ-होस्टिंग किंवा फक्त-लोकल राहणे ही निर्भरता पूर्णपणे काढून टाकते.

## इन्स्टॉल

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा एक-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आणि त्याच मशीनवर किमान एक एजंट रनटाइम आवश्यक आहे. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

किंवा एजंटला तुमच्यासाठी सेटअप करू द्या. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot किंवा OpenCode ला शिकवते की ClawMetry कसे इन्स्टॉल करायचे, मशीनवरील एजंट्स काय करत आहेत आणि किती खर्च करत आहेत याचा अहवाल कसा द्यायचा, विनंतीनुसार एखादे सेशन कसे थांबवायचे, आणि मंजुरीसाठी जोखमीचे टूल कॉल्स कसे थांबवायचे:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तऐवज

| | |
|---|---|
| [रनटाइम सुसंगतता](docs/compatibility.md) | प्रत्येक अ‍ॅडॅप्टर काय वाचतो, आणि रनटाइम कसे जोडायचे |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रत्येक प्रोव्हायडरनुसार विंडो, कॉम्पॅक्शन विरुद्ध ओव्हरफ्लो, प्रत्येक रनटाइमनुसार कव्हरेज |
| [ओव्हरहेड](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनचा खर्च किती, मोजलेला, तो पुन्हा तयार करण्याच्या हार्नेससह |
| [एन्टायटलमेंट्स](docs/ENTITLEMENTS.md) | मोफत विरुद्ध पेड, टियर मॅट्रिक्स, लायसन्स CLI |
| [अ‍ॅप्रूव्हल्स आणि पॉलिसीज](docs/APPROVALS.md) | प्री-एक्झिक्युशन गेटिंग, रिस्क स्कोअरिंग, फोन अ‍ॅप्रूव्हल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेसेस कुठेही एक्सपोर्ट करा, कशाहीमधून OTLP इनजेस्ट करा |
| [तुमचा स्वतःचा एजंट आणा](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सुरुवातीपासून शेवटपर्यंत, चालण्यायोग्य उदाहरणांसह |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः बनवलेल्या एजंट्ससाठी कॉस्ट अ‍ॅट्रिब्युशन |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | Flow मध्ये दाखवलेले चॅट अ‍ॅडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | ते आतून कसे काम करते; सोर्समधून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | अनामिक इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्ज, आणि ते कसे बंद करायचे |

## स्क्रीनशॉट्स

खालील प्रत्येक आकडा एका खऱ्या मशीनवरून आहे, फक्त-वाचनीय, काहीही आधीपासून तयार न करता.

**काहीतरी चुकीचे झाले की ते तुम्हाला सांगते, फक्त काय घडले तेच नाही.**
वरती दोन अ‍ॅनोमली बॅनर्स: दैनंदिन सरासरीच्या 7 पट खर्च चालू, आणि 4.2 पट कॉस्ट स्पाइक. त्याखाली, अलीकडील 667 पैकी 324 सेशन्समध्ये वेस्ट सिग्नल आढळला, कारणानुसार वर्गीकृत.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले हे प्रत्येक विंडोमध्ये दाखवते.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, त्यामागील टोकन्ससह आणि तुमचे सबस्क्रिप्शन त्यातील किती भाग आधीच कव्हर करते. त्याखाली, सुमारे $1,128/महिना रिकव्हरेबल म्हणून वर्गीकृत आणि कॅशे रीयूजमुळे आधीच वाचलेले $17,256/महिना.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**मेसेज उत्तर कसा बनतो हे ते रेखाटते.**
लाईव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवरून आला, गेटवे, सध्या उत्तर देणारे मॉडेल, आणि त्याने वापरलेले प्रत्येक टूल. काम त्यांच्यामधून जाताना नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एकाच टेबलमध्ये.**
तो काय चालवतो, गेल्या 24 तासांत आणि आयुष्यभरात त्याचा खर्च किती, तो शेवटचा कधी दिसला, तो कोणाचा आहे, आणि सबस्क्रिप्शन बिल कव्हर करत आहे का. इथे 14 एजंट्स, 3 सेशन्स काम करत आहेत, 13 शांत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**टूल-टूल पातळीवर एका टर्नचा वेळ आणि पैसा कुठे गेला हे ते दाखवते.**
एका खऱ्या सेशनचा एक टर्न: 11.2 मिनिटांत 11 टूल्स, $1.16 साठी. प्रत्येक Bash कॉल आणि मॉडेल कॉलला टाइमलाइनवर स्वतःची बार मिळते, त्यामुळे 4.1 मिनिटे चाललेली कमांड आणि 226ms चाललेली कमांड एका दृष्टीक्षेपात वेगळी ओळखता येते.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ते काम मोजते, फक्त खर्च नाही.**
या आठवड्यात A ग्रेड: 54 कामे व्यवस्थित पूर्ण झाली, 2 खडतर कामांचा खर्च $48.57 झाला, आणि जज करण्याइतकी पुरेशी अ‍ॅक्टिव्हिटी नसलेले रन्स विजय म्हणून मोजण्याऐवजी ग्रेडमधून वगळले जातात. प्रत्येक खडतर रन त्याच्या ट्रेसकडे लिंक करते.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो का भरत राहते हे ते दाखवते.**
शेवटच्या टर्नमध्ये 1M-टोकन विंडोपैकी 715K, 83.3% पीक, 4 कॉम्पॅक्शन्स जे सर्व ओव्हरफ्लोऐवजी proactively झाले, आणि त्यामागील प्रत्येक टर्नचे युटिलायझेशन.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता डिटेक्शन चालते.**
इन्स्टॉलपासूनच बिल्ट-इन डिटेक्टर्स चालू आहेत: एजंट शांत झाला, टेलिमेट्री फीड थांबली, कॉस्ट स्पाइक, टोकन बर्स्ट, एरर वाढत आहेत, एरर स्पाइक, बजेट थ्रेशोल्ड, थ्रेट सिग्नेचर जुळली, सिक्युरिटी टूल फाइंडिंग, सिक्युरिटी पोश्चर बदलला. तुमचे स्वतःचे नियम त्यावर पर्यायी आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीच्या कॉलला थांबवणे ऑप्ट-इन आहे, आणि बंद अवस्थेत रिलीज होते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुशेस, sudo, सिक्रेट्स, पॅकेज इन्स्टॉल्स आणि आउटबाउंड कॉल्स यापैकी प्रत्येकासाठी तुम्ही चालू करू शकता असा नियम आहे. तुम्ही तो चालू करेपर्यंत, ClawMetry फक्त पाहते आणि काहीही बदलत नाही. एकदा चालू केल्यावर, जुळणारे कॉल्स इथे (किंवा तुमच्या फोनवर) मंजुरी किंवा नकारासाठी थांबतात.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रत्येक रनटाइमनुसार: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## स्टार हिस्टरी

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## परवाना

MIT · [@vivekchand](https://github.com/vivekchand) द्वारे तयार केले · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
