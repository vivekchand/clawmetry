<!-- i18n-src:a855a14295b0 -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**एक एजेंट बिना कोई प्रगति किए सैकड़ों टूल कॉल कर सकता है।** ClawMetry
उन सेशन फाइलों को पढ़ता है जो आपके कोडिंग एजेंट पहले से ही लिखते हैं, और टाइमलाइन,
टूल कॉल्स और रनटाइम जो भी टोकन और कॉस्ट डेटा उजागर करता है उसे एक ही
व्यू में डाल देता है — ताकि आप बता सकें कि कौन सा लंबा रन काम कर रहा है और कौन सा अटका हुआ है।

**32 AI एजेंट रनटाइम** के साथ काम करता है — Claude Code, OpenAI Codex, Hermes, OpenClaw और 28 अन्य। आपके पूरे एजेंट फ्लीट के लिए एक डैशबोर्ड। ([पूरी सूची](SUPPORTED_RUNTIMES.txt), कैटलॉग से जनरेट की गई।)

> 🌐 **इसे इनमें पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िग। सब कुछ ऑटो-डिटेक्ट करता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। ज़ीरो कॉन्फ़िग: यह उन एजेंट रनटाइम को ढूंढ लेता है
जो आपके पास पहले से हैं, उन्हें रीड-ओनली तरीके से पढ़ता है, और यह नहीं बदलता कि वे कैसे चलते हैं।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## इंस्टॉल करने से पहले

| | |
|---|---|
| **यह क्या करता है** | उन सेशन फाइलों और लॉग्स को पढ़ता है जो आपके एजेंट पहले से लिखते हैं। कोई SDK नहीं, कोई कोड बदलाव नहीं, आपके ऐप में कोई इंस्ट्रुमेंटेशन नहीं। |
| **आप क्या देखते हैं** | सेशन टाइमलाइन, टूल-दर-टूल रीप्ले, टोकन और कॉस्ट का ब्रेकडाउन, और ट्रैजेक्टरी सिग्नल (लूपिंग, बार-बार होने वाली विफलताएँ) — प्रत्येक रनटाइम के लिए। |
| **क्या मुफ़्त है** | `pip install clawmetry` बिना किसी अकाउंट, बिना किसी की और बिना किसी नेटवर्क कॉल के **OpenClaw, NVIDIA NemoClaw और Goose** को पढ़ता है। बाकी 27 — Claude Code, Codex, Cursor और बाकी — को क्लोज़्ड-सोर्स `clawmetry-pro` कंपैनियन द्वारा पढ़ा जाता है, जो 7-दिन के ट्रायल या किसी प्लान के साथ मिलता है — सटीक विभाजन के लिए [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) देखें। |
| **कैसे शुरू करें** | `pip install clawmetry && clawmetry`, फिर localhost:8900 खोलें। इस मशीन पर अभी तक कोई एजेंट नहीं? `clawmetry --sample` तीन लेबल्ड सिंथेटिक सेशन के साथ खुलता है। |
| **आपकी मशीन से क्या बाहर जाता है** | कोई सेशन डेटा नहीं, जब तक आप `clawmetry connect` नहीं चलाते। डिफ़ॉल्ट रूप से दो चीज़ें चलती हैं, दोनों ऑप्ट-आउट करने योग्य और दोनों में कोई सेशन कंटेंट नहीं होता: एक एनोनिमस इंस्टॉल पिंग और एक PyPI वर्ज़न चेक। हर डेस्टिनेशन की सूची [docs/EGRESS.md](docs/EGRESS.md) में है, जो कमेंट्स पढ़ने के बजाय वायर कैप्चर से दोबारा बनाई गई है। |

आउटपुट को आँकने से पहले जानने लायक दो सीमाएँ: रनटाइम बहुत अलग-अलग डेटा
उजागर करते हैं (कुछ कोई कॉस्ट प्रकाशित ही नहीं करते — [मैट्रिक्स](docs/compatibility.md)
बताता है कि कौन सा, प्रत्येक रनटाइम के लिए), और किसी क्रिया को देखने का मतलब यह नहीं
कि आप उसे रोक सकते हैं ([कौन से कंट्रोल असली हैं, प्रत्येक रनटाइम के लिए](docs/APPROVALS.md))।


