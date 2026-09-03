<!-- i18n-src:9767c8001c9c -->
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

**अपने एजेंट को सोचते हुए देखें।** **30 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 26 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक डैशबोर्ड।

> 🌐 **इसे पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ ऑटो-डिटेक्ट होता है।

```bash
pip install clawmetry && clawmetry
```

यह **http://localhost:8900** पर खुलता है। शून्य कॉन्फ़िग: यह उन एजेंट रनटाइम को ढूँढ लेता है जो आपके पास पहले से हैं, उन्हें केवल-पढ़ने (read-only) के तौर पर पढ़ता है, और उनके चलने के तरीके में कुछ भी नहीं बदलता।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 एजेंट रनटाइम के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को वही डैशबोर्ड मिलता है। एक साथ कई चलाएँ और हेडर स्विचर हर टैब को उनमें से किसी एक पर फिर से स्कोप कर देता है।

क्या आपने SDK पर अपना खुद का एजेंट बनाया है? इंटरसेप्टर उसकी LLM कॉल्स को भी ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न दर टर्न, रीप्ले के साथ
- **लागत और टोकन**: रनटाइम, मॉडल, सेशन और दिन के हिसाब से, एनोमली फ़्लैग के साथ
- **फ़्लो**: चैनलों, मॉडलों और टूल्स के बीच चल रहे मैसेजों का लाइव डायग्राम
- **ब्रेन**: रीज़निंग और टूल-कॉल इवेंट स्ट्रीम, जैसे-जैसे यह होता है
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोवाइडर के हिसाब से विंडो का आकार, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, साथ ही यह नक्शा कि हम हर रनटाइम में *क्या नहीं* देख पाते ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जिन्हें हर रनटाइम ने वास्तव में लोड किया
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर दर, रेट लिमिट, लाइव लॉग स्ट्रीम
- **अलर्ट्स**: बजट कैप, एरर स्पाइक, एजेंट-ऑफ़लाइन, जिन्हें Slack, Discord, PagerDuty, Telegram, Email पर भेजा जा सकता है
- **अप्रूवल्स**: जोखिम भरे टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और मॉनिटरिंग की लागत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले जवाब देने लायक दो सवाल।

**यह रनटाइम्स में कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे संभालता है?**

यूटिलाइज़ेशन प्रतिशत उतना ही ईमानदार होता है जितना वह अंक जिससे उसे विभाजित किया जाता है। ClawMetry हर प्रोवाइडर के लिए विंडो का आकार [एक ऐसी टेबल](clawmetry/context_windows.py) से लेता है जिसे आप पढ़ और PR कर सकते हैं, जो Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama और GLM को कवर करती है। यह सभी 26 रनटाइम को एक ही वेंडर के पैमाने से नहीं मापता। यह मायने रखता है: Anthropic के 200K के मुक़ाबले मापा गया 300K GPT-5 टर्न ">100%, blown" दिखता है जबकि असल में यह GPT-5 के 400K का 75% है। वही पैमाना एक सचमुच ओवरफ़्लो हुए 130K DeepSeek टर्न को आरामदायक 65% के रूप में छुपा देता है।

हर विंडो अपनी उत्पत्ति के साथ आती है: `model_table`, `explicit_marker`, `observed_floor`, या जब हमें मॉडल का पता नहीं होता तो एक ईमानदार `default`। अनुमान पर बना गेज कभी भी लुकअप पर बने गेज जितनी विश्वसनीयता के साथ नहीं दिखता।

