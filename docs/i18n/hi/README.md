<!-- i18n-src:bab48eec552f -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **14 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 10 अन्य। आपके पूरे एजेंट फ़्लीट के लिए एक ही डैशबोर्ड।

> 🌐 **इसे इनमें पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ अपने आप डिटेक्ट हो जाता है।

```bash
pip install clawmetry && clawmetry
```

यह **http://localhost:8900** पर खुलता है और बस, आपका काम हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजेंट रनटाइम के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह आपके **पूरे एजेंट फ़्लीट** को एक ही डैशबोर्ड में मापता है, आपकी मशीन पर हर रनटाइम को अपने आप डिटेक्ट करते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम ClawMetry Cloud या सेल्फ़-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें और हर टैब — cost, tokens, tools, traces — उसी रनटाइम के अनुसार फिर से स्कोप हो जाता है। सटीक फ़्री/पेड विभाजन, टियर मैट्रिक्स, `/api/entitlement` शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow** — चैनलों, brain, tools से होकर और वापस बहने वाले संदेशों को दिखाने वाला लाइव एनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक, गतिविधि हीटमैप, सेशन काउंट, मॉडल जानकारी
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम गतिविधि के साथ सक्रिय एजेंट सेशन
- **Crons** — स्टेटस, अगला रन, अवधि के साथ शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रीयल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउज़ करें
- **Transcripts** — सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप, एरर-रेट ट्रिगर, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर रूट होते हैं
- **Approvals** — डिस्ट्रक्टिव डिलीट, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल्स को एक-क्लिक साइन-ऑफ़ के पीछे गेट करें

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव एजेंट इवेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन उपयोग और सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रीयल-टाइम टूल कॉल फ़ीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडल और सेशन के अनुसार कॉस्ट ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फ़ाइल ब्राउज़र
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोस्चर और ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजट कैप, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email के लिए वेबहुक
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल्स को मैनुअल साइन-ऑफ़ के पीछे गेट करें; पॉलिसी-समर्थित सुरक्षा नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code के लिए प्री-एग्ज़ीक्यूशन ब्लॉकिंग** — एक कमांड एक
PreToolUse hook इंस्टॉल करता है जो मैचिंग टूल कॉल्स को चलने *से पहले*
रोक देता है और आपके फ़ैसले का इंतज़ार करता है ([cloud push notifications](https://app.clawmetry.com/push)
सक्षम होने पर आपके फ़ोन से एक टैप):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक डिनाई सिर्फ़ उस एक टूल कॉल को ब्लॉक करता है — एजेंट अपना सेशन बनाए
रखता है और दूसरा तरीका आज़मा सकता है। आपके फ़ोन पर अप्रूव करना Claude
Code के अपने परमिशन प्रॉम्प्ट को स्किप कर देता है (आप पहले ही जवाब दे
चुके हैं)। बिना मैच वाले टूल्स की लागत ~40ms होती है और वे Claude
Code के सामान्य परमिशन फ़्लो में चले जाते हैं। जब Claude Code खुद आपके
जवाब का इंतज़ार कर रहा हो तो भी आपको फ़ोन पुश मिलता है
(`permission_prompt` / `idle_prompt` नोटिफ़िकेशन)।

## इंस्टॉल करें

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

v2 React ऐप `frontend/` में है और जब Flask सर्वर v2 सक्षम होकर शुरू
किया जाता है तो यह `/v2` पर सर्व होता है।

डेवलपमेंट के दौरान दो टर्मिनल इस्तेमाल करें:

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

`http://localhost:5173/v2/` खोलें। Vite `/api` रिक्वेस्ट को
`http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना अतिरिक्त
CORS सेटअप के लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ भेजा जाने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry सिर्फ़ OpenClaw ही नहीं, बल्कि कई AI-एजेंट रनटाइम को ऑब्ज़र्व
करता है। हर गैर-OpenClaw रनटाइम एक डेडिकेटेड रीडर एडाप्टर शिप करता है जो
उसके नेटिव सेशन फ़ॉर्मैट को ClawMetry के यूनिफ़ाइड शेप्स में बदलता है;
डेमन इन्हें रनटाइम टैग के साथ उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में
इनजेस्ट करता है, और जब एक से अधिक रनटाइम मौजूद हों तो Session replay
टैब एक **रनटाइम स्विचर** दिखाता है। पूरी मैट्रिक्स + रनटाइम जोड़ने की
गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) और
OpenClaw-फ़ैमिली परिचय के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

| रनटाइम / एजेंट | स्थिति | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव | संदर्भ रनटाइम, अपने आप डिटेक्ट होता है |
| **PicoClaw** | बीटा एडाप्टर | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स। |
| **NanoClaw** | बीटा एडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट + मैसेज काउंट। |
| **Hermes** | बीटा एडाप्टर | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट, मॉडल, टोकन/कॉस्ट। |
| **Claude Code** | बीटा एडाप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स + थिंकिंग, टोकन उपयोग। |
| **Codex** | बीटा एडाप्टर | रोलआउट JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Cursor** | बीटा एडाप्टर | SQLite `state.vscdb`। चैट/कंपोज़र ट्रांसक्रिप्ट, मॉडल। |
| **Aider** | बीटा एडाप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट, मॉडल, टोकन काउंट। |
| **Goose** | बीटा एडाप्टर | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन टोटल। |
| **opencode** | बीटा एडाप्टर | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Qwen Code** | बीटा एडाप्टर | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Pi** | बीटा एडाप्टर | JSONL `~/.pi/agent/sessions`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Deep Agents** | बीटा एडाप्टर | SQLite `~/.deepagents/.state/sessions.db`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |

"बीटा एडाप्टर" का मतलब है कि ClawMetry उस रनटाइम के असली ऑन-डिस्क
फ़ॉर्मैट के लिए एक रीडर शिप करता है, जिसे किसी असली मशीन पर असली इंस्टॉल
के मुक़ाबले बनाया और वेरिफ़ाई किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)।
एडाप्टर रीड-ओनली हैं; हर एक इस बारे में ईमानदार है कि उसका रनटाइम असल
में क्या स्टोर करता है (उदाहरण के लिए, PicoClaw/NanoClaw/Cursor डिस्क
पर टोकन कॉस्ट नहीं लिखते)। जब एक नोड पर कई रनटाइम चल रहे हों, तो रनटाइम
स्विचर एक क्लीन डीप-डाइव के लिए सेशन व्यू को एक रनटाइम तक सीमित कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट अट्रिब्यूशन

ऊपर बताए गए सभी रनटाइम अपने सेशन डिस्क पर लिखते हैं। आपका अपना
**प्रोडक्शन एजेंट** — जो आपने OpenAI Agents SDK, LangChain, Vercel AI
SDK, LlamaIndex, E2B, या एक सादे `httpx` लूप पर बनाया है — ऐसा नहीं
करता। ClawMetry का शून्य-कॉन्फ़िग इंटरसेप्टर फिर भी `httpx`/`requests`
को मंकी-पैच करके उसकी LLM कॉल्स (कॉस्ट, टोकन, लेटेंसी, एरर) कैप्चर कर
लेता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` env वेरिएबल) हर
कॉल को एक **नामित सोर्स** से टैग करता है, ताकि आपका चलाया हुआ हर
प्रोडक्ट डैशबोर्ड के Overview पर मौजूद **🔌 Out-loop sources** कार्ड
में अपनी ख़ुद की, कॉस्ट-अट्रिब्यूटेबल फ़र्स्ट-क्लास लाइन के रूप में
दिखे — प्रति एजेंट कॉल्स, प्रोवाइडर, लेटेंसी, एरर रेट। कोई सोर्स सेट
नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; बस कार्ड छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जो रनटाइम एडाप्टर फ़ीड करते हैं (DuckDB → cloud
snapshot), इसलिए आउट-लूप सोर्स भी बाकी सब चीज़ों की तरह E2E-एन्क्रिप्टेड
होकर क्लाउड डैशबोर्ड में सिंक होते हैं।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI
सिमैंटिक कन्वेंशन** का इस्तेमाल करते हुए, ताकि आपके एजेंट ट्रेस कभी
किसी एक टूल में लॉक-इन न हों।