## 32 एजेंट रनटाइम के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को एक ही डैशबोर्ड मिलता है। एक साथ कई चलाएँ और हेडर
स्विचर हर टैब को उनमें से किसी एक पर दोबारा स्कोप कर देता है।

किसी SDK पर अपना खुद का एजेंट बनाया है? इंटरसेप्टर उसकी LLM कॉल्स भी
ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न-दर-टर्न, रीप्ले के साथ
- **कॉस्ट और टोकन**: प्रत्येक रनटाइम, मॉडल, सेशन और दिन के हिसाब से, एनोमली फ्लैग्स के साथ
- **फ़्लो**: चैनल, मॉडल और टूल्स से गुज़रते हुए मैसेज का लाइव डायग्राम
- **ब्रेन**: रीज़निंग और टूल-कॉल इवेंट स्ट्रीम जैसे-जैसे यह होता है
- **कॉन्टेक्स्ट ब्लोआउट**: प्रोवाइडर के अनुसार साइज़ की गई विंडो यूटिलाइज़ेशन, कॉम्पैक्शन बनाम फ़ोर्स्ड ओवरफ़्लो, साथ ही हम *क्या नहीं* देख सकते इसका प्रति-रनटाइम मैप ([कैसे](docs/CONTEXT_BLOWOUT.md))
- **मेमोरी और स्किल्स**: वे फाइलें और स्किल्स जो हर रनटाइम ने वास्तव में लोड कीं
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर रेट, रेट लिमिट, लाइव लॉग स्ट्रीम
- **अलर्ट**: बजट कैप, एरर स्पाइक्स, एजेंट-ऑफ़लाइन, जो Slack, Discord, PagerDuty, Telegram, Email पर रूट किए जाते हैं
- **अप्रूवल्स**: जोखिम भरी टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, और मॉनिटरिंग की लागत

किसी भी एजेंट-तुलना टूल पर भरोसा करने से पहले जानने लायक दो सवाल।

**यह रनटाइम्स में कॉन्टेक्स्ट-विंडो ब्लोआउट को कैसे संभालता है?**

एक यूटिलाइज़ेशन प्रतिशत उतना ही ईमानदार है जितना वह जिस चीज़ से भाग देता है। ClawMetry
विंडो का साइज़ प्रोवाइडर के अनुसार, [एक टेबल](clawmetry/context_windows.py) से तय करता है
जिसे आप पढ़ और PR कर सकते हैं, जिसमें Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama और GLM शामिल हैं। यह सभी 32
रनटाइम्स को एक ही वेंडर के पैमाने से नहीं मापता। यह मायने रखता है: एक 300K GPT-5
टर्न को Anthropic के 200K के मुक़ाबले नापने पर ">100%, blown" दिखता है जबकि
असल में यह GPT-5 के 400K का सिर्फ़ 75% है। वही पैमाना एक असल में ओवरफ़्लो हो चुके
130K DeepSeek टर्न को एक आरामदायक 65% के रूप में छुपा देता है।

हर विंडो अपनी प्रोवेनेंस के साथ आती है: `model_table`, `explicit_marker`,
`observed_floor`, या जब हमें मॉडल नहीं पता होता तो एक ईमानदार `default`। अनुमान पर बना
एक गेज कभी भी लुकअप पर बने गेज जितने भरोसे के साथ नहीं दिखता।

ClawMetry कुछ रनटाइम्स पर ही कॉम्पैक्शन इवेंट देख सकता है। इसलिए
`GET /api/context-coverage` हर रनटाइम के लिए रिपोर्ट करता है कि **ज़ीरो का मतलब
"साफ़ चला" है या "हम अंधे हैं"**। एक `0` जिसका असल में मतलब अंधा होना है, वह यह बता देता है।
[पूरी जानकारी](docs/CONTEXT_BLOWOUT.md)

**इंस्ट्रुमेंटेशन की क्या लागत है?**

| पाथ | आपके एजेंट में जोड़ा गया | डिफ़ॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सभी 32 रनटाइम्स) | **0**। अलग प्रोसेस, आपके एजेंट में कोई ClawMetry कोड नहीं | ऑन |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रति LLM कॉल **+0.44 ms**, यानी 5s कॉल का 0.009% | ऑफ़ |
| प्री-टूल हुक गेट (वार्म कैश) | प्रति गेटेड टूल कॉल **+44 ms**, 36 ms इंटरप्रेटर फ़्लोर के ऊपर | ऑफ़ |
| एनफ़ोर्समेंट प्रॉक्सी | प्रति LLM कॉल **+9.7 ms** | ऑफ़ |

