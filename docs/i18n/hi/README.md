<!-- i18n-src:61beb8393e2f -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**कोई एजेंट सौ टूल कॉल कर सकता है और फिर भी कोई प्रगति नहीं हो सकती।** ClawMetry
आपके कोडिंग एजेंट्स द्वारा पहले से लिखी गई सेशन फ़ाइलों को पढ़ता है, और टाइमलाइन,
टूल कॉल्स, और रनटाइम जो भी टोकन और लागत डेटा उजागर करता है, उसे एक ही
व्यू में डाल देता है — जिससे आप बता सकते हैं कि कोई लंबा रन काम कर रहा है या अटक गया है।

**30 AI एजेंट रनटाइम्स** के साथ काम करता है — Claude Code, OpenAI Codex, Hermes, OpenClaw और 26 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक ही डैशबोर्ड। ([पूरी सूची](SUPPORTED_RUNTIMES.txt), कैटलॉग से जनरेट की गई।)

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िग। सब कुछ ऑटो-डिटेक्ट होता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। ज़ीरो कॉन्फ़िग: यह उन एजेंट रनटाइम्स को ढूंढ लेता है जो
आपके पास पहले से हैं, उन्हें रीड-ओनली तरीके से पढ़ता है, और वे कैसे चलते हैं इसमें कुछ नहीं बदलता।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इंस्टॉल करने से पहले

