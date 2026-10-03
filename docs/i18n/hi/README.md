<!-- i18n-src:c99ac0512cae -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एक एजेंट बिना किसी प्रगति के सौ टूल कॉल कर सकता है।** ClawMetry उन सेशन फ़ाइलों को पढ़ता है जिन्हें आपके कोडिंग एजेंट पहले से ही लिखते हैं, और टाइमलाइन, टूल कॉल्स, तथा रनटाइम जो भी टोकन और लागत डेटा उजागर करता है, उसे एक ही व्यू में रख देता है, ताकि आप बता सकें कि कोई लंबा रन काम कर रहा है या अटका हुआ है।

**33 AI एजेंट रनटाइम्स** के साथ काम करता है, Claude Code, OpenAI Codex, Hermes, OpenClaw और 29 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक डैशबोर्ड। ([पूरी सूची](SUPPORTED_RUNTIMES.txt), कैटलॉग से जनरेट की गई।)

> 🌐 **इसे इसमें पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िग। सब कुछ अपने आप पहचान लेता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। ज़ीरो कॉन्फ़िग: यह उन एजेंट रनटाइम्स को ढूंढ लेता है जो आपके पास पहले से हैं, उन्हें रीड-ओनली तरीके से पढ़ता है, और उनके चलने के तरीके में कुछ भी नहीं बदलता।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इंस्टॉल करने से पहले

