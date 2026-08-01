<!-- i18n-src:191e9094d7fa -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **14 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 10 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक डैशबोर्ड।

> 🌐 **इसे इस भाषा में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ अपने आप पहचानता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और आपका काम हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजेंट रनटाइम के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह आपके **पूरे एजेंट फ़्लीट** को एक ही डैशबोर्ड में मापता है, आपकी मशीन पर मौजूद हर रनटाइम को अपने आप पहचानते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम ClawMetry Cloud या सेल्फ़-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें, और हर टैब (कॉस्ट, टोकन, टूल्स, ट्रेस) उस रनटाइम के अनुसार फिर से स्कोप हो जाता है। सटीक फ्री/पेड विभाजन, टियर मैट्रिक्स, `/api/entitlement` शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow**: लाइव एनिमेटेड डायग्राम जो चैनलों, ब्रेन, टूल्स से होकर और वापस आते संदेशों के प्रवाह को दिखाता है
- **Overview**: हेल्थ चेक, एक्टिविटी हीटमैप, सेशन काउंट, मॉडल जानकारी
- **Usage**: दैनिक/साप्ताहिक/मासिक ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions**: मॉडल, टोकन, अंतिम गतिविधि के साथ सक्रिय एजेंट सेशन
- **Crons**: स्टेटस, अगले रन, अवधि के साथ शेड्यूल्ड जॉब्स
- **Logs**: कलर-कोडेड रीयल-टाइम लॉग स्ट्रीमिंग
- **Memory**: SOUL.md, MEMORY.md, AGENTS.md, डेली नोट्स ब्राउज़ करें
- **Transcripts**: सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts**: बजट कैप, एरर-रेट ट्रिगर, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर भेजता है
- **Approvals**: विनाशकारी डिलीट, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल्स को एक-क्लिक साइन-ऑफ के पीछे गेट करता है

## स्क्रीनशॉट

