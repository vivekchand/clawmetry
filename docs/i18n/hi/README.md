<!-- i18n-src:88be2deff5d5 -->
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

**अपने एजेंट को सोचते हुए देखें।** **30 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 26 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक ही डैशबोर्ड।

> 🌐 **इसे इनमें पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िगरेशन। सब कुछ अपने-आप पहचान लेता है।

```bash
pip install clawmetry && clawmetry
```

यह **http://localhost:8900** पर खुलता है। ज़ीरो कॉन्फ़िग: यह आपके पास पहले से मौजूद एजेंट रनटाइम को ढूँढ लेता है, उन्हें केवल-पढ़ने के लिए (read-only) पढ़ता है, और उनके चलने के तरीके में कुछ भी नहीं बदलता।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 एजेंट रनटाइम के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को वही डैशबोर्ड मिलता है। एक साथ कई चलाइए और हेडर स्विचर हर टैब को उनमें से किसी एक पर फिर से केंद्रित कर देता है।

क्या आपने किसी SDK पर अपना खुद का एजेंट बनाया है? इंटरसेप्टर उसकी LLM कॉल्स को भी ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न-दर-टर्न, रीप्ले के साथ
- **लागत और टोकन**: प्रति रनटाइम, मॉडल, सेशन और दिन के हिसाब से, विसंगति (anomaly) फ़्लैग के साथ
- **फ़्लो**: चैनलों, मॉडलों और टूल्स से गुज़रते संदेशों का लाइव डायग्राम
- **ब्रेन**: होते ही रीज़निंग और टूल-कॉल इवेंट स्ट्रीम
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोवाइडर के हिसाब से मापी गई विंडो यूटिलाइज़ेशन, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, साथ ही यह प्रति-रनटाइम नक़्शा कि हम *क्या नहीं* देख पाते ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जो हर रनटाइम ने वास्तव में लोड कीं
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर रेट, रेट लिमिट, लाइव लॉग स्ट्रीम
- **अलर्ट**: बजट कैप, एरर स्पाइक, एजेंट-ऑफ़लाइन, जो Slack, Discord, PagerDuty, Telegram, Email पर भेजे जाते हैं
- **अप्रूवल**: जोखिम भरी टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और निगरानी की लागत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले पूछने लायक दो सवाल।

**यह रनटाइम्स में कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे हैंडल करता है?**

यूटिलाइज़ेशन प्रतिशत उतना ही ईमानदार होता है जितना वह जिस अंक से भाग देता है। ClawMetry हर प्रोवाइडर के लिए विंडो का आकार [एक ऐसी टेबल](clawmetry/context_windows.py) से तय करता है जिसे आप पढ़ और PR कर सकते हैं, जो Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama और GLM को कवर करती है। यह सभी 30 रनटाइम को एक ही वेंडर की स्केल से नहीं नापता। यह मायने रखता है: Anthropic के 200K के मुक़ाबले नापा गया 300K GPT-5 टर्न ">100%, ब्लोन" पढ़ता है, जबकि असल में वह GPT-5 के 400K का 75% है। वही स्केल एक वाक़ई ओवरफ़्लो हुए 130K DeepSeek टर्न को आरामदायक 65% के रूप में छुपा देती है।

हर विंडो अपना उद्गम (provenance) साथ लेकर आती है: `model_table`, `explicit_marker`, `observed_floor`, या जब हमें मॉडल पता न हो तो ईमानदार `default`। अनुमान पर बना गेज कभी भी लुकअप पर बने गेज जितने अधिकार के साथ नहीं दिखता।