डीमन होस्ट लागत: **2,762 इवेंट्स/सेकंड** इनजेस्ट, डिस्क पर **710 बाइट्स/इवेंट**
(100k इवेंट्स के लिए 67.7 MB), और एक व्यस्त इंस्टॉल पर सस्टेन्ड **~12% एक कोर का**।
वह आख़िरी आँकड़ा हमारे बताए गए 5-10% बजट से ऊपर है, इसलिए इसे पन्ने से
हटाने के बजाय एक बग के रूप में प्रकाशित किया गया है जिसका पीछा करना है।

Apple M2 Pro पर `benchmarks/overhead.py` से मापा गया। हार्नेस हर
कंडीशन को अलग प्रोसेस में चलाता है, उनका क्रम बदलता है, और **जब राउंड्स
उसके साइन पर असहमत होते हैं तो नंबर छापने से मना कर देता है**। इसे अपनी
मशीन पर एक मिनट में चलाएँ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हर पाथ मापा जाता है, जिसमें हुक गेट्स और एनफ़ोर्समेंट प्रॉक्सी शामिल हैं,
और हार्नेस CI में Linux, macOS और Windows पर चलता है। जानने लायक दो नतीजे:
प्रॉक्सी की लागत Windows पर Linux के मुक़ाबले लगभग सात गुना ज़्यादा है, और
डीमन फ़िलहाल एक कोर का लगभग 12% सस्टेन करता है, जो हमारे अपने 5-10% बजट
से ऊपर है। रॉ JSON, तरीक़ा, और जो अभी तक नहीं मापा गया है वह
[docs/OVERHEAD.md](docs/OVERHEAD.md) में है।

## प्राइसिंग

| प्लान | यह क्या कवर करता है | कीमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताए गए हर दूसरे रनटाइम, फ्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | Starter + कंट्रोल और मूल्यांकन: अप्रूवल्स, टूल-रिस्क पॉलिसी, इवैल्स, एनोमली डिटेक्शन, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट, टैम्पर-एविडेंट ऑडिट लॉग | $19 प्रति नोड / महीना |

वार्षिक प्लान, Enterprise और मौजूदा आँकड़े यहाँ मौजूद हैं
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**। सेल्फ़-होस्टेड लाइसेंस
की क्लाउड के बिना काम करती हैं (`clawmetry license`)। मुफ़्त/पेड का सटीक विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फाइलें और लॉग पढ़ता है। **जब तक आप `clawmetry connect` नहीं चलाते,
आपके बॉक्स से कोई सेशन डेटा बाहर नहीं जाता** — कोई प्रॉम्प्ट, जवाब, टूल आर्ग्युमेंट, फाइल
कंटेंट या लॉग लाइन नहीं। जब आप कनेक्ट करते हैं, तो स्नैपशॉट एक ऐसी की के साथ
एंड-टू-एंड एन्क्रिप्टेड होता है जो कभी आपकी मशीन नहीं छोड़ती, और आपके ब्राउज़र में डिक्रिप्ट
होती है। अगर किसी नोड के पास की नहीं है, तो अपलोड को क्लियर में भेजने के बजाय स्किप
कर दिया जाता है, और कोई भी सर्वर रिस्पॉन्स इसे बंद नहीं कर सकता।

कनेक्ट करने से पहले डिफ़ॉल्ट रूप से दो चीज़ें चलती हैं, दोनों ऑप्ट-आउट करने योग्य और
दोनों में कोई सेशन डेटा नहीं होता: एक एनोनिमस इंस्टॉल पिंग और PyPI के मुक़ाबले एक वर्ज़न
चेक। एक डिफ़ॉल्ट इंस्टॉल स्टार्टअप बैनर लाइन के लिए एक बार आपका पब्लिक IP भी लुकअप
करता है। हर डेस्टिनेशन, वह क्या ले जाता है और उसे कैसे बंद करें, इसकी सूची
[docs/EGRESS.md](docs/EGRESS.md) में है; सेल्फ़-होस्टेड, रीपॉइंटेड और एयर-गैप्ड इंस्टॉल
कोई भी विवेकाधीन आउटबाउंड कॉल नहीं करते।