### 🧠 Brain: लाइव एजेंट इवेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: टोकन उपयोग और सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: रीयल-टाइम टूल कॉल फ़ीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: मॉडल और सेशन के अनुसार कॉस्ट ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: वर्कस्पेस फ़ाइल ब्राउज़र
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: पोस्चर और ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: बजट कैप, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email के लिए वेबहुक
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: जोखिम भरे टूल कॉल्स को मैनुअल साइन-ऑफ के पीछे गेट करता है; पॉलिसी-समर्थित सुरक्षा नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code के लिए प्री-एक्ज़ीक्यूशन ब्लॉकिंग**: एक कमांड एक PreToolUse हुक इंस्टॉल करता है जो मेल खाते टूल कॉल्स को चलने *से पहले* रोकता है और आपके निर्णय की प्रतीक्षा करता है ([cloud push notifications](https://app.clawmetry.com/push) सक्षम होने पर आपके फ़ोन से एक टैप में):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक deny केवल उस एक टूल कॉल को ब्लॉक करता है, एजेंट अपना सेशन बनाए रखता है और कोई और तरीका आज़मा सकता है। अपने फ़ोन पर अप्रूव करने से Claude Code का खुद का परमिशन प्रॉम्प्ट छूट जाता है (आप पहले ही जवाब दे चुके हैं)। न मिलने वाले टूल्स की लागत ~40ms होती है और वे Claude Code के सामान्य परमिशन फ़्लो में चले जाते हैं। जब Claude Code खुद आपकी प्रतीक्षा कर रहा हो तो आपको फ़ोन पर पुश नोटिफ़िकेशन भी मिलता है (`permission_prompt` / `idle_prompt` नोटिफ़िकेशन)।

## इंस्टॉल

**वन-लाइनर (अनुशंसित):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**सोर्स से:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 फ़्रंटएंड डेवलपमेंट

v2 React ऐप `frontend/` में रहता है और जब Flask सर्वर को v2 सक्षम करके शुरू किया जाता है तो यह `/v2` पर सर्व होता है।

डेवलप करते समय दो टर्मिनल का उपयोग करें:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` खोलें। Vite `/api` रिक्वेस्ट को `http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना किसी अतिरिक्त CORS सेटअप के लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry सिर्फ़ OpenClaw ही नहीं, बल्कि कई AI-एजेंट रनटाइम को ऑब्ज़र्व करता है। हर non-OpenClaw रनटाइम के साथ एक समर्पित रीडर एडेप्टर आता है जो उसके नेटिव सेशन फ़ॉर्मेट को ClawMetry के यूनिफ़ाइड शेप्स में बदलता है; डेमॉन इन्हें रनटाइम टैग के साथ उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इनजेस्ट करता है, और जब एक से ज़्यादा रनटाइम मौजूद हों तो Session replay टैब एक **रनटाइम स्विचर** दिखाता है। पूरी मैट्रिक्स और रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-फ़ैमिली परिचय के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

[Perplexity का numbat](https://github.com/perplexityai/numbat) एजेंट-सुरक्षा टूल चला रहे हैं? ClawMetry इसके फाइंडिंग्स और एनफोर्समेंट निर्णयों को आउट ऑफ़ द बॉक्स इनजेस्ट करता है, देखें [`docs/NUMBAT.md`](docs/NUMBAT.md)।

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | नेटिव | रेफरेंस रनटाइम, ऑटो-डिटेक्टेड |
| **PicoClaw** | बीटा एडेप्टर | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स। |
| **NanoClaw** | बीटा एडेप्टर | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट + मैसेज काउंट। |
| **Hermes** | बीटा एडेप्टर | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट, मॉडल, टोकन/कॉस्ट। |
| **Claude Code** | बीटा एडेप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स + थिंकिंग, टोकन उपयोग। |
| **Codex** | बीटा एडेप्टर | Rollout JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Cursor** | बीटा एडेप्टर | SQLite `state.vscdb`। चैट/कंपोज़र ट्रांसक्रिप्ट, मॉडल। |
| **Aider** | बीटा एडेप्टर | प्रति प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट, मॉडल, टोकन काउंट। |
| **Goose** | बीटा एडेप्टर | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन टोटल। |
| **opencode** | बीटा एडेप्टर | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Qwen Code** | बीटा एडेप्टर | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Pi** | बीटा एडेप्टर | JSONL `~/.pi/agent/sessions`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Deep Agents** | बीटा एडेप्टर | SQLite `~/.deepagents/.state/sessions.db`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **n8n** | बीटा एडेप्टर | SQLite `~/.n8n/database.sqlite`। वर्कफ़्लो एक्ज़ीक्यूशन, नोड रन, AI Agent प्रॉम्प्ट, मॉडल + टोकन जहाँ n8n उन्हें रिकॉर्ड करता है। |
| **Antigravity** | बीटा एडेप्टर | `~/.gemini/<flavor>/brain/` के अंतर्गत Brain JSONL। कन्वर्सेशन, टूल स्टेप्स, थिंकिंग, प्रति-जनरेशन Gemini टोकन स्प्लिट + कॉस्ट, बैकग्राउंड-जनरेशन बर्न। |

"बीटा एडेप्टर" का मतलब है कि ClawMetry उस रनटाइम के वास्तविक ऑन-डिस्क फ़ॉर्मेट के लिए एक रीडर शिप करता है, जिसे हर बार एक असली मशीन पर असली इंस्टॉल के विरुद्ध बनाया और सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। एडेप्टर रीड-ओनली हैं; हर एक इस बारे में ईमानदार है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (उदाहरण के लिए, PicoClaw/NanoClaw/Cursor डिस्क पर टोकन कॉस्ट नहीं लिखते)। जब एक ही नोड पर कई रनटाइम चल रहे हों, तो रनटाइम स्विचर सेशन व्यू को एक साफ़ डीप-डाइव के लिए एक रनटाइम तक सीमित कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें: आउट-लूप कॉस्ट एट्रिब्यूशन

ऊपर बताए गए सभी रनटाइम सेशन को डिस्क पर लिखते हैं। आपका अपना **प्रोडक्शन एजेंट** (जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक साधारण `httpx` लूप पर बनाया है) ऐसा नहीं करता। ClawMetry का ज़ीरो-कॉन्फ़िग इंटरसेप्टर फिर भी `httpx`/`requests` को मंकी-पैच करके इसकी LLM कॉल्स (कॉस्ट, टोकन, लेटेंसी, एरर) कैप्चर कर लेता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` env वेरिएबल) हर कॉल को एक **नामित सोर्स** से टैग करता है, ताकि आपका चलाया हर प्रोडक्ट Overview पर डैशबोर्ड के **🔌 Out-loop sources** कार्ड में अपनी खुद की फ़र्स्ट-क्लास, कॉस्ट-एट्रिब्यूटेबल लाइन के रूप में दिखे, यानी प्रति एजेंट कॉल्स, प्रोवाइडर, लेटेंसी, एरर रेट। कोई सोर्स सेट नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; बस कार्ड छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह उसी डेटा लेयर का उपयोग करता है जो रनटाइम एडेप्टर इस्तेमाल करते हैं (DuckDB → क्लाउड स्नैपशॉट), इसलिए आउट-लूप सोर्स भी बाकी सब कुछ की तरह ही क्लाउड डैशबोर्ड से सिंक होते हैं, वह भी एंड-टू-एंड एन्क्रिप्टेड।

## OpenTelemetry: वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry **GenAI सिमेंटिक कन्वेंशन** का उपयोग करते हुए दोनों दिशाओं में **OpenTelemetry** बोलता है, ताकि आपके एजेंट ट्रेस कभी किसी एक टूल में लॉक न हों।

हर सेशन को **एक्सपोर्ट** करें (LLM कॉल्स, टूल्स, सब-एजेंट, टोकन, कॉस्ट) OTLP/HTTP GenAI स्पैन के रूप में किसी भी कलेक्टर पर (Datadog, Grafana, Honeycomb, या आपका खुद का OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर और पोल इंटरवल वैकल्पिक env वेरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट**: बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर किसी भी और चीज़ से ट्रेस और मेट्रिक्स स्वीकार करता है (प्रोटोबफ़ इनजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फ़र्स्ट ClawMetry डैशबोर्ड **और** आपकी टीम जो भी बैकएंड पहले से चला रही है उसमें आपका डेटा, दोनों मिलते हैं; न कोई लॉक-इन, न इंस्टॉल करने के लिए कोई दूसरा एजेंट।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग, सेशन, और क्रॉन को अपने आप पहचान लेता है।

अगर आपको कस्टमाइज़ करने की ज़रूरत है:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके द्वारा कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव गतिविधि दिखाता है। केवल वे चैनल जो वास्तव में आपके `openclaw.json` में सेट अप हैं, Flow डायग्राम में दिखते हैं; जो कॉन्फ़िगर नहीं हैं वे अपने आप छिपा दिए जाते हैं।

आने वाले/जाने वाले संदेशों की संख्या के साथ लाइव चैट बबल व्यू देखने के लिए Flow में किसी भी चैनल नोड पर क्लिक करें।

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आँकड़े, 10 सेकंड रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | सीधे `~/Library/Messages/chat.db` पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के ज़रिए |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के ज़रिए |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के ज़रिए iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक के ज़रिए |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams bot प्लगइन के ज़रिए |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ़-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DM |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के ज़रिए चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपकी `~/.openclaw/openclaw.json` पढ़ता है और केवल वही चैनल रेंडर करता है जिन्हें आपने वास्तव में कॉन्फ़िगर किया है। किसी मैनुअल सेटअप की ज़रूरत नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को एक कंटेनर में चलाना चाहते हैं? कोई समस्या नहीं! 🐳

**Docker के साथ क्विक स्टार्ट:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose उदाहरण:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **नोट:** Docker में चलाते समय, अपने एजेंट की डेटा + लॉग डायरेक्टरी माउंट करें (उदाहरण के लिए `~/.openclaw`, `~/.claude`, `~/.codex`) ताकि ClawMetry आपके सेटअप को अपने आप पहचान सके।

## आवश्यकताएँ

- Python 3.8+
- Flask (pip के ज़रिए अपने आप इंस्टॉल हो जाता है)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, या Antigravity (या Docker के लिए माउंटेड वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry अपने आप [NemoClaw](https://github.com/NVIDIA/NemoClaw) का पता लगा लेता है, जो NVIDIA का OpenClaw के लिए एंटरप्राइज़ सुरक्षा रैपर है और जो एजेंट को सैंडबॉक्स्ड OpenShell कंटेनर के भीतर चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं होती। sync डेमॉन सेशन फ़ाइलों को अपने आप खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या किसी OpenShell कंटेनर के भीतर।

### यह कैसे काम करता है

ClawMetry दो तरीकों से NemoClaw का पता लगाता है:

1. **बाइनरी डिटेक्शन**: `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन**: `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज के लिए चल रहे Docker कंटेनरों को स्कैन करता है, फिर वॉल्यूम माउंट या `docker cp` के ज़रिए सेशन पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलों को क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा से टैग किया जाता है, ताकि आप एक नज़र में उन्हें स्टैंडर्ड OpenClaw सेशन से अलग बता सकें।

### अनुशंसित सेटअप: HOST पर sync डेमॉन

सबसे अच्छे अनुभव के लिए, ClawMetry के sync डेमॉन को **होस्ट मशीन** पर चलाएँ (सैंडबॉक्स के भीतर नहीं)। इससे NemoClaw की नेटवर्क पॉलिसी प्रतिबंधों से बचा जा सकता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync डेमॉन किसी भी चल रहे OpenShell कंटेनर के भीतर सेशन को अपने आप खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स की ओर इंगित करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के भीतर चलाना (एडवांस्ड)

अगर आपको sync डेमॉन को OpenShell सैंडबॉक्स के **भीतर** ही चलाना है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह egress नियम जोड़ें ताकि यह ClawMetry इनजेस्ट API तक पहुँच सके:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

इसके साथ लागू करें:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट और एंडपॉइंट

| Endpoint | Port | Protocol | Required |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (sync डेमॉन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | - | Unix socket | कंटेनर सेशन डिस्कवरी के लिए |

sync डेमॉन केवल `ingest.clawmetry.com` पर आउटबाउंड HTTPS कॉल करता है। किसी इनबाउंड पोर्ट की ज़रूरत नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी, और Docker के लिए **[क्लाउड टेस्टिंग गाइड](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

यह प्रोजेक्ट BrowserStack के साथ टेस्ट किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry `https://app.clawmetry.com/api/install` पर गुमनाम install-lifecycle पिंग भेजता है: नई मशीन पर पहली बार `clawmetry` CLI चलाने पर एक `install` पिंग, नए वर्ज़न में अपग्रेड करने के बाद पहली बार चलाने पर एक `update` पिंग, और डैशबोर्ड-के-भीतर ऑनबोर्डिंग चॉइस पूरी करने पर एक `onboarded` पिंग। हम इसका उपयोग असली इंस्टॉल गिनने के लिए करते हैं (कच्चे PyPI डाउनलोड आँकड़े लगभग 98% मिरर, CI, और ऑटो-अपडेट री-डाउनलोड होते हैं) और यह जानने के लिए कि वास्तव में कौन से एजेंट फ्रेमवर्क और वर्ज़न इस्तेमाल हो रहे हैं।

**हर वर्ज़न के लिए प्रति लाइफ़साइकिल इवेंट अधिकतम एक POST**, जिसमें शामिल है:

| Field | Example | Why |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर संग्रहीत रैंडम UUID | डीड्यूप; तब तक गुमनाम जब तक आप स्पष्ट रूप से Cloud sync कनेक्ट नहीं करते (उसके बाद authenticated डेमॉन हार्टबीट इसे साथ ले जाता है, जो इस इंस्टॉल को आपके अकाउंट से जोड़ता है) |
| `event` | `install` / `update` / `onboarded` | नया इंस्टॉल बनाम किसी मौजूदा का अपग्रेड |
| `version` | `0.12.167` | कौन से वर्ज़न इस्तेमाल हो रहे हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | आगे किन एजेंट के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड रिक्वेस्ट से सर्वर-साइड पर देश कोड निकालता है, फिर IP को हटा देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस पाथ, फ़ाइल कंटेंट, आपकी api_key, आपका ईमेल, कोई भी PII या वर्कस्पेस-विशिष्ट जानकारी। वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट किया जा सकता है।

**ऑप्ट आउट करें** (इनमें से कोई भी एक इसे स्थायी रूप से बंद कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहाँ नेटवर्क फ़ेलियर कभी भी `clawmetry` को चलने से नहीं रोकता; पिंग एक डेमॉन थ्रेड पर 3 सेकंड के टाइमआउट के साथ फ़ायर-एंड-फ़ॉरगेट होती है।

## स्टार हिस्ट्री

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लाइसेंस

MIT

---

<p align="center">
  <strong>🦞 अपने एजेंट को सोचते हुए देखें</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> द्वारा बनाया गया · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टम का हिस्सा</sub>
</p>
