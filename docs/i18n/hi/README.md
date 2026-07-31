<!-- i18n-src:02b789586c7d -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **14 AI एजेंट रनटाइम्स** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 10 अन्य। आपके पूरे एजेंट फ्लीट के लिए एक डैशबोर्ड।

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और देखें →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ ऑटो-डिटेक्ट।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और बस, हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजेंट रनटाइम्स के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह एक ही डैशबोर्ड में आपके **पूरे एजेंट फ्लीट** को मीटर करता है, आपकी मशीन पर हर रनटाइम को ऑटो-डिटेक्ट करते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम्स ClawMetry Cloud या सेल्फ-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें और हर टैब — कॉस्ट, टोकन, टूल्स, ट्रेसेस — उसी रनटाइम पर फिर से स्कोप हो जाता है। सटीक फ्री/पेड विभाजन, टियर मैट्रिक्स, `/api/entitlement` शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow** — चैनलों, ब्रेन, टूल्स से होकर और वापस बहते संदेशों को दिखाने वाला लाइव एनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, एक्टिविटी हीटमैप, सेशन काउंट्स, मॉडल जानकारी
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम एक्टिविटी के साथ सक्रिय एजेंट सेशन
- **Crons** — स्टेटस, अगला रन, ड्यूरेशन के साथ शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रीयल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, डेली नोट्स ब्राउज़ करें
- **Transcripts** — सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप्स, एरर-रेट ट्रिगर्स, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर भेजता है
- **Approvals** — विनाशकारी डिलीट्स, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल्स को एक-क्लिक साइन-ऑफ के पीछे गेट करें

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