डिक्रिप्शन आपके ब्राउज़र में होती है, उस कोड में जो हम आपको सर्व करते हैं। यह पहले एक
वादा हुआ करता था; अब यह कुछ ऐसा है जिसे आप जाँच सकते हैं। आपकी की को छूने वाली
हर लाइन एक पढ़ने लायक फाइल में है, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
जो व्हील के अंदर शिप होती है और ज्यों की त्यों सर्व की जाती है, एक Subresource
Integrity हैश के साथ पिन की गई। यह पुष्टि करने के लिए कि ब्राउज़र वही चलाता है
जो हमने प्रकाशित किया:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

यह क्या साबित नहीं करता: हम वह पेज सर्व करते हैं जो फाइल लोड करता है, इसलिए हम एक
अलग पेज सर्व कर सकते थे। इंटीग्रिटी हैश आपको एक समझौता किए गए CDN से बचाते हैं,
वेंडर से नहीं। आपको जो मिलता है वह यह है कि किसी भी प्रतिस्थापन का जानबूझकर,
पेज सोर्स में दिखाई देने वाला, और PyPI पर मौजूद किसी आर्टिफ़ैक्ट से अलग होना ज़रूरी है
जिसे कोई भी फ़ेच कर सकता है। सेल्फ़-होस्टिंग या केवल लोकल रहना इस निर्भरता को
पूरी तरह ख़त्म कर देता है।

## इंस्टॉल

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक
एजेंट रनटाइम। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

या एजेंट को आपके लिए इसे सेटअप करने दें। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
स्किल Claude Code, Codex, Cursor, Gemini CLI, Copilot या OpenCode को
ClawMetry इंस्टॉल करना, मशीन पर मौजूद एजेंट क्या कर रहे हैं और कितना खर्च कर रहे हैं
इसकी रिपोर्ट देना, अनुरोध पर एक सेशन रोकना, और अप्रूवल के लिए जोखिम भरी टूल
कॉल्स को होल्ड करना सिखाती है:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## दस्तावेज़

| | |
|---|---|
| [रनटाइम कम्पैटिबिलिटी](docs/compatibility.md) | हर अडैप्टर क्या पढ़ता है, और एक रनटाइम कैसे जोड़ें |
| [कॉन्टेक्स्ट ब्लोआउट](docs/CONTEXT_BLOWOUT.md) | प्रति-प्रोवाइडर विंडो, कॉम्पैक्शन बनाम ओवरफ़्लो, प्रति-रनटाइम कवरेज |
| [ओवरहेड](docs/OVERHEAD.md) | इंस्ट्रुमेंटेशन की मापी गई लागत, और उसे दोबारा पैदा करने वाला हार्नेस |
| [एंटाइटलमेंट्स](docs/ENTITLEMENTS.md) | मुफ़्त बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [अप्रूवल्स और पॉलिसी](docs/APPROVALS.md) | प्री-एक्ज़ीक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [अपना खुद का एजेंट लाएँ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सिरे से सिरे तक, चलाने योग्य उदाहरणों के साथ |
| [SDK ट्रैकिंग](docs/SDK_TRACKING.md) | आपके खुद बनाए एजेंट्स के लिए कॉस्ट अट्रिब्यूशन |
| [चैट चैनल](docs/CHANNELS.md) | फ़्लो में दिखाए गए चैट अडैप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप |
| [Docker](docs/DOCKER.md) | इमेज, कम्पोज़, वॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेवलपमेंट](docs/DEVELOPMENT.md) | अंदर से यह कैसे काम करता है; सोर्स से चलाना |
| [टेलीमेट्री](docs/TELEMETRY.md) | एनोनिमस इंस्टॉल और डेस्कटॉप-ओपन पिंग, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट्स

नीचे दिया गया हर आँकड़ा एक असली मशीन से है, रीड-ओनली, बिना कुछ भी सीड किए।