हर सेशन — LLM कॉल्स, टूल्स, सब-एजेंट, टोकन, कॉस्ट — को किसी भी कलेक्टर
(Datadog, Grafana, Honeycomb, या आपका अपना OTel Collector) में
OTLP/HTTP GenAI स्पैन के रूप में **एक्सपोर्ट** करें:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth हेडर और पोल इंटरवल वैकल्पिक env वेरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर
किसी और भी चीज़ से ट्रेस और मेट्रिक स्वीकार करता है (protobuf इनजेस्ट
के लिए `pip install clawmetry[otel]`)।

आपको शून्य-कॉन्फ़िग, लोकल-फ़र्स्ट ClawMetry डैशबोर्ड **और** आपका डेटा
आपकी टीम पहले से चला रहे किसी भी बैकएंड में मिलता है — कोई लॉक-इन नहीं,
कोई दूसरा एजेंट इंस्टॉल करने की ज़रूरत नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं पड़ती। ClawMetry आपके
वर्कस्पेस, लॉग, सेशन, और क्रॉन को अपने आप डिटेक्ट कर लेता है।

अगर आपको कस्टमाइज़ करना हो:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव गतिविधि
दिखाता है। सिर्फ़ वे चैनल जो वाक़ई आपके `openclaw.json` में सेटअप हैं,
Flow डायग्राम में दिखते हैं — बिना कॉन्फ़िगर किए हुए चैनल अपने आप छिप
जाते हैं।

Flow में किसी भी चैनल नोड पर क्लिक करके इनकमिंग/आउटगोइंग मैसेज काउंट के
साथ लाइव चैट बबल व्यू देखें।