### 🚨 Alerts — बजट कैप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email को वेबहुक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल्स को मैनुअल साइन-ऑफ के पीछे गेट करें; पॉलिसी-समर्थित प्रोटेक्शन नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code के लिए प्री-एक्ज़ीक्यूशन ब्लॉकिंग** — एक कमांड एक
PreToolUse hook इंस्टॉल करता है जो मेल खाने वाले टूल कॉल्स को *चलने से पहले*
रोक देता है और आपके निर्णय का इंतज़ार करता है (आपके फ़ोन से एक टैप, जब
[cloud push notifications](https://app.clawmetry.com/push) सक्षम हों):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक "deny" केवल उसी एक टूल कॉल को ब्लॉक करता है — एजेंट अपना सेशन बनाए रखता है और
कोई दूसरा तरीका आज़मा सकता है। आपके फ़ोन पर अप्रूव करना Claude Code के अपने
परमिशन प्रॉम्प्ट को स्किप कर देता है (आप पहले ही जवाब दे चुके हैं)। बेमेल टूल्स की लागत ~40ms होती है और
वे Claude Code के सामान्य परमिशन फ़्लो में चले जाते हैं। जब Claude Code खुद आपके जवाब का
इंतज़ार कर रहा हो, तो आपको फ़ोन पुश भी मिलता है (`permission_prompt` /
`idle_prompt` नोटिफिकेशन्स)।

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

## v2 फ्रंटएंड डेवलपमेंट

v2 React ऐप `frontend/` में रहता है और जब Flask
सर्वर v2 सक्षम के साथ शुरू किया जाता है तो यह `/v2` पर सर्व होता है।

डेवलप करते समय दो टर्मिनल का इस्तेमाल करें:

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

`http://localhost:5173/v2/` खोलें। Vite `/api` रिक्वेस्ट्स को
`http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना किसी अतिरिक्त
CORS सेटअप के लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry केवल OpenClaw ही नहीं, बल्कि कई AI-एजेंट रनटाइम्स को ऑब्ज़र्व करता है। हर गैर-OpenClaw रनटाइम एक समर्पित रीडर एडैप्टर शिप करता है जो उसके नेटिव सेशन फ़ॉर्मैट को ClawMetry के यूनिफ़ाइड शेप्स में अनुवादित करता है; डेमन इन्हें रनटाइम टैग के साथ उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इनजेस्ट करता है, और Session रीप्ले टैब एक से अधिक रनटाइम मौजूद होने पर एक **रनटाइम स्विचर** दिखाता है। पूरा मैट्रिक्स + रनटाइम्स जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-फैमिली प्राइमर के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

| रनटाइम / एजेंट | स्टेटस | नोट्स |
|---|---|---|
| **OpenClaw** | Native | रेफ़रेंस रनटाइम, ऑटो-डिटेक्टेड |
| **PicoClaw** | Beta adapter | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स। |
| **NanoClaw** | Beta adapter | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट्स + मैसेज काउंट्स। |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट्स, मॉडल, टोकन्स/कॉस्ट। |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स + थिंकिंग, टोकन उपयोग। |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Cursor** | Beta adapter | SQLite `state.vscdb`। चैट/कंपोज़र ट्रांसक्रिप्ट्स, मॉडल। |
| **Aider** | Beta adapter | प्रति-प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट्स, मॉडल, टोकन काउंट्स। |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन टोटल्स। |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन्स + कॉस्ट। |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन्स + कॉस्ट। |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन्स + कॉस्ट। |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`। वर्कफ़्लो एक्ज़ीक्यूशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, जहाँ n8n रिकॉर्ड करता है वहाँ मॉडल + टोकन्स। |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` के तहत Brain JSONL। कन्वर्सेशन्स, टूल स्टेप्स, थिंकिंग, प्रति-जनरेशन Gemini टोकन स्प्लिट + कॉस्ट, बैकग्राउंड-जनरेशन बर्न। |

"Beta adapter" का मतलब है कि ClawMetry उस रनटाइम के वास्तविक ऑन-डिस्क फ़ॉर्मैट के लिए एक रीडर शिप करता है, जिसे असली मशीन पर असली इंस्टॉल के विरुद्ध बनाया और सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। एडैप्टर्स रीड-ओनली हैं; हर एक इस बारे में स्पष्ट है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (जैसे, PicoClaw/NanoClaw/Cursor डिस्क पर टोकन कॉस्ट नहीं लिखते)। जब एक नोड पर कई रनटाइम्स चल रहे हों, तो रनटाइम स्विचर एक साफ़ डीप-डाइव के लिए सेशंस व्यू को एक पर स्कोप कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट एट्रिब्यूशन

ऊपर बताए गए सभी रनटाइम्स सेशंस को डिस्क पर लिखते हैं। आपका खुद का **प्रोडक्शन एजेंट** — जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक सादे `httpx` लूप पर बनाया है — ऐसा नहीं करता। ClawMetry का ज़ीरो-कॉन्फ़िग इंटरसेप्टर फिर भी `httpx`/`requests` को मंकी-पैच करके इसकी LLM कॉल्स (कॉस्ट, टोकन्स, लेटेंसी, एरर्स) कैप्चर करता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` env वेरिएबल) हर कॉल को एक **नामित सोर्स** के साथ टैग करता है, ताकि आपका चलाया हर प्रोडक्ट डैशबोर्ड के Overview पर मौजूद **🔌 Out-loop sources** कार्ड में अपनी खुद की, कॉस्ट-एट्रिब्यूटेबल लाइन के रूप में दिखे — प्रति एजेंट कॉल्स, प्रोवाइडर्स, लेटेंसी, एरर रेट। कोई सोर्स सेट नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; बस कार्ड छुपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जिसे रनटाइम एडैप्टर्स फ़ीड करते हैं (DuckDB → क्लाउड स्नैपशॉट), इसलिए आउट-लूप सोर्सेज़ बाकी सब चीज़ों की तरह ही क्लाउड डैशबोर्ड में सिंक होते हैं, E2E-एन्क्रिप्टेड।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेसेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI सिमेंटिक कन्वेंशन्स** का उपयोग करते हुए, ताकि आपके एजेंट ट्रेसेस कभी भी किसी एक टूल में लॉक न हों।

हर सेशन को — LLM कॉल्स, टूल्स, सब-एजेंट्स, टोकन्स, कॉस्ट — किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपका खुद का OTel Collector) को OTLP/HTTP GenAI स्पैन्स के रूप में **एक्सपोर्ट** करें:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth हेडर्स और पोल इंटरवल वैकल्पिक env वेरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर किसी भी अन्य स्रोत से ट्रेसेस और मेट्रिक्स स्वीकार करता है (protobuf इनजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फ़र्स्ट ClawMetry डैशबोर्ड **और** आपकी टीम पहले से चला रही किसी भी बैकएंड में आपका डेटा दोनों मिलते हैं — कोई लॉक-इन नहीं, इंस्टॉल करने के लिए कोई दूसरा एजेंट नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग्स, सेशंस, और क्रॉन्स को ऑटो-डिटेक्ट करता है।

अगर आपको कस्टमाइज़ करने की ज़रूरत है:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके द्वारा कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव एक्टिविटी दिखाता है। केवल वे चैनल जो वास्तव में आपके `openclaw.json` में सेट अप हैं, Flow डायग्राम में दिखाई देते हैं — अनकॉन्फ़िगर्ड चैनल ऑटोमैटिकली छिपे रहते हैं।

Flow में किसी भी चैनल नोड पर क्लिक करके इनकमिंग/आउटगोइंग मैसेज काउंट्स के साथ एक लाइव चैट बबल व्यू देखें।

| चैनल | स्टेटस | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आँकड़े, 10s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` को सीधे पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के माध्यम से |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के माध्यम से |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशंस |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के माध्यम से iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक्स के माध्यम से |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन के माध्यम से |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE मैसेजिंग API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के माध्यम से चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपका `~/.openclaw/openclaw.json` पढ़ता है और केवल उन्हीं चैनलों को रेंडर करता है जिन्हें आपने वास्तव में कॉन्फ़िगर किया है। किसी मैनुअल सेटअप की ज़रूरत नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को कंटेनर में चलाना चाहते हैं? कोई समस्या नहीं! 🐳

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

> **नोट:** Docker में चलाते समय, अपने एजेंट की डेटा + लॉग डायरेक्ट्रीज़ माउंट करें (जैसे, `~/.openclaw`, `~/.claude`, `~/.codex`) ताकि ClawMetry आपके सेटअप को ऑटो-डिटेक्ट कर सके।

## आवश्यकताएँ

- Python 3.8+
- Flask (pip के माध्यम से ऑटोमैटिकली इंस्टॉल)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, या Antigravity (या Docker के लिए माउंटेड वॉल्यूम्स)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry स्वचालित रूप से [NemoClaw](https://github.com/NVIDIA/NemoClaw) को डिटेक्ट करता है — OpenClaw के लिए NVIDIA का एंटरप्राइज़ सिक्योरिटी रैपर जो सैंडबॉक्स्ड OpenShell कंटेनरों के अंदर एजेंट्स चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक डेमन सेशन फ़ाइलों को स्वचालित रूप से खोजता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या किसी OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry दो तरीकों से NemoClaw को डिटेक्ट करता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज के लिए चल रहे Docker कंटेनरों को स्कैन करता है, फिर वॉल्यूम माउंट्स या `docker cp` के ज़रिए सेशंस पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलों को क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा से टैग किया जाता है, ताकि आप उन्हें एक नज़र में स्टैंडर्ड OpenClaw सेशंस से अलग बता सकें।

### अनुशंसित सेटअप: होस्ट पर सिंक डेमन

सबसे अच्छे अनुभव के लिए, ClawMetry का सिंक डेमन **होस्ट मशीन** पर चलाएँ (सैंडबॉक्स के अंदर नहीं)। यह NemoClaw नेटवर्क पॉलिसी प्रतिबंधों से बचाता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशंस को स्वचालित रूप से खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स पर पॉइंट करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (एडवांस्ड)

अगर आपको सिंक डेमन **OpenShell सैंडबॉक्स के अंदर** ही चलाना है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह egress नियम जोड़ें ताकि यह ClawMetry ingest API तक पहुँच सके:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

इससे लागू करें:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट्स और एंडपॉइंट्स

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | आवश्यक |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` को आउटबाउंड HTTPS कॉल्स करता है। किसी इनबाउंड पोर्ट की ज़रूरत नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल्स, रिवर्स प्रॉक्सी, और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

इस प्रोजेक्ट का परीक्षण BrowserStack के साथ किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry `https://app.clawmetry.com/api/install` को अनाम इंस्टॉल-लाइफसाइकल
पिंग भेजता है: नई मशीन पर पहली बार `clawmetry` CLI चलाने पर एक `install`
पिंग, नए वर्ज़न में अपग्रेड के बाद पहली बार चलाने पर एक `update` पिंग,
और इन-डैशबोर्ड ऑनबोर्डिंग चॉइस पूरी करने पर एक `onboarded`
पिंग। हम इसका उपयोग वास्तविक इंस्टॉल्स गिनने के लिए करते हैं (कच्चे PyPI डाउनलोड नंबर ~98% मिरर, CI,
और ऑटो-अपडेट री-डाउनलोड होते हैं) और यह जानने के लिए कि असल में कौन से एजेंट फ़्रेमवर्क और
वर्ज़न इस्तेमाल हो रहे हैं।

**प्रति लाइफसाइकल इवेंट प्रति वर्ज़न अधिकतम एक POST**, जिसमें शामिल है:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` में स्टोर किया गया रैंडम UUID | डेडुप; तब तक अनाम जब तक आप स्पष्ट रूप से Cloud sync कनेक्ट नहीं करते (उसके बाद ऑथेंटिकेटेड डेमन हार्टबीट इसे साथ ले जाता है, इस इंस्टॉल को आपके अकाउंट से लिंक करते हुए) |
| `event` | `install` / `update` / `onboarded` | फ्रेश इंस्टॉल बनाम मौजूदा का अपग्रेड |
| `version` | `0.12.167` | कौन से वर्ज़न इस्तेमाल में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म सपोर्ट प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न सपोर्ट मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट्स के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल्स को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड सर्वर-साइड रिक्वेस्ट से देश कोड निकालता है,
फिर IP को छोड़ देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस
पाथ, फ़ाइल कॉन्टेंट्स, आपकी api_key, आपकी ईमेल, कुछ भी PII या
वर्कस्पेस-विशिष्ट। वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट योग्य है।

**ऑप्ट आउट** (इनमें से कोई भी एक इसे स्थायी रूप से अक्षम कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहाँ नेटवर्क फेल्योर कभी भी `clawmetry` को चलने से नहीं रोकता — यह
पिंग एक डेमन थ्रेड पर 3s टाइमआउट के साथ फ़ायर-एंड-फ़ॉरगेट है।

## Star History

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
  <sub>निर्माता <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टम का हिस्सा</sub>
</p>