ClawMetry कुछ रनटाइम पर ही कॉम्पैक्शन इवेंट देख पाता है। इसलिए `GET /api/context-coverage` प्रति रनटाइम यह रिपोर्ट करता है कि **शून्य का मतलब "साफ़ चला" है या "हम अंधे हैं"**। जो `0` वाक़ई में अंधे होने का मतलब रखता है, वह यही कहता है। [पूरा विवरण](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रूमेंटेशन की लागत क्या है?**

| पथ | आपके एजेंट में जोड़ी गई | डिफ़ॉल्ट? |
|---|---|---|
| सेशन-फ़ाइल टेलिंग (सभी 30 रनटाइम) | **0**। अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रति LLM कॉल **+0.44 ms**, यानी 5s की कॉल का 0.009% | बंद |
| प्री-टूल हुक गेट (वार्म कैश) | 36 ms के इंटरप्रेटर फ़्लोर के ऊपर, प्रति गेटेड टूल कॉल **+44 ms** | बंद |
| एनफ़ोर्समेंट प्रॉक्सी | प्रति LLM कॉल **+9.7 ms** | बंद |

डेमन होस्ट लागत: **2,762 इवेंट/सेकंड** इनजेस्ट, डिस्क पर **710 बाइट्स/इवेंट** (100k इवेंट प्रति 67.7 MB), और व्यस्त इंस्टॉल पर लगातार **एक कोर का ~12%**। वह आख़िरी आँकड़ा हमारे अपने बताए गए 5-10% बजट से ज़्यादा है, इसलिए इसे पन्ने से हटाने के बजाय एक ऐसे बग के रूप में प्रकाशित किया गया है जिसका पीछा करना है।

Apple M2 Pro पर `benchmarks/overhead.py` से मापा गया। हार्नेस हर स्थिति को अलग प्रोसेस में चलाता है, उनका क्रम बदलता रहता है, और **जब राउंड्स उसके चिह्न (sign) पर असहमत हों तो आँकड़ा छापने से इनकार कर देता है**। इसे अपनी ही मशीन पर एक मिनट में चलाएँ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पथ मापा जाता है, जिसमें हुक गेट्स और एनफ़ोर्समेंट प्रॉक्सी भी शामिल हैं, और यह हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो नतीजे: Windows पर प्रॉक्सी की लागत Linux के मुक़ाबले लगभग सात गुना ज़्यादा है, और डेमन फ़िलहाल एक कोर का लगभग 12% इस्तेमाल करता है, जो हमारे अपने 5-10% बजट से ज़्यादा है। रॉ JSON, तरीक़ा, और अब भी क्या नहीं मापा गया है, यह सब [docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## मूल्य निर्धारण

| प्लान | यह क्या कवर करता है | क़ीमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताए गए बाक़ी सभी रनटाइम, फ़्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | Starter + नियंत्रण और मूल्यांकन: अप्रूवल, टूल-रिस्क पॉलिसी, इवैल्स, विसंगति पहचान, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट, टैम्पर-एविडेंट ऑडिट लॉग | $19 प्रति नोड / महीना |

वार्षिक प्लान, एंटरप्राइज़ और मौजूदा आँकड़े **[clawmetry.com/pricing](https://clawmetry.com/pricing)** पर मिलते हैं। सेल्फ़-होस्टेड लाइसेंस की (`clawmetry license`) क्लाउड के बिना भी काम करती है। मुफ़्त/पेड का सटीक बँटवारा [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग पढ़ता है। **जब तक आप `clawmetry connect` नहीं चलाते, तब तक कोई सेशन डेटा आपके सिस्टम से बाहर नहीं जाता** — न प्रॉम्प्ट, न जवाब, न टूल आर्ग्युमेंट, न फ़ाइल कंटेंट, न लॉग लाइनें। जब आप कनेक्ट करते हैं, तो स्नैपशॉट एक ऐसी कुंजी से एंड-टू-एंड एन्क्रिप्ट होता है जो कभी आपकी मशीन से बाहर नहीं जाती, और आपके ब्राउज़र में डिक्रिप्ट होती है। अगर किसी नोड के पास कुंजी नहीं है, तो अपलोड को बिना एन्क्रिप्शन भेजने के बजाय छोड़ दिया जाता है, और कोई सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

कनेक्ट करने से पहले डिफ़ॉल्ट रूप से दो चीज़ें चलती हैं, दोनों ऑप्ट-आउट करने योग्य हैं और दोनों में कोई सेशन डेटा नहीं होता: एक अनाम इंस्टॉल पिंग और PyPI के मुक़ाबले एक वर्ज़न चेक। एक डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए एक बार आपका पब्लिक IP भी देखता है। हर गंतव्य, वह क्या ले जाता है, और उसे कैसे बंद करें, इसकी पूरी सूची [docs/EGRESS.md](docs/EGRESS.md) में है; सेल्फ़-होस्टेड, रीपॉइंटेड और एयर-गैप्ड इंस्टॉल कोई भी वैकल्पिक आउटबाउंड कॉल बिल्कुल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में, हमारे द्वारा दिए गए कोड में होता है। यह पहले सिर्फ़ एक वादा था; अब यह ऐसी चीज़ है जिसे आप जाँच सकते हैं। आपकी कुंजी को छूने वाली हर लाइन एक पढ़ी जा सकने वाली फ़ाइल [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js) में रहती है, जो व्हील के अंदर शिप होती है और हूबहू परोसी जाती है, एक Subresource Integrity हैश के साथ पिन की गई। यह पुष्टि करने के लिए कि ब्राउज़र वही चला रहा है जो हमने प्रकाशित किया:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह क्या साबित नहीं करता: वह पेज हम ही परोसते हैं जो इस फ़ाइल को लोड करता है, तो हम एक अलग पेज परोस सकते थे। इंटीग्रिटी हैश आपको एक कॉम्प्रोमाइज़्ड CDN से बचाते हैं, वेंडर से नहीं। आपको जो मिलता है वह यह है कि कोई भी बदलाव जानबूझकर, पेज सोर्स में दिखने वाला, और PyPI पर मौजूद किसी भी आर्टिफ़ैक्ट से अलग होना ही होगा, जिसे कोई भी फ़ेच कर सकता है। सेल्फ़-होस्टिंग या केवल लोकल रहना इस निर्भरता को पूरी तरह हटा देता है।

## इंस्टॉल

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

या एजेंट को यह आपके लिए सेट अप करने दें। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot या OpenCode को सिखाती है कि ClawMetry कैसे इंस्टॉल करें, मशीन पर मौजूद एजेंट क्या कर रहे हैं और क्या ख़र्च कर रहे हैं इसकी रिपोर्ट कैसे दें, अनुरोध पर एक सेशन कैसे रोकें, और अप्रूवल के लिए जोखिम भरी टूल कॉल्स को कैसे रोक कर रखें:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तावेज़

| | |
|---|---|
| [रनटाइम कम्पैटिबिलिटी](docs/compatibility.md) | हर एडेप्टर क्या पढ़ता है, और रनटाइम कैसे जोड़ें |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोवाइडर विंडो, कॉम्पैक्शन बनाम ओवरफ़्लो, प्रति-रनटाइम कवरेज |
| [ओवरहेड](docs/OVERHEAD.md) | इंस्ट्रूमेंटेशन की लागत क्या है, मापी गई, साथ में पुनरुत्पादन का हार्नेस |
| [एनटाइटलमेंट्स](docs/ENTITLEMENTS.md) | Free बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [अप्रूवल और पॉलिसी](docs/APPROVALS.md) | प्री-एग्ज़िक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेस कहीं भी एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [अपना ख़ुद का एजेंट लाएँ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain, शुरू से अंत तक, चलाने-योग्य उदाहरणों के साथ |
| [SDK ट्रैकिंग](docs/SDK_TRACKING.md) | आपके ख़ुद बनाए एजेंट्स के लिए लागत आरोपण |
| [चैट चैनल](docs/CHANNELS.md) | Flow में दिखाए गए चैट एडेप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप |
| [Docker](docs/DOCKER.md) | इमेज, कम्पोज़, वॉल्यूम माउंट |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेवलपमेंट](docs/DEVELOPMENT.md) | यह अंदर कैसे काम करता है; सोर्स से चलाना |
| [टेलीमेट्री](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट

नीचे दिया गया हर आँकड़ा एक असली मशीन से है, केवल-पढ़ने के लिए (read-only), बिना कुछ बोया हुआ।

**यह आपको बताता है कि कब कुछ ग़लत है, सिर्फ़ यह नहीं कि क्या हुआ।**
सबसे ऊपर दो एनोमली बैनर: ख़र्च रोज़ाना औसत का 7x चल रहा है, और 4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 सेशन में से 324 में एक वेस्ट सिग्नल मिला, कारण के अनुसार सूचीबद्ध।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहाँ गया, हर विंडो में।**
आज $252.47, इस हफ़्ते $513.15, इस महीने $1,312.92, हर एक के पीछे के टोकन के साथ और यह भी कि आपकी सब्सक्रिप्शन इसमें से कितना पहले ही कवर करती है। उसके नीचे, लगभग $1,128/माह रिकवर करने योग्य के रूप में सूचीबद्ध और कैश रीयूज़ से पहले ही $17,256/माह बचाए गए।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि एक संदेश कैसे जवाब बनता है।**
लाइव फ़्लो डायग्राम: आप, वह चैनल जिस पर यह आया, गेटवे, अभी जवाब दे रहा मॉडल, और हर वह टूल जिसे उसने इस्तेमाल किया। जैसे-जैसे काम उनसे होकर गुज़रता है, नोड्स रोशन होते जाते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर हर एजेंट, एक ही टेबल में।**
वह क्या चलाता है, पिछले 24 घंटों में और अपने पूरे जीवनकाल में इसकी लागत क्या है, आख़िरी बार कब देखा गया, इसका मालिक कौन है, और क्या कोई सब्सक्रिप्शन बिल कवर कर रही है। यहाँ 14 एजेंट, 3 सेशन काम कर रहे, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि एक टर्न का समय और पैसा कहाँ गया, टूल-दर-टूल।**
एक असली सेशन का एक टर्न: 11.2 मिनट में 11 टूल, $1.16 में। हर Bash कॉल और मॉडल कॉल को टाइमलाइन पर अपना ख़ुद का बार मिलता है, ताकि 4.1 मिनट तक चलने वाली कमांड और 226ms तक चलने वाली कमांड एक नज़र में अलग पहचानी जा सकें।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को आँकता है, सिर्फ़ ख़र्च को नहीं।**
इस हफ़्ते एक A: 54 टास्क साफ़-सुथरे वापस आए, 2 कमज़ोर टास्क की लागत $48.57 रही, और जिन रन में आँकने लायक़ पर्याप्त गतिविधि नहीं थी उन्हें जीत मानने के बजाय ग्रेड से बाहर रखा गया। हर कमज़ोर रन अपने ट्रेस से लिंक होता है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो क्यों भरती रहती है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% पीक, 4 कॉम्पैक्शन जो सभी ओवरफ़्लो के बजाय पहले से ही (proactively) चले, और उसके पीछे हर टर्न का यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**डिटेक्शन बिना आपके कुछ भी कॉन्फ़िगर किए चलता है।**
बिल्ट-इन डिटेक्टर इंस्टॉल से ही चालू हैं: एजेंट शांत हो गया, टेलीमेट्री फ़ीड रुक गई, कॉस्ट स्पाइक, टोकन बर्स्ट, एरर बढ़ रहे हैं, एरर स्पाइक, बजट थ्रेशोल्ड, थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फ़ाइंडिंग, सिक्योरिटी पॉस्चर बदला। इसके ऊपर आपके ख़ुद के नियम वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को रोकना ऑप्ट-इन है, और शिप ऑफ़ है।**
रिकर्सिव डिलीट, फ़ोर्स पुश, sudo, सीक्रेट्स, पैकेज इंस्टॉल और आउटबाउंड कॉल्स में से हर एक के लिए एक नियम है जिसे आप चालू कर सकते हैं। जब तक आप ऐसा नहीं करते, ClawMetry बस देखता है और कुछ नहीं बदलता। एक बार चालू होने पर, मेल खाती कॉल्स यहाँ (या आपके फ़ोन पर) अप्रूव या डिनाई होने का इंतज़ार करती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रति रनटाइम: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## स्टार इतिहास

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लाइसेंस

MIT · [@vivekchand](https://github.com/vivekchand) द्वारा बनाया गया · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
