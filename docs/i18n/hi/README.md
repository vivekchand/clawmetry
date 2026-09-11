<!-- i18n-src:12b97259721e -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एक एजेंट बिना कोई प्रगति किए सौ टूल कॉल कर सकता है।** ClawMetry
आपके कोडिंग एजेंट पहले से जो सेशन फ़ाइलें लिखते हैं उन्हें पढ़ता है, और टाइमलाइन,
टूल कॉल्स, और रनटाइम जो भी टोकन और लागत डेटा उजागर करता है उसे एक ही
व्यू में लाता है — ताकि आप बता सकें कि कौन सा लंबा रन काम कर रहा है और कौन सा अटका हुआ है।

**31 AI एजेंट रनटाइम्स** के साथ काम करता है — Claude Code, OpenAI Codex, Hermes, OpenClaw और 27 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक डैशबोर्ड। ([पूरी सूची](SUPPORTED_RUNTIMES.txt), कैटलॉग से जनरेट की गई।)

> 🌐 **इसे इनमें पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िग। सब कुछ अपने आप पहचान लेता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। शून्य कॉन्फ़िग: यह उन एजेंट रनटाइम्स को खोज लेता है
जो आपके पास पहले से हैं, उन्हें केवल-पढ़ने के लिए (read-only) पढ़ता है, और उनके चलने के तरीके में कुछ भी नहीं बदलता।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इंस्टॉल करने से पहले

