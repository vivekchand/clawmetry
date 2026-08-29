<!-- i18n-src:d21bea5161e0 -->
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

> 🌐 **इसे इस भाषा में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ अपने-आप पहचान लेता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। शून्य कॉन्फ़िगरेशन: यह उन एजेंट रनटाइम्स को ढूँढ लेता है जो आपके पास पहले से हैं, उन्हें केवल-पढ़ने के रूप में एक्सेस करता है, और उनके चलने के तरीक़े में कुछ भी नहीं बदलता।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 एजेंट रनटाइम्स के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को वही डैशबोर्ड मिलता है। एक साथ कई चलाएँ और हेडर स्विचर हर टैब को उनमें से किसी एक पर फिर से स्कोप कर देता है।

अपने SDK पर ख़ुद का एजेंट बनाया है, किसी और चीज़ की बजाय? इंटरसेप्टर उसकी LLM कॉल्स को भी ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **Sessions & transcripts**: हर एजेंट ने क्या किया, टर्न दर टर्न, रीप्ले के साथ
- **Cost & tokens**: रनटाइम, मॉडल, सेशन और दिन के हिसाब से, एनोमली फ़्लैग्स के साथ
- **Flow**: चैनलों, मॉडलों और टूल्स से गुज़रते संदेशों का लाइव डायग्राम
- **Brain**: रीज़निंग और टूल-कॉल इवेंट स्ट्रीम, जैसे-जैसे यह होता है
- **Context blowout**: प्रत्येक प्रोवाइडर के अनुसार आकार दी गई विंडो यूटिलाइज़ेशन, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, साथ ही हम जो *नहीं* देख पाते उसका प्रति-रनटाइम मैप ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: वे फ़ाइलें और स्किल्स जो हर रनटाइम ने वास्तव में लोड कीं
- **Health & logs**: डिस्क, मेमोरी, एरर रेट्स, रेट लिमिट्स, लाइव लॉग स्ट्रीम
- **Alerts**: बजट कैप्स, एरर स्पाइक्स, एजेंट-ऑफ़लाइन, Slack, Discord, PagerDuty, Telegram, Email पर रूट किए गए
- **Approvals**: जोखिम भरी टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अनुमोदित करें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और निगरानी की लागत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले जवाब देने लायक दो सवाल।

**यह रनटाइम्स में कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे संभालता है?**

एक यूटिलाइज़ेशन प्रतिशत उतना ही ईमानदार है जितनी वह चीज़ जिससे उसे विभाजित किया जाता है। ClawMetry हर प्रोवाइडर के लिए विंडो का आकार एक [ऐसी टेबल से तय करता है जिसे आप पढ़ और PR कर सकते हैं](clawmetry/context_windows.py), जो Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama और GLM को कवर करती है। यह सभी 26 रनटाइम्स को एक ही वेंडर के पैमाने से नहीं नापता। यह मायने रखता है: Anthropic के 200K के मुक़ाबले नापा गया GPT-5 का 300K टर्न ">100%, blown" दिखता है जबकि वास्तव में यह GPT-5 के 400K का 75% है। वही पैमाना एक वाक़ई ओवरफ़्लो हुए 130K DeepSeek टर्न को आरामदायक 65% के रूप में छुपा देता है।

हर विंडो अपनी प्रोवेनन्स के साथ आती है: `model_table`, `explicit_marker`, `observed_floor`, या जब हमें मॉडल पता नहीं होता तो एक ईमानदार `default`। अनुमान पर बना गेज कभी उतने ही अधिकार के साथ रेंडर नहीं होता जितना लुकअप पर बना गेज।