**यह आपको तब बताता है जब कुछ गलत होता है, सिर्फ़ यह नहीं कि क्या हुआ।**
सबसे ऊपर दो एनोमली बैनर: खर्च दैनिक औसत के 7 गुने पर चल रहा है, और एक
4.2x कॉस्ट स्पाइक। उनके नीचे, हाल के 667 में से 324 सेशन में वेस्ट सिग्नल है,
जिसे कारण के अनुसार अलग किया गया है।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**यह आपको दिखाता है कि पैसा कहाँ गया, हर विंडो में।**
आज $252.47, इस हफ़्ते $513.15, इस महीने $1,312.92, हर एक के पीछे के टोकन के
साथ और आपकी सब्सक्रिप्शन उसमें से कितना पहले से कवर करती है। उसके नीचे,
लगभग $1,128/महीना रिकवरेबल के रूप में और कैश रीयूज़ से पहले ही बचाए गए
$17,256/महीना बताए गए हैं।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**यह दिखाता है कि एक मैसेज कैसे जवाब बनता है।**
लाइव फ़्लो डायग्राम: आप, जिस चैनल पर यह आया, गेटवे, अभी जवाब दे रहा मॉडल,
और हर वह टूल जिसका इसने इस्तेमाल किया। काम आगे बढ़ने के साथ नोड्स रोशन होते हैं।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीन पर हर एजेंट, एक ही टेबल में।**
यह क्या चलाता है, पिछले 24 घंटे में और अपने पूरे जीवनकाल में इसकी लागत कितनी है,
इसे आख़िरी बार कब देखा गया, इसका मालिक कौन है, और क्या कोई सब्सक्रिप्शन बिल कवर
कर रही है। यहाँ 14 एजेंट, 3 सेशन काम कर रहे, 13 शांत।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**यह दिखाता है कि किसी टर्न का समय और पैसा कहाँ गया, टूल दर टूल।**
एक असली सेशन का एक टर्न: 11.2 मिनट में 11 टूल, $1.16 में। हर Bash कॉल और मॉडल
कॉल को टाइमलाइन पर अपना बार मिलता है, ताकि जो कमांड 4.1 मिनट तक चली और
जो 226ms तक चली, उन्हें एक नज़र में अलग बताया जा सके।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**यह काम को आँकता है, सिर्फ़ खर्च को नहीं।**
इस हफ़्ते एक A: 54 टास्क साफ़-सुथरे वापस आए, 2 खुरदुरे टास्क की लागत $48.57 रही,
और जिन रन्स में आँकने लायक पर्याप्त गतिविधि नहीं थी उन्हें जीत के रूप में गिनने के बजाय
ग्रेड से बाहर रखा गया। हर खुरदुरा रन अपने ट्रेस से लिंक करता है।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**यह दिखाता है कि कॉन्टेक्स्ट विंडो क्यों भरती जा रही है।**
नवीनतम टर्न पर 1M-टोकन विंडो में से 715K, 83.3% पीक, 4 कॉम्पैक्शन जो सब
ओवरफ़्लो के बजाय प्रोएक्टिव रूप से ट्रिगर हुए, और उसके पीछे हर टर्न का यूटिलाइज़ेशन।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**डिटेक्शन बिना आपको कुछ भी कॉन्फ़िगर किए चलता है।**
बिल्ट-इन डिटेक्टर इंस्टॉल से ही ऑन होते हैं: एजेंट शांत हो गया, टेलीमेट्री फ़ीड
रुक गई, कॉस्ट स्पाइक, टोकन बर्स्ट, बढ़ती हुई एरर्स, एरर स्पाइक, बजट थ्रेशोल्ड,
थ्रेट सिग्नेचर मैच हुआ, सिक्योरिटी टूल फाइंडिंग, सिक्योरिटी पोस्चर बदला। इसके ऊपर
आपके अपने नियम वैकल्पिक हैं।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखिम भरी कॉल को होल्ड करना ऑप्ट-इन है, और डिफ़ॉल्ट रूप से बंद शिप होता है।**
रिकर्सिव डिलीट, फ़ोर्स पुश, sudo, सीक्रेट्स, पैकेज इंस्टॉल और आउटबाउंड कॉल्स में
से हर एक के लिए एक नियम है जिसे आप ऑन कर सकते हैं। जब तक आप ऐसा नहीं करते,
ClawMetry बस देखता है और कुछ नहीं बदलता। एक बार कोई ऑन हो जाए, तो मैचिंग
कॉल्स अप्रूव या डिनाई के लिए यहाँ (या आपके फ़ोन पर) रुकती हैं।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

और भी, प्रत्येक रनटाइम के हिसाब से: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

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