| चैनल | स्थिति | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मैसेज, स्टैट्स, 10s रीफ़्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | सीधे `~/Library/Messages/chat.db` पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के ज़रिए |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के ज़रिए |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के ज़रिए iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक के ज़रिए |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन के ज़रिए |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ़-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE सपोर्ट |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DM |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के ज़रिए चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपकी `~/.openclaw/openclaw.json` पढ़ता है
> और सिर्फ़ वही चैनल रेंडर करता है जो आपने वाक़ई कॉन्फ़िगर किए हैं। कोई
> मैनुअल सेटअप ज़रूरी नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को कंटेनर में चलाना चाहते हैं? कोई दिक़्क़त नहीं! 🐳

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

> **नोट:** Docker में चलाते समय, अपने एजेंट की डेटा + लॉग डायरेक्टरी
> (जैसे `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करें ताकि
> ClawMetry आपका सेटअप अपने आप डिटेक्ट कर सके।

## आवश्यकताएँ

- Python 3.8+
- Flask (pip के ज़रिए अपने आप इंस्टॉल हो जाता है)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude
  Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider,
  NanoClaw, PicoClaw, Pi, या Deep Agents (या Docker के लिए माउंटेड
  वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) को अपने आप
डिटेक्ट करता है — यह NVIDIA का एंटरप्राइज़ सुरक्षा रैपर है जो OpenClaw
के लिए एजेंट को सैंडबॉक्स्ड OpenShell कंटेनर के अंदर चलाता है।

ज़्यादातर मामलों में कोई अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक
डेमन सेशन फ़ाइलों को अपने आप खोज लेता है, चाहे वे होस्ट पर
`~/.openclaw/` में हों या किसी OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry NemoClaw को दो तरीकों से डिटेक्ट करता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स
   जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — चल रहे Docker कंटेनर में `openshell`,
   `nemoclaw`, या `ghcr.io/nvidia/` इमेज को स्कैन करता है, फिर वॉल्यूम
   माउंट या `docker cp` के ज़रिए सेशन पढ़ता है

NemoClaw कंटेनर से सिंक की गई सेशन फ़ाइलें क्लाउड डैशबोर्ड में
`runtime=nemoclaw` और `container_id` मेटाडेटा के साथ टैग होती हैं,
ताकि आप उन्हें एक नज़र में मानक OpenClaw सेशन से अलग बता सकें।

### अनुशंसित सेटअप: होस्ट पर सिंक डेमन

सबसे अच्छे अनुभव के लिए, ClawMetry के सिंक डेमन को **होस्ट मशीन** पर
चलाएँ (सैंडबॉक्स के अंदर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी की
पाबंदियों से बचा जा सकता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशन को अपने आप ढूँढ
लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम न करे, तो ClawMetry को सही सैंडबॉक्स की ओर इशारा
करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (एडवांस्ड)

अगर आपको सिंक डेमन **सैंडबॉक्स के अंदर** OpenShell में चलाना ही है, तो
अपनी NemoClaw नेटवर्क पॉलिसी में यह egress नियम जोड़ें ताकि यह
ClawMetry इनजेस्ट API तक पहुँच सके:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

इसे लागू करें:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट और एंडपॉइंट

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | ज़रूरी |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` पर आउटबाउंड HTTPS कॉल करता है।
कोई इनबाउंड पोर्ट ज़रूरी नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी, और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

इस प्रोजेक्ट का परीक्षण BrowserStack से किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

जब आप किसी नई मशीन पर पहली बार `clawmetry` CLI चलाते हैं, तो ClawMetry
`https://app.clawmetry.com/api/install` पर एक बार अनाम "फ़र्स्ट रन" पिंग
भेजता है। हम इसका उपयोग इंस्टॉल गिनने के लिए करते हैं (एक OSS प्रोजेक्ट
के लिए हमारे पास बस यही मार्केटिंग मेट्रिक है) और यह जानने के लिए कि
हमारे यूज़र्स ने कौन-से एजेंट फ़्रेमवर्क इंस्टॉल किए हैं।

**प्रति इंस्टॉल ठीक एक POST**, जिसमें शामिल है:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` में स्टोर की गई रैंडम UUID | डिडुप; आपके ईमेल या api_key से लिंक नहीं |
| `version` | `0.12.167` | कौन-से वर्ज़न इस्तेमाल में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म सपोर्ट प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न सपोर्ट मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल को CI शोर से अलग करना |

**हम यह नहीं भेजते**: IP (क्लाउड सर्वर-साइड रिक्वेस्ट से देश कोड
निकालता है, फिर IP को त्याग देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस
पाथ, फ़ाइल कंटेंट, आपकी api_key, आपका ईमेल, कोई भी PII या
वर्कस्पेस-विशिष्ट जानकारी। वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट करने योग्य है।

**ऑप्ट आउट** करें (इनमें से कोई भी एक इसे स्थायी रूप से बंद कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहाँ कोई नेटवर्क फ़ेलियर कभी `clawmetry` को चलने से नहीं रोकता — यह
पिंग एक डेमन थ्रेड पर 3 सेकंड के टाइमआउट के साथ फ़ायर-एंड-फ़ॉरगेट है।

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
  <sub>बनाया <a href="https://github.com/vivekchand">@vivekchand</a> ने · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टम का हिस्सा</sub>
</p>