ClawMetry कुछ रनटाइम्स पर ही कॉम्पैक्शन इवेंट्स देख सकता है। इसलिए `GET /api/context-coverage` हर रनटाइम के लिए यह रिपोर्ट करता है कि **शून्य का मतलब "साफ़ चला" है या "हम अंधे हैं"**। एक `0` जिसका वाक़ई मतलब अंधापन है, वह यह बताता है। [पूरा विवरण](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रुमेंटेशन की लागत क्या है?**

| Path | आपके एजेंट में जुड़ा | डिफ़ॉल्ट? |
|---|---|---|
| Session-file tailing (सभी 30 रनटाइम्स) | **0**। अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | प्रति LLM कॉल **+0.44 ms**, यानी 5s कॉल का 0.009% | off |
| Pre-tool hook gate (warm cache) | 36 ms के इंटरप्रेटर फ़्लोर के ऊपर, प्रति गेटेड टूल कॉल **+44 ms** | off |
| Enforcement proxy | प्रति LLM कॉल **+9.7 ms** | off |

Daemon host cost: **2,762 events/sec** इंजेस्ट, डिस्क पर **710 bytes/event** (100k इवेंट्स के लिए 67.7 MB), और व्यस्त इंस्टॉल पर सस्टेन्ड रूप से **एक कोर का लगभग 12%**। वह आख़िरी आँकड़ा हमारे अपने बताए गए 5-10% बजट से ऊपर है, इसलिए इसे पीछे छोड़ने की बजाय एक बग के रूप में प्रकाशित किया गया है जिसका पीछा करना है।

Apple M2 Pro पर `benchmarks/overhead.py` से नापा गया। हार्नेस हर कंडीशन को अलग प्रोसेस में चलाता है, उनका क्रम बदलता रहता है, और **जब राउंड्स उसके साइन पर असहमत होते हैं तो नंबर प्रिंट करने से इनकार कर देता है**। इसे अपनी मशीन पर एक मिनट में चलाएँ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पाथ नापा गया है, जिसमें hook gates और enforcement proxy शामिल हैं, और हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो नतीजे: प्रॉक्सी की लागत Windows पर Linux के मुक़ाबले क़रीब सात गुना ज़्यादा है, और डेमन फ़िलहाल एक कोर का लगभग 12% सस्टेन करता है, जो हमारे अपने 5-10% बजट से ऊपर है। रॉ JSON, तरीक़ा, और अभी तक क्या नहीं नापा गया है, यह सब [docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## Pricing

| Plan | यह क्या कवर करता है | Price |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताए गए बाक़ी सभी रनटाइम्स, फ़्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | Starter + नियंत्रण और मूल्यांकन: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 प्रति नोड / महीना |

वार्षिक प्लान, Enterprise और मौजूदा आँकड़े यहाँ मिलते हैं
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**। सेल्फ़-होस्टेड लाइसेंस
की तक क्लाउड के बिना काम करती हैं (`clawmetry license`)। फ़्री/पेड का सटीक विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग पढ़ता है। **कोई सेशन डेटा आपके बॉक्स से बाहर तभी जाता है जब आप `clawmetry connect` चलाते हैं** — कोई प्रॉम्प्ट, रिप्लाई, टूल आर्ग्युमेंट, फ़ाइल कंटेंट या लॉग लाइन नहीं। जब आप कनेक्ट करते हैं, तो स्नैपशॉट ऐसी कुंजी के साथ एंड-टू-एंड एन्क्रिप्टेड होता है जो कभी आपकी मशीन नहीं छोड़ती, और आपके ब्राउज़र में डिक्रिप्ट होती है। अगर किसी नोड के पास कुंजी नहीं है, तो अपलोड को साफ़ भेजने की बजाय छोड़ दिया जाता है, और कोई सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

दो चीज़ें कनेक्ट करने से पहले भी डिफ़ॉल्ट रूप से चलती हैं, दोनों ऑप्ट-आउट और दोनों में कोई सेशन डेटा नहीं होता: एक अनाम इंस्टॉल पिंग और PyPI के मुक़ाबले एक वर्ज़न चेक। एक डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए आपका पब्लिक IP भी एक बार देखता है। हर डेस्टिनेशन, वह क्या ले जाता है और उसे कैसे बंद करें, यह सब [docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है; सेल्फ़-होस्टेड, रीपॉइंटेड और एयर-गैप्ड इंस्टॉल कोई भी स्वेच्छिक आउटबाउंड कॉल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में होता है, हमारे द्वारा दिए गए कोड में। यह पहले एक वादा था; अब यह ऐसी चीज़ है जिसे आप जाँच सकते हैं। आपकी कुंजी को छूने वाली हर लाइन एक पढ़ने-योग्य फ़ाइल में है, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), जो व्हील के अंदर शिप होती है और जस-की-तस सर्व की जाती है, जो Subresource Integrity हैश से पिन की गई है। यह पुष्टि करने के लिए कि ब्राउज़र वही चलाता है जो हमने प्रकाशित किया है:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह क्या साबित नहीं करता: हम वह पेज सर्व करते हैं जो फ़ाइल लोड करता है, इसलिए हम एक अलग पेज सर्व कर सकते हैं। इंटीग्रिटी हैश आपको एक कॉम्प्रोमाइज़्ड CDN से बचाते हैं, वेंडर से नहीं। आपको जो फ़ायदा मिलता है वह यह है कि किसी भी सब्स्टिट्यूशन को जान-बूझकर, पेज सोर्स में दिखने योग्य, और PyPI पर मौजूद उस आर्टिफ़ैक्ट से अलग होना पड़ेगा जिसे कोई भी फ़ेच कर सकता है। सेल्फ़-होस्टिंग या केवल-लोकल रहने से यह निर्भरता पूरी तरह ख़त्म हो जाती है।

## Install

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

## Docs

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | हर एडैप्टर क्या पढ़ता है, और एक रनटाइम कैसे जोड़ें |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोवाइडर विंडोज़, कॉम्पैक्शन बनाम ओवरफ़्लो, प्रति-रनटाइम कवरेज |
| [Overhead](docs/OVERHEAD.md) | इंस्ट्रुमेंटेशन की लागत क्या है, नापी गई, इसे रीप्रोड्यूस करने वाले हार्नेस के साथ |
| [Entitlements](docs/ENTITLEMENTS.md) | फ़्री बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एग्ज़िक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इंजेस्ट करें |
| [SDK tracking](docs/SDK_TRACKING.md) | आपके अपने बनाए गए एजेंट्स के लिए कॉस्ट अट्रिब्यूशन |
| [Chat channels](docs/CHANNELS.md) | Flow में दिखाए गए चैट एडैप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट्स |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | अंदर यह कैसे काम करता है; सोर्स से चलाना |
| [Telemetry](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग्स, और उन्हें कैसे बंद करें |

## Screenshots

नीचे दिया हर आँकड़ा एक असली मशीन से है, केवल-पढ़ने के रूप में, बिना किसी सीडिंग के।

**यह आपको बताता है कि कब कुछ ग़लत है, न कि सिर्फ़ यह कि क्या हुआ।**
सबसे ऊपर दो एनोमली बैनर: खर्च दैनिक औसत का 7 गुना चल रहा है, और 4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 सेशंस में से 324 में वेस्ट सिग्नल मौजूद है, कारण के हिसाब से अलग-अलग सूचीबद्ध।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहाँ गया, हर विंडो में।**
आज $252.47, इस हफ़्ते $513.15, इस महीने $1,312.92, हर एक के पीछे के टोकन्स के साथ और यह भी कि आपकी सब्सक्रिप्शन इसमें से पहले से कितना कवर करती है। उसके नीचे, लगभग $1,128/माह को रिकवरेबल के रूप में और $17,256/माह को कैश रीयूज़ द्वारा पहले ही बचाए गए के रूप में सूचीबद्ध किया गया है।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि एक संदेश जवाब कैसे बनता है।**
लाइव फ़्लो डायग्राम: आप, वह चैनल जिस पर संदेश आया, गेटवे, अभी जवाब दे रहा मॉडल, और हर वह टूल जिसे उसने इस्तेमाल किया। जैसे-जैसे काम आगे बढ़ता है, नोड्स रोशन होते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर मौजूद हर एजेंट, एक ही टेबल में।**
यह क्या चलाता है, पिछले 24 घंटों में और अपने पूरे जीवनकाल में इसकी लागत क्या है, इसे आख़िरी बार कब देखा गया, इसका मालिक कौन है, और क्या कोई सब्सक्रिप्शन बिल कवर कर रही है। यहाँ 14 एजेंट, 3 सेशंस काम कर रहे, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि एक टर्न का समय और पैसा कहाँ गया, टूल दर टूल।**
एक असली सेशन का एक टर्न: 11.2 मिनट में 11 टूल्स, $1.16 में। हर Bash कॉल और मॉडल कॉल को टाइमलाइन पर अपनी बार मिलती है, ताकि जो कमांड 4.1 मिनट चला और जो 226ms चला, दोनों एक नज़र में अलग पहचाने जा सकें।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को आँकता है, न कि सिर्फ़ खर्च को।**
इस हफ़्ते A ग्रेड: 54 टास्क साफ़-सुथरे वापस आए, 2 कठिन टास्क की लागत $48.57 रही, और जिन रन्स में आँकने लायक़ पर्याप्त गतिविधि नहीं थी उन्हें जीत के रूप में गिनने की बजाय ग्रेड से बाहर रखा गया। हर कठिन रन अपने ट्रेस से जुड़ा है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो लगातार क्यों भरती रहती है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% पीक, 4 कॉम्पैक्शन जो सभी ओवरफ़्लो पर नहीं बल्कि प्रोएक्टिव रूप से हुए, साथ ही उसके पीछे हर टर्न का यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**डिटेक्शन बिना आपके कुछ कॉन्फ़िगर किए चलता है।**
इनबिल्ट डिटेक्टर्स इंस्टॉल से ही ऑन हैं: एजेंट शांत हो गया, टेलीमेट्री फ़ीड रुक गई, कॉस्ट स्पाइक, टोकन बर्स्ट, बढ़ती त्रुटियाँ, एरर स्पाइक, बजट थ्रेशोल्ड, थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फ़ाइंडिंग, सिक्योरिटी पोस्चर बदला। आपके अपने नियम इसके ऊपर वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को रोकना ऑप्ट-इन है, और डिफ़ॉल्ट रूप से बंद शिप होता है।**
Recursive deletes, force pushes, sudo, secrets, package installs और आउटबाउंड कॉल्स — हर एक को अपना नियम मिलता है जिसे आप चालू कर सकते हैं। जब तक आप ऐसा नहीं करते, ClawMetry देखता रहता है और कुछ नहीं बदलता। एक बार चालू होने पर, मेल खाती कॉल्स यहाँ (या आपके फ़ोन पर) अप्रूव या डिनाई होने के लिए रुक जाती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रति रनटाइम: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT · [@vivekchand](https://github.com/vivekchand) द्वारा बनाया गया · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