| | |
|---|---|
| **यह क्या करता है** | उन सेशन फ़ाइलों और लॉग को पढ़ता है जो आपके एजेंट पहले से ही लिखते हैं। कोई SDK नहीं, कोड में कोई बदलाव नहीं, आपके ऐप में कोई इंस्ट्रूमेंटेशन नहीं। |
| **आप क्या देखते हैं** | सेशन टाइमलाइन, टूल-दर-टूल रीप्ले, टोकन और लागत का विवरण, और ट्रैजेक्टरी सिग्नल (लूपिंग, बार-बार विफलता) प्रति रनटाइम। |
| **क्या मुफ़्त है** | `pip install clawmetry` बिना किसी अकाउंट, बिना की और बिना नेटवर्क कॉल के **OpenClaw, NVIDIA NemoClaw, Goose और Qwen Code** को पढ़ता है। बाकी 28, Claude Code, Codex, Cursor और बाकी सब, क्लोज़्ड-सोर्स `clawmetry-pro` कंपेनियन द्वारा पढ़े जाते हैं, जो 7-दिन के ट्रायल या किसी प्लान के साथ आता है, सटीक विभाजन के लिए देखें [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)। |
| **कैसे शुरू करें** | `pip install clawmetry && clawmetry`, फिर localhost:8900 खोलें। इस मशीन पर अभी तक कोई एजेंट नहीं है? `clawmetry --sample` तीन लेबल किए गए सिंथेटिक सेशनों के साथ खुलता है। |
| **आपकी मशीन से क्या बाहर जाता है** | कोई सेशन डेटा नहीं, जब तक आप `clawmetry connect` नहीं चलाते। डिफ़ॉल्ट रूप से दो चीज़ें चलती हैं, दोनों ऑप्ट-आउट हैं और दोनों में कोई सेशन कंटेंट नहीं होता: एक अनाम इंस्टॉल पिंग और एक PyPI वर्शन चेक। हर गंतव्य [docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है, जो टिप्पणियाँ पढ़ने के बजाय वायर कैप्चर से बनाई गई है। |

दो सीमाएँ, जिन्हें आउटपुट को परखने से पहले जान लेना उपयोगी है: रनटाइम बहुत अलग-अलग डेटा उजागर करते हैं (कुछ कोई लागत बिल्कुल नहीं दिखाते, [मैट्रिक्स](docs/compatibility.md) बताता है कि कौन-सा, प्रति रनटाइम), और किसी कार्रवाई को देख पाना उसे रोक पाने जैसा नहीं है ([कौन-से नियंत्रण असली हैं, प्रति रनटाइम](docs/APPROVALS.md))।


## 33 एजेंट रनटाइम्स के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**किसी पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को एक ही डैशबोर्ड मिलता है। एक साथ कई चलाएँ और हेडर स्विचर हर टैब को उनमें से किसी एक के दायरे में फिर से सेट कर देता है।

अपना खुद का एजेंट किसी SDK पर बनाया है? इंटरसेप्टर उसकी LLM कॉल्स को भी ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न दर टर्न, रीप्ले के साथ
- **लागत और टोकन**: प्रति रनटाइम, मॉडल, सेशन और दिन, एनोमली फ़्लैग के साथ
- **फ़्लो**: चैनलों, मॉडलों और टूल्स से गुज़रते संदेशों का लाइव डायग्राम
- **ब्रेन**: रीज़निंग और टूल-कॉल इवेंट स्ट्रीम, जैसे ही वह होता है
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोवाइडर के अनुसार विंडो उपयोग का आकार, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, साथ ही यह नक्शा कि हम प्रति रनटाइम *क्या नहीं* देख पाते ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जिन्हें हर रनटाइम ने वास्तव में लोड किया
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर दर, रेट लिमिट, लाइव लॉग स्ट्रीम
- **अलर्ट**: बजट कैप, एरर स्पाइक, एजेंट-ऑफ़लाइन, जो Slack, Discord, PagerDuty, Telegram, Email पर भेजे जाते हैं
- **अप्रूवल्स**: जोखिम भरी टूल कॉल्स को चलने से *पहले* रोकें और अपने फ़ोन से स्वीकृति दें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और निगरानी की कीमत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले दो सवाल जान लेने लायक हैं।

**यह रनटाइम्स में कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे संभालता है?**

यूटिलाइज़ेशन प्रतिशत उतना ही ईमानदार होता है जितनी वह संख्या जिससे उसे विभाजित किया जाता है। ClawMetry प्रति प्रोवाइडर विंडो का आकार एक [ऐसी टेबल](clawmetry/context_windows.py) से तय करता है जिसे आप पढ़ और PR कर सकते हैं, जिसमें Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama और GLM शामिल हैं। यह सभी 33 रनटाइम्स को एक ही वेंडर के पैमाने से नहीं नापता। यह मायने रखता है: Anthropic के 200K के मुकाबले नापा गया एक 300K GPT-5 टर्न ">100%, blown" पढ़ता है जबकि वह वास्तव में GPT-5 के 400K का 75% है। वही पैमाना एक वाकई ओवरफ़्लो हो चुके 130K DeepSeek टर्न को एक आरामदायक 65% के रूप में छुपा देता है।

हर विंडो अपने प्रॉवनेंस के साथ आती है: `model_table`, `explicit_marker`, `observed_floor`, या जब हमें मॉडल का पता न हो तो एक ईमानदार `default`। अनुमान पर बना गेज कभी भी लुकअप पर बने गेज जितना भरोसेमंद नहीं दिखता।

ClawMetry कुछ ही रनटाइम्स पर कॉम्पैक्शन इवेंट देख पाता है। इसलिए `GET /api/context-coverage` प्रति रनटाइम यह रिपोर्ट करता है कि क्या **ज़ीरो का मतलब "साफ़ चला" है या "हमें दिखाई नहीं देता"**। एक `0` जिसका वाकई मतलब अंधा होना है, वह यह बता देता है।
[पूरी जानकारी](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रूमेंटेशन की कीमत क्या है?**

| पाथ | आपके एजेंट में जोड़ा गया | डिफ़ॉल्ट? |
|---|---|---|
| सेशन-फ़ाइल टेलिंग (सभी 33 रनटाइम्स) | **0**। अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | on |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रति LLM कॉल **+0.44 ms**, यानी 5s कॉल का 0.009% | off |
| प्री-टूल हुक गेट (वॉर्म कैश) | प्रति गेटेड टूल कॉल **+44 ms**, 36 ms इंटरप्रेटर फ़्लोर के ऊपर | off |
| एन्फ़ोर्समेंट प्रॉक्सी | प्रति LLM कॉल **+9.7 ms** | off |

डेमन होस्ट कॉस्ट: **2,762 इवेंट्स/सेकंड** इनजेस्ट, डिस्क पर **710 बाइट्स/इवेंट** (1 लाख इवेंट्स पर 67.7 MB), और एक व्यस्त इंस्टॉल पर लगातार **एक कोर का ~12%**। वह आखिरी नंबर हमारे अपने बताए गए 5-10% बजट से ज़्यादा है, इसलिए इसे पीछे छिपाने के बजाय एक बग के रूप में प्रकाशित किया गया है, जिसे ठीक किया जाना बाकी है।

Apple M2 Pro पर `benchmarks/overhead.py` से नापा गया। हार्नेस हर स्थिति को अलग प्रोसेस में चलाता है, उनका क्रम बदलता रहता है, और **जब राउंड उसके साइन पर सहमत नहीं होते तो कोई संख्या नहीं छापता**। इसे अपनी ही मशीन पर एक मिनट में चलाएँ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पाथ नापा जाता है, जिसमें हुक गेट्स और एन्फ़ोर्समेंट प्रॉक्सी शामिल हैं, और हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो नतीजे: Windows पर प्रॉक्सी की कीमत Linux की तुलना में लगभग सात गुना ज़्यादा है, और डेमन फ़िलहाल एक कोर का लगभग 12% इस्तेमाल करता है, जो हमारे अपने 5-10% बजट से ज़्यादा है। रॉ JSON, तरीका, और जो अभी तक नहीं नापा गया है वह सब [docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## प्राइसिंग

| प्लान | यह क्या कवर करता है | कीमत |
|---|---|---|
| **फ़्री** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **स्टार्टर** | ऊपर के बाकी सभी रनटाइम्स, फ़्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | स्टार्टर + नियंत्रण और मूल्यांकन: अप्रूवल्स, टूल-रिस्क पॉलिसीज़, evals, एनोमली डिटेक्शन, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट, टैम्पर-एविडेंट ऑडिट लॉग | $19 प्रति नोड / महीना |

वार्षिक प्लान, Enterprise और मौजूदा कीमतें **[clawmetry.com/pricing](https://clawmetry.com/pricing)** पर हैं। सेल्फ़-होस्टेड लाइसेंस की बिना क्लाउड के भी काम करती हैं (`clawmetry license`)। मुफ़्त/पेड का सटीक विभाजन [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग पढ़ता है। **जब तक आप `clawmetry connect` नहीं चलाते, आपके बॉक्स से कोई सेशन डेटा बाहर नहीं जाता**, कोई प्रॉम्प्ट, जवाब, टूल आर्गुमेंट, फ़ाइल कंटेंट या लॉग लाइन नहीं। जब आप कनेक्ट करते हैं, तो स्नैपशॉट एंड-टू-एंड एन्क्रिप्टेड होता है, ऐसी की के साथ जो कभी आपकी मशीन नहीं छोड़ती, और आपके ब्राउज़र में डिक्रिप्ट होता है। अगर किसी नोड के पास की नहीं है, तो अपलोड को खुले में भेजने के बजाय छोड़ दिया जाता है, और कोई भी सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

कनेक्ट करने से पहले डिफ़ॉल्ट रूप से दो चीज़ें चलती हैं, दोनों ऑप्ट-आउट हैं और दोनों में कोई सेशन डेटा नहीं होता: एक अनाम इंस्टॉल पिंग और PyPI के मुकाबले एक वर्शन चेक। एक डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए आपका पब्लिक IP भी एक बार देखता है। हर गंतव्य, वह क्या ले जाता है, और उसे कैसे बंद करें, यह सब [docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है; सेल्फ़-होस्टेड, रीपॉइंटेड और एयर-गैप्ड इंस्टॉल कोई भी स्वैच्छिक आउटबाउंड कॉल बिल्कुल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में, हमारे द्वारा भेजे गए कोड में होता है। यह पहले एक वादा था; अब यह कुछ ऐसा है जिसे आप जांच सकते हैं। आपकी की को छूने वाली हर लाइन एक ही पढ़ने लायक फ़ाइल में है, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), जो व्हील के अंदर शिप होती है और ज्यों की त्यों सर्व होती है, Subresource Integrity हैश के साथ पिन की हुई। यह पुष्टि करने के लिए कि ब्राउज़र वही चलाता है जो हमने प्रकाशित किया:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह जो साबित नहीं करता: हम वह पेज सर्व करते हैं जो फ़ाइल को लोड करता है, इसलिए हम एक अलग पेज भी सर्व कर सकते हैं। इंटीग्रिटी हैश आपको किसी भ्रष्ट CDN से बचाते हैं, वेंडर से नहीं। आपको जो मिलता है वह यह है कि कोई भी प्रतिस्थापन जानबूझकर, पेज सोर्स में दिखाई देने वाला, और PyPI पर मौजूद किसी भी व्यक्ति के फ़ेच कर सकने वाले आर्टिफ़ैक्ट से अलग होना चाहिए। सेल्फ़-होस्टिंग करना या सिर्फ़ लोकल रहना इस निर्भरता को पूरी तरह हटा देता है।

## इंस्टॉल

```bash
pip install clawmetry     # फिर: clawmetry
```

या एक-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

या एजेंट को ही यह सेटअप करने दें। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot या OpenCode को सिखाती है कि कैसे ClawMetry इंस्टॉल करें, यह रिपोर्ट करें कि मशीन पर मौजूद एजेंट क्या कर रहे हैं और कितना खर्च कर रहे हैं, अनुरोध पर एक सेशन रोकें, और जोखिम भरी टूल कॉल्स को स्वीकृति के लिए रोककर रखें:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तावेज़

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | हर एडाप्टर क्या पढ़ता है, और एक रनटाइम कैसे जोड़ें |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोवाइडर विंडो, कॉम्पैक्शन बनाम ओवरफ़्लो, प्रति-रनटाइम कवरेज |
| [Overhead](docs/OVERHEAD.md) | इंस्ट्रूमेंटेशन की नापी गई कीमत, और उसे दोहराने के लिए हार्नेस |
| [Entitlements](docs/ENTITLEMENTS.md) | फ़्री बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एक्ज़िक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain शुरू से अंत तक, चलने योग्य उदाहरणों के साथ |
| [SDK tracking](docs/SDK_TRACKING.md) | आपने खुद बनाए एजेंट्स के लिए लागत का श्रेय |
| [Chat channels](docs/CHANNELS.md) | Flow में दिखाए गए चैट एडाप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स किए गए NVIDIA NemoClaw सेटअप |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | यह अंदर से कैसे काम करता है; सोर्स से चलाना |
| [Telemetry](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट

नीचे की हर संख्या एक असली मशीन से है, रीड-ओनली, बिना कुछ भी सीड किए।

**यह आपको तब बताता है जब कुछ गलत होता है, सिर्फ़ यह नहीं कि क्या हुआ।**
ऊपर दो एनोमली बैनर: खर्च दैनिक औसत से 7 गुना चल रहा है, और एक 4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 सेशनों में से 324 में वेस्ट सिग्नल, कारण के अनुसार विभाजित।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहाँ गया, हर विंडो में।**
आज $252.47, इस हफ़्ते $513.15, इस महीने $1,312.92, हर एक के पीछे के टोकन और यह कि आपकी सब्सक्रिप्शन इसमें से कितना पहले से कवर करती है। उसके नीचे, लगभग $1,128/महीना को रिकवरेबल के रूप में और कैश रीयूज़ से पहले से बचाए गए $17,256/महीना को विस्तार से दिखाया गया है।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि कोई संदेश जवाब कैसे बनता है।**
लाइव फ़्लो डायग्राम: आप, वह चैनल जिस पर यह आया, गेटवे, अभी जवाब दे रहा मॉडल, और हर वह टूल जिसे उसने इस्तेमाल किया। जैसे-जैसे काम उनसे होकर गुज़रता है, नोड्स जगमगाते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर मौजूद हर एजेंट, एक ही टेबल में।**
यह क्या चलाता है, पिछले 24 घंटों में और अपने पूरे जीवनकाल में इसकी लागत कितनी है, इसे आखिरी बार कब देखा गया, इसका मालिक कौन है, और क्या कोई सब्सक्रिप्शन बिल कवर कर रही है। यहाँ 14 एजेंट, 3 सेशन काम कर रहे, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि किसी टर्न का समय और पैसा टूल दर टूल कहाँ गया।**
एक असली सेशन का एक टर्न: 11.2 मिनट में 11 टूल्स, $1.16 में। हर Bash कॉल और मॉडल कॉल को टाइमलाइन पर अपना बार मिलता है, ताकि 4.1 मिनट तक चलने वाले कमांड और 226ms में चलने वाले कमांड को एक नज़र में अलग पहचाना जा सके।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को परखता है, सिर्फ़ खर्च को नहीं।**
इस हफ़्ते एक A: 54 टास्क साफ़ वापस आए, 2 मुश्किल टास्क की कीमत $48.57 रही, और जिन रन में परखने लायक पर्याप्त गतिविधि नहीं थी उन्हें जीत के रूप में गिनने के बजाय ग्रेड से बाहर रखा गया। हर मुश्किल रन अपने ट्रेस से जुड़ा है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो लगातार क्यों भरती जाती है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% का पीक, 4 कॉम्पैक्शन जो सभी ओवरफ़्लो के बजाय प्रोएक्टिव रूप से फ़ायर हुए, और इसके पीछे हर टर्न का यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**बिना आपके कुछ भी कॉन्फ़िगर किए डिटेक्शन चलता है।**
बिल्ट-इन डिटेक्टर इंस्टॉल से ही चालू हैं: एजेंट चुप हो गया, टेलीमेट्री फ़ीड रुक गई, कॉस्ट स्पाइक, टोकन बर्स्ट, बढ़ती त्रुटियाँ, एरर स्पाइक, बजट थ्रेशोल्ड, थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फ़ाइंडिंग, सिक्योरिटी पोस्चर बदला। आपके अपने नियम इसके ऊपर वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को रोकना ऑप्ट-इन है, और डिफ़ॉल्ट रूप से बंद शिप होता है।**
रिकर्सिव डिलीट, फ़ोर्स पुश, sudo, सीक्रेट्स, पैकेज इंस्टॉल और आउटबाउंड कॉल्स में से हर एक के लिए एक नियम है जिसे आप चालू कर सकते हैं। जब तक आप ऐसा नहीं करते, ClawMetry बस देखता रहता है और कुछ नहीं बदलता। एक बार चालू होने पर, मैच होने वाली कॉल्स यहाँ (या आपके फ़ोन पर) स्वीकृति या अस्वीकृति के लिए रुकती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

और भी, प्रति रनटाइम: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## पहचान

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