ClawMetry कुछ रनटाइम्स पर ही कॉम्पैक्शन इवेंट देख पाता है। इसलिए `GET /api/context-coverage` हर रनटाइम के लिए रिपोर्ट करता है कि क्या **एक शून्य का मतलब "साफ़ चला" है या "हम अंधे हैं"**। जो `0` वास्तव में अंधे होने का मतलब रखता है, वह इसे साफ़-साफ़ बताता है।
[पूरा विवरण](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रुमेंटेशन की लागत क्या है?**

| पथ | आपके एजेंट में जोड़ा गया | डिफ़ॉल्ट? |
|---|---|---|
| सेशन-फ़ाइल टेलिंग (सभी 30 रनटाइम) | **0**। अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | ऑन |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रति LLM कॉल **+0.44 ms**, यानी 5s की कॉल का 0.009% | ऑफ़ |
| प्री-टूल हुक गेट (वार्म कैश) | 36 ms के इंटरप्रेटर फ़्लोर के ऊपर, गेटेड टूल कॉल पर **+44 ms** | ऑफ़ |
| एनफ़ोर्समेंट प्रॉक्सी | प्रति LLM कॉल **+9.7 ms** | ऑफ़ |

डेमन होस्ट की लागत: **2,762 इवेंट/सेकंड** इनजेस्ट, डिस्क पर **710 बाइट्स/इवेंट** (100k इवेंट प्रति 67.7 MB), और व्यस्त इंस्टॉल पर लगातार **एक कोर का ~12%**। वह आख़िरी आंकड़ा हमारे बताए गए 5-10% के बजट से ज़्यादा है, इसलिए इसे पेज से हटाने के बजाय पीछा किए जाने लायक एक बग के रूप में प्रकाशित किया गया है।

Apple M2 Pro पर `benchmarks/overhead.py` से मापा गया। हार्नेस हर स्थिति को एक अलग प्रोसेस में चलाता है, उनके क्रम को बदलता रहता है, और **जब राउंड्स उसके चिह्न पर असहमत हों तो कोई आंकड़ा छापने से मना कर देता है**। इसे अपनी मशीन पर एक मिनट में चलाएँ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पथ मापा गया है, जिसमें हुक गेट्स और एनफ़ोर्समेंट प्रॉक्सी शामिल हैं, और यह हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो नतीजे: Windows पर प्रॉक्सी की लागत Linux के मुक़ाबले लगभग सात गुना ज़्यादा है, और डेमन फ़िलहाल एक कोर के लगभग 12% पर टिका रहता है, जो हमारे अपने 5-10% के बजट से ज़्यादा है। कच्चा JSON, तरीका, और जो अभी तक नहीं मापा गया है, वह सब [docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## मूल्य निर्धारण

| प्लान | यह क्या कवर करता है | कीमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताए सभी अन्य रनटाइम, फ़्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | Starter + नियंत्रण और मूल्यांकन: अप्रूवल्स, टूल-रिस्क पॉलिसी, evals, एनोमली डिटेक्शन, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट, टैम्पर-एविडेंट ऑडिट लॉग | $19 प्रति नोड / महीना |

एन्युअल प्लान, Enterprise और मौजूदा आंकड़े **[clawmetry.com/pricing](https://clawmetry.com/pricing)** पर मौजूद हैं। सेल्फ़-होस्टेड लाइसेंस की (`clawmetry license`) क्लाउड के बिना भी काम करती हैं। सटीक फ़्री/पेड बँटवारा [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग पढ़ता है। **जब तक आप `clawmetry connect` नहीं चलाते, तब तक कोई सेशन डेटा आपके बॉक्स से बाहर नहीं जाता** — कोई प्रॉम्प्ट, रिप्लाई, टूल आर्ग्युमेंट्स, फ़ाइल कॉन्टेंट या लॉग लाइन नहीं। जब आप कनेक्ट करते हैं, तो स्नैपशॉट एक ऐसी कुंजी के साथ एंड-टू-एंड एन्क्रिप्टेड होता है जो कभी आपकी मशीन नहीं छोड़ती, और आपके ब्राउज़र में डिक्रिप्ट होता है। अगर किसी नोड के पास कोई कुंजी नहीं है, तो अपलोड को साफ़ भेजने के बजाय छोड़ दिया जाता है, और कोई सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

कनेक्ट करने से पहले डिफ़ॉल्ट रूप से दो चीज़ें चलती हैं, दोनों ऑप्ट-आउट हैं और दोनों में कोई सेशन डेटा नहीं होता: एक अनाम इंस्टॉल पिंग और PyPI के मुक़ाबले एक वर्ज़न चेक। डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए एक बार आपका पब्लिक IP भी देखता है। हर डेस्टिनेशन, वह क्या ले जाता है और उसे कैसे बंद करें, यह सब [docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है; सेल्फ़-होस्टेड, रीपॉइंटेड और एयर-गैप्ड इंस्टॉल कोई भी वैकल्पिक आउटबाउंड कॉल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में, हमारे द्वारा दिए गए कोड में होता है। यह पहले एक वादा हुआ करता था; अब यह कुछ ऐसा है जिसे आप जाँच सकते हैं। आपकी कुंजी को छूने वाली हर लाइन एक पढ़ने लायक फ़ाइल, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js) में रहती है, जो व्हील के अंदर शिप होती है और ज्यों की त्यों परोसी जाती है, एक Subresource Integrity हैश के साथ पिन की गई। यह पुष्टि करने के लिए कि ब्राउज़र वही चलाता है जो हमने प्रकाशित किया है:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह क्या साबित नहीं करता: हम वह पेज परोसते हैं जो फ़ाइल को लोड करता है, इसलिए हम एक अलग पेज भी परोस सकते थे। इंटीग्रिटी हैश आपको एक समझौता किए गए CDN से बचाते हैं, वेंडर से नहीं। आपको जो मिलता है वह यह है कि कोई भी बदलाव जान-बूझकर किया गया होना चाहिए, पेज सोर्स में दिखाई देना चाहिए, और PyPI पर मौजूद उस आर्टिफ़ैक्ट से अलग होना चाहिए जिसे कोई भी फ़ेच कर सकता है। सेल्फ़-होस्टिंग करना या केवल लोकल रहना इस निर्भरता को पूरी तरह हटा देता है।

## इंस्टॉल

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

## दस्तावेज़

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | हर एडाप्टर क्या पढ़ता है, और एक रनटाइम कैसे जोड़ें |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | प्रोवाइडर के हिसाब से विंडो, कॉम्पैक्शन बनाम ओवरफ़्लो, रनटाइम-वार कवरेज |
| [Overhead](docs/OVERHEAD.md) | इंस्ट्रुमेंटेशन की मापी गई लागत, और उसे दोहराने के लिए हार्नेस |
| [Entitlements](docs/ENTITLEMENTS.md) | फ़्री बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एक्ज़ीक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सिरे से सिरे तक, चलाने योग्य उदाहरणों के साथ |
| [SDK tracking](docs/SDK_TRACKING.md) | आपके खुद बनाए एजेंट्स के लिए लागत अट्रिब्यूशन |
| [Chat channels](docs/CHANNELS.md) | Flow में दिखाए गए चैट एडाप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | यह अंदर से कैसे काम करता है; सोर्स से चलाना |
| [Telemetry](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट्स

नीचे दिया गया हर आंकड़ा एक असली मशीन से है, केवल-पढ़ने के तौर पर, बिना किसी सीडिंग के।

**यह आपको बताता है कि कब कुछ गलत है, सिर्फ़ यह नहीं कि क्या हुआ।**
ऊपर दो एनोमली बैनर: खर्च दैनिक औसत का 7 गुना चल रहा है, और एक 4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 में से 324 सेशन में वेस्ट सिग्नल मिला, कारण के हिसाब से बाँटा गया।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहाँ गया, हर विंडो में।**
आज $252.47, इस हफ़्ते $513.15, इस महीने $1,312.92, हर एक के पीछे के टोकन के साथ और इसमें से कितना आपका सब्सक्रिप्शन पहले से कवर करता है। उसके नीचे, लगभग $1,128/महीना रिकवरेबल के रूप में बताया गया और कैश रीयूज़ से पहले से बचाए गए $17,256/महीना।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि एक मैसेज कैसे एक जवाब बनता है।**
लाइव फ़्लो डायग्राम: आप, वह चैनल जिस पर यह आया, गेटवे, अभी जवाब दे रहा मॉडल, और हर वह टूल जिसे उसने इस्तेमाल किया। जैसे-जैसे काम इनमें से गुज़रता है, नोड्स जगमगाते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर हर एजेंट, एक ही टेबल में।**
यह क्या चलाता है, पिछले 24 घंटों में और अपने पूरे जीवनकाल में इसकी लागत कितनी है, इसे आख़िरी बार कब देखा गया, यह किसका है, और क्या कोई सब्सक्रिप्शन बिल कवर कर रहा है। यहाँ 14 एजेंट, 3 सेशन काम कर रहे, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि एक टर्न का समय और पैसा कहाँ गया, टूल दर टूल।**
एक असली सेशन का एक टर्न: 11.2 मिनट में 11 टूल, $1.16 में। हर Bash कॉल और मॉडल कॉल को टाइमलाइन पर अपना बार मिलता है, ताकि 4.1 मिनट चलने वाली कमांड और 226ms चलने वाली कमांड को एक नज़र में अलग पहचाना जा सके।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को आँकता है, सिर्फ़ खर्च को नहीं।**
इस हफ़्ते एक A: 54 काम साफ़-सुथरे तरीके से पूरे हुए, 2 खुरदुरे कामों की लागत $48.57 रही, और जिन रन में आँकने लायक इतनी गतिविधि नहीं थी उन्हें जीत के रूप में गिनने के बजाय ग्रेड से बाहर रखा गया। हर खुरदुरा रन अपने ट्रेस से लिंक होता है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो क्यों भरती जा रही है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% का पीक, 4 कॉम्पैक्शन जो सभी ओवरफ़्लो के बजाय प्रोएक्टिव रूप से चले, साथ ही इसके पीछे हर टर्न का यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**बिना आपके कुछ कॉन्फ़िगर किए डिटेक्शन चलता है।**
बिल्ट-इन डिटेक्टर्स इंस्टॉल से ही ऑन हैं: एजेंट चुप हो गया, टेलीमेट्री फ़ीड रुक गई, कॉस्ट स्पाइक, टोकन बर्स्ट, बढ़ते एरर, एरर स्पाइक, बजट थ्रेशोल्ड, थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फ़ाइंडिंग, सिक्योरिटी पॉस्चर बदला। आपके अपने नियम ऊपर से वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को रोकना ऑप्ट-इन है, और डिफ़ॉल्ट रूप से बंद शिप होता है।**
रिकर्सिव डिलीट, फ़ोर्स पुश, sudo, सीक्रेट्स, पैकेज इंस्टॉल और आउटबाउंड कॉल्स — हर एक को ऐसा नियम मिलता है जिसे आप चालू कर सकते हैं। जब तक आप ऐसा नहीं करते, ClawMetry देखता रहता है और कुछ नहीं बदलता। एक बार चालू होने पर, मैच होने वाली कॉल्स यहाँ (या आपके फ़ोन पर) अप्रूव या डिनाई होने का इंतज़ार करती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

रनटाइम के हिसाब से और भी: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## स्टार इतिहास

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लाइसेंस

MIT · निर्माता [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