| | |
|---|---|
| **यह क्या करता है** | आपके एजेंट्स द्वारा पहले से लिखी गई सेशन फ़ाइलों और लॉग्स को पढ़ता है। कोई SDK नहीं, कोड में कोई बदलाव नहीं, आपके ऐप में कोई इंस्ट्रुमेंटेशन नहीं। |
| **आप क्या देखते हैं** | सेशन टाइमलाइन, टूल-बाय-टूल रीप्ले, टोकन और लागत का ब्रेकडाउन, और ट्रैजेक्टरी सिग्नल (लूपिंग, दोहराई गई विफलताएं) — प्रत्येक रनटाइम के लिए। |
| **फ्री में क्या मिलता है** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw और Goose** को किसी अकाउंट, की या नेटवर्क कॉल के बिना पढ़ता है। बाकी 27 — Claude Code, Codex, Cursor और बाकी — को क्लोज़्ड-सोर्स `clawmetry-pro` कंपेनियन द्वारा पढ़ा जाता है, जो 7-दिन के ट्रायल या किसी प्लान के साथ आता है — सटीक विभाजन के लिए [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) देखें। |
| **कैसे शुरू करें** | `pip install clawmetry && clawmetry`, फिर localhost:8900 खोलें। इस मशीन पर अभी कोई एजेंट नहीं है? `clawmetry --sample` तीन लेबल किए गए सिंथेटिक सेशन के साथ खुलता है। |
| **आपकी मशीन से क्या बाहर जाता है** | कोई सेशन डेटा नहीं, जब तक आप `clawmetry connect` नहीं चलाते। डिफ़ॉल्ट रूप से दो चीज़ें ही चलती हैं, दोनों ऑप्ट-आउट हैं और किसी में सेशन कंटेंट नहीं होता: एक अनाम इंस्टॉल पिंग और एक PyPI वर्शन चेक। हर डेस्टिनेशन [docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है, जो कमेंट्स पढ़ने के बजाय एक वायर कैप्चर से बनाया गया है। |

फैसला करने से पहले जानने लायक दो सीमाएं: रनटाइम्स बहुत अलग-अलग डेटा उजागर करते हैं
(कुछ बिल्कुल भी लागत प्रकाशित नहीं करते — [मैट्रिक्स](docs/compatibility.md)
बताता है कि प्रत्येक रनटाइम के लिए क्या है), और किसी एक्शन को देख पाना उसे
रोक पाने के बराबर नहीं है ([कौन-से कंट्रोल असली हैं, प्रत्येक रनटाइम के लिए](docs/APPROVALS.md))।


## 30 एजेंट रनटाइम्स के साथ काम करता है

**ओपन सोर्स ऐप में फ्री:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को एक ही डैशबोर्ड मिलता है। कई एक साथ चलाएं और हेडर
स्विचर हर टैब को उनमें से किसी एक के लिए फिर से स्कोप कर देता है।

किसी SDK पर अपना खुद का एजेंट बनाया है? इंटरसेप्टर उसकी LLM कॉल्स को भी
ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न-दर-टर्न, रीप्ले के साथ
- **लागत और टोकन**: प्रत्येक रनटाइम, मॉडल, सेशन और दिन के अनुसार, एनोमली फ़्लैग्स के साथ
- **फ़्लो**: चैनलों, मॉडलों और टूल्स के बीच चल रहे मैसेजों का लाइव डायग्राम
- **ब्रेन**: रीज़निंग और टूल-कॉल इवेंट स्ट्रीम, जैसे-जैसे यह होता है
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोवाइडर के अनुसार साइज़ की गई विंडो यूटिलाइज़ेशन, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, और हम क्या *नहीं* देख पाते इसका प्रति-रनटाइम मैप ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जो हर रनटाइम ने वास्तव में लोड की
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर रेट्स, रेट लिमिट्स, लाइव लॉग स्ट्रीम
- **अलर्ट्स**: बजट कैप, एरर स्पाइक्स, एजेंट-ऑफ़लाइन, Slack, Discord, PagerDuty, Telegram, Email पर रूट किए गए
- **अप्रूवल्स**: जोखिम भरे टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और मॉनिटरिंग की लागत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले जानने लायक दो सवाल हैं।

**यह रनटाइम्स के बीच कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे संभालता है?**

यूटिलाइज़ेशन प्रतिशत तभी सही होता है जब वह किस चीज़ से भाग दे रहा है वह सही हो।
ClawMetry हर प्रोवाइडर के लिए विंडो का साइज़ [एक टेबल](clawmetry/context_windows.py)
से तय करता है जिसे आप पढ़ सकते हैं और PR कर सकते हैं, जो Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama और GLM को कवर करती है। यह सभी 30
रनटाइम्स को एक ही वेंडर की माप-पट्टी से नहीं मापता। यह मायने रखता है: एक 300K GPT-5
टर्न को Anthropic की 200K के हिसाब से मापने पर वह ">100%, blown" दिखता है जबकि
वास्तव में वह GPT-5 की 400K का 75% है। वही माप-पट्टी वास्तव में ओवरफ़्लो हुए
130K DeepSeek टर्न को एक आरामदायक 65% के रूप में छिपा देती है।

हर विंडो अपनी उत्पत्ति के साथ आती है: `model_table`, `explicit_marker`,
`observed_floor`, या जब मॉडल पता नहीं होता तो एक ईमानदार `default`। अंदाज़े पर
बना गेज कभी उतने ही भरोसे के साथ नहीं दिखाया जाता जितना किसी लुकअप पर बना गेज।

ClawMetry कुछ रनटाइम्स पर ही कॉम्पैक्शन इवेंट्स देख सकता है। इसलिए
`GET /api/context-coverage` प्रत्येक रनटाइम के लिए रिपोर्ट करता है कि क्या
कोई **ज़ीरो का मतलब "साफ़ चला" है या "हम अंधे हैं"**। जो `0` वास्तव में अंधा
होने का मतलब रखता है वह ऐसा कहता है। [पूरी जानकारी](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रुमेंटेशन की लागत क्या है?**

| पाथ | आपके एजेंट में जोड़ा गया | डिफ़ॉल्ट? |
|---|---|---|
| सेशन-फ़ाइल टेलिंग (सभी 30 रनटाइम्स) | **0**. अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | ऑन |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉल पर **+0.44 ms**, या 5s कॉल का 0.009% | ऑफ़ |
| प्री-टूल हुक गेट (वॉर्म कैश) | प्रत्येक गेटेड टूल कॉल पर **+44 ms**, 36 ms इंटरप्रेटर फ़्लोर के ऊपर | ऑफ़ |
| एनफ़ोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉल पर **+9.7 ms** | ऑफ़ |

डेमन होस्ट लागत: **2,762 इवेंट्स/सेकंड** इनजेस्ट, **710 बाइट्स/इवेंट** डिस्क पर
(1 लाख इवेंट्स प्रति 67.7 MB), और व्यस्त इंस्टॉल पर सस्टेन्ड **एक कोर का ~12%**।
वह आखिरी नंबर हमारे बताए गए 5-10% बजट से ज़्यादा है, इसलिए इसे पेज से हटाने के
बजाय पीछा किए जाने वाली बग के रूप में प्रकाशित किया गया है।

Apple M2 Pro पर `benchmarks/overhead.py` से मापा गया। हार्नेस हर स्थिति को
अलग प्रोसेस में चलाता है, उनका क्रम बदलता है, और **जब राउंड्स नंबर के साइन पर
सहमत नहीं होते तो कोई नंबर प्रिंट करने से इनकार करता है**। इसे अपनी ही मशीन
पर एक मिनट में चलाएं:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पाथ मापा गया है, जिसमें हुक गेट्स और एनफ़ोर्समेंट प्रॉक्सी शामिल हैं,
और हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो नतीजे:
प्रॉक्सी की लागत Windows पर Linux की तुलना में लगभग सात गुना ज़्यादा है, और
डेमन अभी हमारे अपने 5-10% बजट से ज़्यादा, एक कोर का लगभग 12% सस्टेन करता है।
रॉ JSON, तरीका, और अभी भी जो नहीं मापा गया है वह
[docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## कीमत

| प्लान | यह क्या कवर करता है | कीमत |
|---|---|---|
| **फ्री** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **स्टार्टर** | ऊपर दिए गए हर दूसरे रनटाइम, फ़्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / माह |
| **Pro** | स्टार्टर + कंट्रोल और इवैल्युएशन: अप्रूवल्स, टूल-रिस्क पॉलिसीज़, इवैल्स, एनोमली डिटेक्शन, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट, टैम्पर-एविडेंट ऑडिट लॉग | $19 प्रति नोड / माह |

एन्युअल प्लान, एंटरप्राइज़ और मौजूदा नंबर
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** पर हैं। सेल्फ़-होस्टेड लाइसेंस
कीज़ क्लाउड के बिना काम करती हैं (`clawmetry license`)। फ्री/पेड का सटीक विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलों और लॉग्स को पढ़ता है। **जब तक आप `clawmetry connect`
नहीं चलाते, तब तक आपके बॉक्स से कोई सेशन डेटा बाहर नहीं जाता** — कोई प्रॉम्प्ट,
जवाब, टूल आर्ग्युमेंट्स, फ़ाइल कंटेंट या लॉग लाइन नहीं। जब आप कनेक्ट करते हैं,
तो स्नैपशॉट एक ऐसी की के साथ एंड-टू-एंड एन्क्रिप्टेड होता है जो कभी आपकी मशीन
नहीं छोड़ती, और आपके ब्राउज़र में डिक्रिप्ट होता है। यदि किसी नोड के पास की नहीं है,
तो अपलोड को साफ़ भेजने के बजाय स्किप कर दिया जाता है, और कोई सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

कनेक्ट करने से पहले डिफ़ॉल्ट रूप से दो चीज़ें ही चलती हैं, दोनों ऑप्ट-आउट हैं और
किसी में सेशन डेटा नहीं होता: एक अनाम इंस्टॉल पिंग और PyPI के मुकाबले एक वर्शन
चेक। डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए एक बार आपका पब्लिक IP भी देखता है।
हर डेस्टिनेशन, वह क्या ले जाता है और उसे कैसे बंद करें, यह
[docs/EGRESS.md](docs/EGRESS.md) में सूचीबद्ध है; सेल्फ़-होस्टेड, रीपॉइंटेड और
एयर-गैप्ड इंस्टॉल्स कोई भी विवेकाधीन आउटबाउंड कॉल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में होता है, उस कोड में जो हम आपको देते हैं। यह पहले एक
वादा था; अब यह कुछ ऐसा है जिसे आप जांच सकते हैं। हर लाइन जो आपकी की को छूती है
एक पढ़ने योग्य फ़ाइल, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
में रहती है, जो व्हील के अंदर शिप होती है और शब्दशः सर्व होती है, एक Subresource
Integrity हैश के साथ पिन की गई। यह पुष्टि करने के लिए कि ब्राउज़र वही चलाता है
जो हमने प्रकाशित किया है:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह जो साबित नहीं करता: हम वह पेज सर्व करते हैं जो फ़ाइल को लोड करता है,
इसलिए हम अलग पेज सर्व कर सकते हैं। इंटीग्रिटी हैश आपको एक कॉम्प्रोमाइज़्ड CDN से
बचाते हैं, वेंडर से नहीं। आपको जो फ़ायदा मिलता है वह यह है कि कोई भी बदलाव
जानबूझकर, पेज सोर्स में दिखने वाला, और PyPI पर मौजूद किसी आर्टिफ़ैक्ट से अलग
होना चाहिए, जिसे कोई भी फ़ेच कर सकता है। सेल्फ़-होस्टिंग या केवल-लोकल रहने से
यह निर्भरता पूरी तरह खत्म हो जाती है।

## इंस्टॉल

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट
रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

या एजेंट को यह आपके लिए सेट अप करने दें। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot या OpenCode को
ClawMetry इंस्टॉल करना, मशीन पर मौजूद एजेंट्स क्या कर रहे हैं और क्या खर्च कर रहे हैं
यह रिपोर्ट करना, रिक्वेस्ट पर एक सेशन रोकना, और जोखिम भरे टूल कॉल्स को
अप्रूवल के लिए रोक कर रखना सिखाती है:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तावेज़

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | प्रत्येक एडाप्टर क्या पढ़ता है, और रनटाइम कैसे जोड़ें |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोवाइडर विंडोज़, कॉम्पैक्शन बनाम ओवरफ़्लो, प्रति-रनटाइम कवरेज |
| [Overhead](docs/OVERHEAD.md) | इंस्ट्रुमेंटेशन की लागत क्या है, मापी गई, इसे दोहराने वाले हार्नेस के साथ |
| [Entitlements](docs/ENTITLEMENTS.md) | फ्री बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एग्ज़ीक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain एंड टू एंड, चलाने योग्य उदाहरणों के साथ |
| [SDK tracking](docs/SDK_TRACKING.md) | आपके द्वारा खुद बनाए गए एजेंट्स के लिए लागत आरोपण |
| [Chat channels](docs/CHANNELS.md) | Flow में दिखाए गए चैट एडाप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट्स |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | यह अंदर से कैसे काम करता है; सोर्स से चलाना |
| [Telemetry](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग्स, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट्स

नीचे दिया हर नंबर एक असली मशीन से है, रीड-ओनली, बिना कुछ भी सीड किए।

**यह आपको बताता है कि कब कुछ गलत है, न कि सिर्फ़ क्या हुआ।**
शीर्ष पर दो एनोमली बैनर: औसत दैनिक खर्च से 7x ज़्यादा चल रहा खर्च, और एक
4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 सेशनों में से 324 में एक वेस्ट
सिग्नल है, कारण के अनुसार सूचीबद्ध।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहां गया, हर विंडो में।**
आज $252.47, इस सप्ताह $513.15, इस महीने $1,312.92, हर एक के पीछे के टोकन
और आपकी सब्सक्रिप्शन उसमें से कितना कवर करती है, इसके साथ। उसके नीचे,
लगभग $1,128/माह रिकवरेबल के रूप में सूचीबद्ध और कैश रीयूज़ से पहले ही बचाए
गए $17,256/माह।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि कोई मैसेज कैसे जवाब बनता है।**
लाइव फ़्लो डायग्राम: आप, वह चैनल जिससे यह आया, गेटवे, अभी जवाब दे रहा मॉडल,
और वह हर टूल जिसे उसने इस्तेमाल किया। जैसे-जैसे काम उनसे होकर गुज़रता है,
नोड्स रोशन होते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर मौजूद हर एजेंट, एक ही टेबल में।**
यह क्या चलाता है, पिछले 24 घंटों में और अपने पूरे जीवनकाल में इसकी लागत क्या है,
इसे आखिरी बार कब देखा गया, इसका मालिक कौन है, और क्या कोई सब्सक्रिप्शन इसका
बिल कवर कर रही है। यहां 14 एजेंट, 3 सेशन काम कर रहे, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि किसी टर्न का समय और पैसा कहां गया, टूल दर टूल।**
एक असली सेशन का एक टर्न: 11.2 मिनट में 11 टूल्स, $1.16 में। हर Bash कॉल
और मॉडल कॉल को टाइमलाइन पर अपना बार मिलता है, ताकि जो कमांड 4.1 मिनट तक चली
और जो 226ms तक चली, उनमें एक नज़र में फ़र्क़ किया जा सके।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को ग्रेड करता है, न कि सिर्फ़ खर्च को।**
इस सप्ताह एक A: 54 टास्क साफ़ वापस आए, 2 खराब वालों की लागत $48.57 रही,
और जिन रन्स में जज करने के लिए बहुत कम एक्टिविटी थी, उन्हें जीत के रूप में
गिनने के बजाय ग्रेड से बाहर रखा गया। हर खराब रन अपने ट्रेस से लिंक होता है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो क्यों भरती जा रही है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% पीक, 4 कॉम्पैक्शन जो सभी
ओवरफ़्लो पर होने के बजाय प्रोएक्टिवली फ़ायर हुए, और उसके पीछे हर टर्न का
यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**डिटेक्शन आपके कुछ भी कॉन्फ़िगर किए बिना चलता है।**
बिल्ट-इन डिटेक्टर्स इंस्टॉल से ही ऑन होते हैं: एजेंट शांत हो गया, टेलीमेट्री फ़ीड
बंद हो गई, कॉस्ट स्पाइक, टोकन बर्स्ट, बढ़ती एरर्स, एरर स्पाइक, बजट थ्रेशोल्ड,
थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फ़ाइंडिंग, सिक्योरिटी पोज़्चर बदला। आपके
अपने नियम ऊपर से वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को रोकना ऑप्ट-इन है, और डिफ़ॉल्ट रूप से बंद शिप होता है।**
रिकर्सिव डिलीट्स, फ़ोर्स पुश, sudo, सीक्रेट्स, पैकेज इंस्टॉल्स और आउटबाउंड
कॉल्स — हर एक के लिए आप एक नियम ऑन कर सकते हैं। जब तक आप ऐसा नहीं करते,
ClawMetry सिर्फ़ देखता है और कुछ नहीं बदलता। एक बार कोई नियम ऑन होने पर,
मैचिंग कॉल्स यहां (या आपके फ़ोन पर) अप्रूव या डिनाई के लिए रुकी रहती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

और भी, प्रति रनटाइम: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## पहचान

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## स्टार हिस्ट्री

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