| | |
|---|---|
| **यह क्या करता है** | आपके एजेंट पहले से जो सेशन फ़ाइलें और लॉग लिखते हैं उन्हें पढ़ता है। कोई SDK नहीं, कोई कोड बदलाव नहीं, आपके ऐप में कोई इंस्ट्रूमेंटेशन नहीं। |
| **आप क्या देखते हैं** | सेशन टाइमलाइन, टूल-दर-टूल रीप्ले, टोकन और लागत का ब्रेकडाउन, और ट्रैजेक्टरी सिग्नल (लूपिंग, बार-बार होने वाली विफलताएं) — प्रति रनटाइम। |
| **मुफ़्त में क्या है** | `pip install clawmetry` बिना किसी अकाउंट, बिना की और बिना नेटवर्क कॉल के **OpenClaw, NVIDIA NemoClaw और Goose** को पढ़ता है। बाकी 27 — Claude Code, Codex, Cursor और बाकी — को क्लोज़्ड-सोर्स `clawmetry-pro` कम्पैनियन पढ़ता है, जो 7-दिन के ट्रायल या किसी प्लान के साथ आता है — सटीक विभाजन के लिए [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) देखें। |
| **कैसे शुरू करें** | `pip install clawmetry && clawmetry`, फिर localhost:8900 खोलें। इस मशीन पर अभी कोई एजेंट नहीं है? `clawmetry --sample` तीन लेबल किए गए सिंथेटिक सेशंस के साथ खुलता है। |
| **आपकी मशीन से क्या बाहर जाता है** | कोई सेशन डेटा नहीं, जब तक आप `clawmetry connect` न चलाएं। डिफ़ॉल्ट रूप से दो चीज़ें ज़रूर चलती हैं, दोनों ऑप्ट-आउट करने योग्य हैं और दोनों में कोई सेशन कंटेंट नहीं होता: एक अनाम इंस्टॉल पिंग और एक PyPI वर्ज़न चेक। हर गंतव्य [docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है, जो कमेंट्स पढ़कर नहीं बल्कि वायर कैप्चर से बनाया गया है। |

आउटपुट को परखने से पहले दो सीमाएं जान लेना ज़रूरी है: रनटाइम्स बहुत
अलग-अलग डेटा उजागर करते हैं (कुछ तो कोई लागत ही प्रकाशित नहीं करते — [मैट्रिक्स](docs/compatibility.md)
बताता है कि किस रनटाइम में क्या है), और किसी कार्रवाई को देख पाना उसे
रोक पाने के बराबर नहीं है ([कौन से नियंत्रण वास्तविक हैं, प्रति रनटाइम](docs/APPROVALS.md))।


## 31 एजेंट रनटाइम्स के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को वही डैशबोर्ड मिलता है। एक साथ कई चलाएं और हेडर
स्विचर हर टैब को उनमें से किसी एक पर फिर से स्कोप कर देता है।

अपना खुद का एजेंट किसी SDK पर बनाया है? इंटरसेप्टर उसकी LLM कॉल्स भी
ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशंस और ट्रांसक्रिप्ट्स**: हर एजेंट ने क्या किया, बारी-बारी से, रीप्ले के साथ
- **लागत और टोकन**: प्रति रनटाइम, मॉडल, सेशन और दिन, विसंगति फ्लैग्स के साथ
- **फ़्लो**: चैनलों, मॉडलों और टूल्स से होकर गुज़रते संदेशों का लाइव डायग्राम
- **ब्रेन**: होते ही रीज़निंग और टूल-कॉल इवेंट स्ट्रीम
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोवाइडर के अनुसार साइज़ की गई विंडो यूटिलाइज़ेशन, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, साथ ही यह प्रति-रनटाइम नक्शा कि हम *क्या नहीं* देख सकते ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जिन्हें हर रनटाइम ने वास्तव में लोड किया
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर रेट्स, रेट लिमिट्स, लाइव लॉग स्ट्रीम
- **अलर्ट्स**: बजट कैप्स, एरर स्पाइक्स, एजेंट-ऑफ़लाइन, Slack, Discord, PagerDuty, Telegram, Email पर रूट किए गए
- **अप्रूवल्स**: जोखिम भरी टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और मॉनिटरिंग की लागत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले दो सवाल जिनका जवाब जानना ज़रूरी है।

**यह रनटाइम्स में कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे संभालता है?**

यूटिलाइज़ेशन प्रतिशत उतना ही ईमानदार होता है जितना कि वह जिससे विभाजित है। ClawMetry
[एक टेबल](clawmetry/context_windows.py) से हर प्रोवाइडर के अनुसार विंडो साइज़ करता है, जिसे आप पढ़ और
PR कर सकते हैं, जो Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama और GLM को कवर करती है। यह सभी 31
रनटाइम्स को एक ही वेंडर के पैमाने से नहीं मापता। यह मायने रखता है: Anthropic के
200K के मुकाबले मापा गया एक 300K GPT-5 टर्न ">100%, blown" पढ़ता है जबकि वह
असल में GPT-5 के 400K का 75% है। वही पैमाना असल में ओवरफ़्लो हो चुके एक
130K DeepSeek टर्न को एक आरामदायक 65% के रूप में छुपा देता है।

हर विंडो अपने साथ अपना स्रोत लेकर आती है: `model_table`, `explicit_marker`,
`observed_floor`, या मॉडल पता न होने पर ईमानदार `default`। अनुमान पर बना
गेज कभी भी लुकअप पर बने गेज जितने भरोसे के साथ नहीं दिखता।

ClawMetry केवल कुछ रनटाइम्स पर ही कॉम्पैक्शन इवेंट्स देख सकता है। इसलिए
`GET /api/context-coverage` प्रति रनटाइम रिपोर्ट करता है कि क्या **शून्य का मतलब
"साफ़ चला" है या "हम अंधे हैं"**। जो `0` वास्तव में अंधेपन का मतलब रखता है, वह ऐसा ज़ाहिर करता है।
[पूरी जानकारी](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रूमेंटेशन की लागत कितनी है?**

| पाथ | आपके एजेंट में जुड़ा | डिफ़ॉल्ट? |
|---|---|---|
| सेशन-फ़ाइल टेलिंग (सभी 31 रनटाइम्स) | **0**। अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | on |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रति LLM कॉल **+0.44 ms**, यानी 5s कॉल का 0.009% | off |
| प्री-टूल हुक गेट (warm cache) | 36 ms के इंटरप्रेटर फ़्लोर के ऊपर, प्रति गेटेड टूल कॉल **+44 ms** | off |
| एनफ़ोर्समेंट प्रॉक्सी | प्रति LLM कॉल **+9.7 ms** | off |

डेमन होस्ट लागत: **2,762 इवेंट्स/सेकंड** इनजेस्ट, डिस्क पर **710 बाइट्स/इवेंट**
(100k इवेंट्स के लिए 67.7 MB), और व्यस्त इंस्टॉल पर सस्टेन्ड **~12% एक कोर का**। वह
आखिरी नंबर हमारे अपने बताए गए 5-10% बजट से ऊपर है, इसलिए इसे पेज से हटाने के
बजाय एक बग के रूप में प्रकाशित किया गया है जिसे ठीक करना है।

Apple M2 Pro पर `benchmarks/overhead.py` से मापा गया। हार्नेस हर
कंडीशन को एक अलग प्रोसेस में चलाता है, उनका क्रम बदलता रहता है, और
**राउंड्स के चिह्न (sign) पर असहमत होने पर नंबर प्रिंट करने से इनकार करता है**। इसे
अपनी मशीन पर एक मिनट में चलाएं:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पाथ मापा गया है, जिसमें हुक गेट्स और एनफ़ोर्समेंट प्रॉक्सी शामिल हैं,
और हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो
नतीजे: Linux के मुकाबले Windows पर प्रॉक्सी की लागत लगभग सात गुना ज़्यादा है, और
डेमन फ़िलहाल एक कोर का लगभग 12% सस्टेन करता है, जो हमारे अपने 5-10%
बजट से ऊपर है। रॉ JSON, तरीका, और जो अभी भी अनमापा है, वह
[docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## प्राइसिंग

| प्लान | यह क्या कवर करता है | कीमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताए गए हर अन्य रनटाइम, फ़्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | Starter + नियंत्रण और मूल्यांकन: अप्रूवल्स, टूल-रिस्क पॉलिसीज़, evals, विसंगति पहचान, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट, टैम्पर-एविडेंट ऑडिट लॉग | $19 प्रति नोड / महीना |

वार्षिक प्लान, Enterprise और मौजूदा नंबर
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** पर हैं। सेल्फ़-होस्टेड लाइसेंस
कुंजियां क्लाउड के बिना काम करती हैं (`clawmetry license`)। सटीक फ्री/पेड विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग पढ़ता है। **जब तक आप `clawmetry connect` न चलाएं,
आपके बॉक्स से कोई सेशन डेटा बाहर नहीं जाता** — कोई प्रॉम्प्ट, रिप्लाई, टूल आर्ग्युमेंट, फ़ाइल
कंटेंट या लॉग लाइन नहीं। जब आप कनेक्ट करते हैं, तो स्नैपशॉट एक ऐसी की के साथ
एंड-टू-एंड एन्क्रिप्टेड होता है जो कभी आपकी मशीन नहीं छोड़ती, और आपके ब्राउज़र में डिक्रिप्ट
होती है। अगर किसी नोड के पास कोई की नहीं है, तो अपलोड को क्लियर में भेजने के बजाय
छोड़ दिया जाता है, और कोई सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

कनेक्ट करने से पहले डिफ़ॉल्ट रूप से दो चीज़ें ज़रूर चलती हैं, दोनों ऑप्ट-आउट करने योग्य हैं और
दोनों में कोई सेशन डेटा नहीं होता: एक अनाम इंस्टॉल पिंग और PyPI के खिलाफ़ एक
वर्ज़न चेक। डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए एक बार आपका पब्लिक IP भी
लुक अप करता है। हर गंतव्य, वह क्या ले जाता है और उसे कैसे बंद करें, यह
[docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है; सेल्फ़-होस्टेड, रीपॉइंटेड और एयर-गैप्ड इंस्टॉल्स
कोई भी विवेकाधीन (discretionary) आउटबाउंड कॉल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में, हमारे परोसे गए कोड में होता है। यह पहले एक
वादा हुआ करता था; अब यह कुछ ऐसा है जिसे आप जांच सकते हैं। आपकी की को छूने वाली हर लाइन
एक पठनीय फ़ाइल में रहती है, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
जो wheel के अंदर शिप होती है और शब्दशः परोसी जाती है, जो Subresource
Integrity हैश से पिन की गई है। यह पुष्टि करने के लिए कि ब्राउज़र वही चलाता है जो हमने
प्रकाशित किया:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह क्या साबित नहीं करता: हम वह पेज परोसते हैं जो फ़ाइल को लोड करता है, इसलिए हम
एक अलग पेज परोस सकते थे। इंटेग्रिटी हैश आपको एक समझौता किए गए CDN से बचाते हैं,
वेंडर से नहीं। आपको जो मिलता है वह यह है कि किसी भी बदलाव का जानबूझकर होना,
पेज सोर्स में दिखना, और PyPI पर मौजूद किसी आर्टिफ़ैक्ट से अलग होना ज़रूरी है जिसे कोई
भी फ़ेच कर सकता है। सेल्फ़-होस्टिंग या केवल-लोकल रहना इस निर्भरता को पूरी तरह
हटा देता है।

## इंस्टॉल

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक
एजेंट रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

या एजेंट को आपके लिए इसे सेट अप करने दें। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot या OpenCode को सिखाती है कि
ClawMetry कैसे इंस्टॉल करें, मशीन पर एजेंट क्या कर रहे हैं और क्या खर्च कर रहे हैं इसकी
रिपोर्ट कैसे दें, अनुरोध पर एक सेशन कैसे रोकें, और अप्रूवल के लिए जोखिम भरी टूल
कॉल्स को कैसे रोकें:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तावेज़ (Docs)

| | |
|---|---|
| [रनटाइम संगतता](docs/compatibility.md) | हर एडेप्टर क्या पढ़ता है, और एक रनटाइम कैसे जोड़ें |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोवाइडर विंडो, कॉम्पैक्शन बनाम ओवरफ़्लो, प्रति-रनटाइम कवरेज |
| [ओवरहेड](docs/OVERHEAD.md) | इंस्ट्रूमेंटेशन की मापी गई लागत, इसे दोहराने के हार्नेस के साथ |
| [एंटाइटलमेंट्स](docs/ENTITLEMENTS.md) | फ्री बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [अप्रूवल्स और पॉलिसीज़](docs/APPROVALS.md) | प्री-एग्ज़िक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [अपना खुद का एजेंट लाएं](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सिरे से सिरे तक, चलाने योग्य उदाहरणों के साथ |
| [SDK ट्रैकिंग](docs/SDK_TRACKING.md) | आपके खुद बनाए एजेंट्स के लिए कॉस्ट एट्रिब्यूशन |
| [चैट चैनल्स](docs/CHANNELS.md) | फ़्लो में दिखाए गए चैट एडेप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेवलपमेंट](docs/DEVELOPMENT.md) | यह अंदर से कैसे काम करता है; सोर्स से चलाना |
| [टेलीमेट्री](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग्स, और इन्हें कैसे बंद करें |

## स्क्रीनशॉट्स

नीचे दिया हर नंबर एक असली मशीन से है, केवल-पढ़ने के लिए (read-only), बिना कुछ बोया हुआ।

**यह आपको बताता है कि कब कुछ गलत है, सिर्फ़ यह नहीं कि क्या हुआ।**
शीर्ष पर दो विसंगति बैनर: खर्च दैनिक औसत का 7x चल रहा है, और एक
4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 सेशंस में से 324 में एक वेस्ट
सिग्नल है, कारण के अनुसार सूचीबद्ध।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहां गया, हर विंडो में।**
आज $252.47, इस हफ़्ते $513.15, इस महीने $1,312.92, हर एक के पीछे
मौजूद टोकंस और आपकी सब्सक्रिप्शन पहले से कितना कवर करती है, इसके साथ। उसके नीचे,
लगभग $1,128/माह को रिकवर करने योग्य के रूप में सूचीबद्ध किया गया और cache
पुनः उपयोग से पहले ही बचाए गए $17,256/माह।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि एक संदेश कैसे जवाब बनता है।**
लाइव फ़्लो डायग्राम: आप, वह चैनल जिस पर यह आया, गेटवे, अभी जवाब दे रहा
मॉडल, और हर टूल जिसका उसने इस्तेमाल किया। जैसे-जैसे काम उनके ज़रिए बढ़ता है, नोड्स
रोशन होते जाते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर हर एजेंट, एक ही टेबल में।**
यह क्या चलाता है, पिछले 24 घंटों में और अपने पूरे जीवनकाल में इसकी लागत क्या है, आख़िरी बार
कब देखा गया, इसका मालिक कौन है, और क्या कोई सब्सक्रिप्शन बिल को कवर कर रही है। यहां
14 एजेंट, 3 सेशंस काम कर रहे हैं, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि एक टर्न का समय और पैसा कहां गया, टूल-दर-टूल।**
एक असली सेशन का एक टर्न: $1.16 में 11.2 मिनट में 11 टूल्स। हर Bash
कॉल और मॉडल कॉल को टाइमलाइन पर अपना बार मिलता है, ताकि 4.1 मिनट तक चलने वाली
कमांड और 226ms चलने वाली कमांड को एक नज़र में अलग बताया जा सके।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को आंकता है, सिर्फ़ खर्च को नहीं।**
इस हफ़्ते एक A: 54 टास्क साफ़-सुथरे वापस आए, 2 रफ़ (खराब) टास्क की कीमत $48.57 रही,
और जिन रन्स में आंकने लायक बहुत कम गतिविधि थी उन्हें जीत के तौर पर गिनने के बजाय
ग्रेड से बाहर रखा गया। हर रफ़ रन अपने ट्रेस से लिंक होता है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो क्यों भरती जा रही है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% पीक, 4 कॉम्पैक्शन
जो सभी ओवरफ़्लो पर नहीं बल्कि प्रोएक्टिव रूप से हुए, और उसके पीछे हर टर्न की
यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**आपके कुछ भी कॉन्फ़िगर किए बिना डिटेक्शन चलता है।**
इंस्टॉल से ही बिल्ट-इन डिटेक्टर्स चालू हैं: एजेंट शांत हो गया, टेलीमेट्री फ़ीड
रुक गई, कॉस्ट स्पाइक, टोकन बर्स्ट, बढ़ती एरर्स, एरर स्पाइक, बजट
थ्रेशहोल्ड, थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फाइंडिंग, सिक्योरिटी पोस्चर
बदला। आपके अपने नियम इसके ऊपर वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को रोकना ऑप्ट-इन है, और डिफ़ॉल्ट रूप से बंद शिप होता है।**
रिकर्सिव डिलीट्स, फ़ोर्स पुश, sudo, सीक्रेट्स, पैकेज इंस्टॉल्स और आउटबाउंड
कॉल्स — हर एक के लिए एक नियम है जिसे आप चालू कर सकते हैं। जब तक आप ऐसा नहीं करते,
ClawMetry बस देखता है और कुछ नहीं बदलता। एक बार चालू हो जाने पर, मैच होने वाली
कॉल्स यहां (या आपके फ़ोन पर) अप्रूव या डिनाई के लिए इंतज़ार करती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रति रनटाइम: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## पहचान (Recognition)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star इतिहास

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लाइसेंस

MIT · बनाया [@vivekchand](https://github.com/vivekchand) द्वारा · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
