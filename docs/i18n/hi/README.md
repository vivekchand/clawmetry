<!-- i18n-src:48548997be76 -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **12 AI एजेंट रनटाइम** के लिए रियल-टाइम ऑब्जर्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 8 अन्य। आपके पूरे एजेंट बेड़े के लिए एक डैशबोर्ड।

> 🌐 **इसे इसमें पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ स्वचालित रूप से पहचानता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और बस हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 एजेंट रनटाइम के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्जर्वेबिलिटी के रूप में हुई थी, और अब यह एक ही डैशबोर्ड में आपके **पूरे एजेंट बेड़े** को मापता है, आपकी मशीन पर प्रत्येक रनटाइम को स्वचालित रूप से पहचानता है:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; अन्य रनटाइम ClawMetry Cloud या सेल्फ-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें और हर टैब — लागत, टोकन, टूल, ट्रेस — उस रनटाइम के अनुसार फिर से स्कोप हो जाता है।

## आपको क्या मिलता है

- **Flow** — लाइव एनिमेटेड डायग्राम जो चैनल, ब्रेन, टूल और वापस से बहते संदेशों को दिखाता है
- **Overview** — हेल्थ चेक, एक्टिविटी हीटमैप, सेशन काउंट, मॉडल जानकारी
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउन के साथ टोकन और लागत ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम गतिविधि सहित सक्रिय एजेंट सेशन
- **Crons** — स्थिति, अगली रन, अवधि सहित शेड्यूल किए गए जॉब
- **Logs** — रंग-कोडेड रियल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउज़ करें
- **Transcripts** — सेशन इतिहास पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप, एरर-रेट ट्रिगर, एजेंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर रूट करता है
- **Approvals** — विनाशकारी डिलीट, फोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल को वन-क्लिक साइन-ऑफ के पीछे गेट करें

## स्क्रीनशॉट

### 🧠 Brain — लाइव एजेंट इवेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन उपयोग और सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रियल-टाइम टूल कॉल फ़ीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडल और सेशन के अनुसार लागत ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फ़ाइल ब्राउज़र
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोस्चर और ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजट कैप, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email पर वेबहुक
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल को मैनुअल साइन-ऑफ के पीछे गेट करें; पॉलिसी-समर्थित सुरक्षा नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## v2 फ्रंटेंड डेवलपमेंट

v2 React ऐप `frontend/` में है और Flask सर्वर को v2 सक्षम के साथ शुरू करने पर `/v2` पर सर्व किया जाता है।

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

`http://localhost:5173/v2/` खोलें। Vite `/api` अनुरोधों को `http://localhost:8900` पर प्रॉक्सी करता है, इसलिए React ऐप बिना अतिरिक्त CORS सेटअप के लोकल Flask सर्वर से बात कर सकता है।

Python पैकेज के साथ शिप होने वाला बंडल बिल्ड करने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry केवल OpenClaw नहीं, बल्कि कई AI-एजेंट रनटाइम को ऑब्जर्व करता है। प्रत्येक गैर-OpenClaw रनटाइम एक समर्पित रीडर एडेप्टर के साथ आता है जो उसके नेटिव सेशन फॉर्मेट को ClawMetry के यूनिफाइड शेप में अनुवादित करता है; डेमन उन्हें रनटाइम के साथ टैग करके उसी DuckDB स्टोर और क्लाउड स्नैपशॉट में इनजेस्ट करता है, और जब एक से अधिक रनटाइम मौजूद हों तो Session रिप्ले टैब एक **रनटाइम स्विचर** दिखाता है। पूर्ण मैट्रिक्स और रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-फैमिली प्राइमर के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

| रनटाइम / एजेंट | स्थिति | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव | रेफरेंस रनटाइम, स्वचालित रूप से पहचाना जाता है |
| **PicoClaw** | बीटा एडेप्टर | फ्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट, मॉडल, टूल कॉल। |
| **NanoClaw** | बीटा एडेप्टर | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट और मेसेज काउंट। |
| **Hermes** | बीटा एडेप्टर | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट, मॉडल, टोकन/लागत। |
| **Claude Code** | बीटा एडेप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल और थिंकिंग, टोकन उपयोग। |
| **Codex** | बीटा एडेप्टर | रोलआउट JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन उपयोग। |
| **Cursor** | बीटा एडेप्टर | SQLite `state.vscdb`। चैट/कंपोजर ट्रांसक्रिप्ट, मॉडल। |
| **Aider** | बीटा एडेप्टर | प्रति प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट, मॉडल, टोकन काउंट। |
| **Goose** | बीटा एडेप्टर | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन टोटल। |
| **opencode** | बीटा एडेप्टर | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन और लागत। |
| **Qwen Code** | बीटा एडेप्टर | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन उपयोग। |

"बीटा एडेप्टर" का मतलब है कि ClawMetry उस रनटाइम के असली ऑन-डिस्क फॉर्मेट के लिए एक रीडर शिप करता है, प्रत्येक को एक असली मशीन पर असली इंस्टॉल के विरुद्ध बिल्ड और वेरिफाई किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। एडेप्टर केवल पढ़ने के लिए हैं; प्रत्येक इस बारे में ईमानदार है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (उदा. PicoClaw/NanoClaw/Cursor डिस्क पर टोकन लागत नहीं लिखते)। जब एक नोड पर कई रनटाइम चलते हैं, तो रनटाइम स्विचर क्लीन डीप-डाइव के लिए सेशन व्यू को एक तक स्कोप करता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट एट्रिब्यूशन

ऊपर के रनटाइम सभी डिस्क पर सेशन लिखते हैं। आपका खुद का **प्रोडक्शन एजेंट** — जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक सादे `httpx` लूप पर बनाया है — नहीं लिखता। ClawMetry का जीरो-कॉन्फिग इंटरसेप्टर फिर भी `httpx`/`requests` को मंकी-पैच करके उसके LLM कॉल (लागत, टोकन, लेटेंसी, एरर) कैप्चर करता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` एनव वेरिएबल) प्रत्येक कॉल को एक **नामित स्रोत** के साथ टैग करता है, इसलिए आप जो भी प्रोडक्ट चलाते हैं वह डैशबोर्ड के **🔌 Out-loop sources** कार्ड में Overview पर अपनी खुद की पहली श्रेणी, कॉस्ट-एट्रिब्यूटेबल लाइन के रूप में दिखता है — प्रति एजेंट कॉल, प्रोवाइडर, लेटेंसी, एरर रेट। कोई स्रोत सेट नहीं? कॉल फिर भी ट्रैक होते हैं; कार्ड बस छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जिसे रनटाइम एडेप्टर फीड करते हैं (DuckDB क्लाउड स्नैपशॉट), इसलिए आउट-लूप स्रोत बाकी सब चीज़ों की तरह क्लाउड डैशबोर्ड में सिंक होते हैं, E2E-एन्क्रिप्टेड।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry **GenAI सिमेंटिक कन्वेंशन** का उपयोग करते हुए दोनों दिशाओं में **OpenTelemetry** बोलता है, इसलिए आपके एजेंट ट्रेस कभी एक टूल में लॉक नहीं होते।

**एक्सपोर्ट** करें हर सेशन — LLM कॉल, टूल, सब-एजेंट, टोकन, लागत — किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपके खुद के OTel Collector) को OTLP/HTTP GenAI स्पैन के रूप में:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर और पोल इंटर्वल वैकल्पिक एनव वेरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर किसी भी अन्य चीज़ से ट्रेस और मेट्रिक्स स्वीकार करता है (प्रोटोबफ इनजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको जीरो-कॉन्फिग, लोकल-फर्स्ट ClawMetry डैशबोर्ड **और** जो भी बैकेंड आपकी टीम पहले से चला रही है उसमें आपका डेटा मिलता है — कोई लॉक-इन नहीं, इंस्टॉल करने के लिए कोई दूसरा एजेंट नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग, सेशन और crons को स्वचालित रूप से पहचानता है।

यदि आपको कस्टमाइज़ करने की ज़रूरत हो:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव एक्टिविटी दिखाता है। केवल वे चैनल जो आपके `openclaw.json` में वास्तव में सेटअप हैं, Flow डायग्राम में दिखाई देते हैं — बिना कॉन्फ़िगर किए गए चैनल स्वचालित रूप से छिपा दिए जाते हैं।

Flow में किसी चैनल नोड पर क्लिक करें तो आने/जाने वाले मेसेज काउंट के साथ लाइव चैट बबल व्यू मिलता है।

| चैनल | स्थिति | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आंकड़े, 10 सेकंड रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` सीधे पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के माध्यम से |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के माध्यम से |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | Guild और चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस और चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के माध्यम से iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक के माध्यम से |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन के माध्यम से |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के माध्यम से चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **स्वचालित पहचान:** ClawMetry आपका `~/.openclaw/openclaw.json` पढ़ता है और केवल उन्हीं चैनलों को रेंडर करता है जो आपने वास्तव में कॉन्फ़िगर किए हैं। कोई मैनुअल सेटअप आवश्यक नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को एक कंटेनर में चलाना चाहते हैं? कोई समस्या नहीं! 🐳

**Docker के साथ त्वरित शुरुआत:**

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

> **नोट:** Docker में चलाते समय, अपने एजेंट के डेटा और लॉग डायरेक्टरी (जैसे `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करें ताकि ClawMetry आपका सेटअप स्वचालित रूप से पहचान सके।

## आवश्यकताएं

- Python 3.8+
- Flask (pip के माध्यम से स्वचालित रूप से इंस्टॉल)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, या PicoClaw (या Docker के लिए माउंटेड वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry स्वचालित रूप से [NemoClaw](https://github.com/NVIDIA/NemoClaw) का पता लगाता है — NVIDIA का एंटरप्राइज़ सिक्योरिटी रैपर जो OpenClaw के लिए सैंडबॉक्स्ड OpenShell कंटेनर के अंदर एजेंट चलाता है।

अधिकांश मामलों में कोई अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक डेमन सेशन फाइल स्वचालित रूप से खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry दो तरीकों से NemoClaw का पता लगाता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जांच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज के लिए चल रहे Docker कंटेनर स्कैन करता है, फिर वॉल्यूम माउंट या `docker cp` के माध्यम से सेशन पढ़ता है

NemoClaw कंटेनर से सिंक की गई सेशन फाइलों को क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा के साथ टैग किया जाता है, ताकि आप उन्हें एक नज़र में मानक OpenClaw सेशन से अलग पहचान सकें।

### अनुशंसित सेटअप: होस्ट पर सिंक डेमन

सबसे अच्छे अनुभव के लिए, ClawMetry का सिंक डेमन **होस्ट मशीन** पर चलाएं (सैंडबॉक्स के अंदर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी प्रतिबंधों से बचा जाता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशन स्वचालित रूप से खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

यदि स्वचालित पहचान काम नहीं करती, तो ClawMetry को सही सैंडबॉक्स की ओर इंगित करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (उन्नत)

यदि आपको सिंक डेमन **OpenShell सैंडबॉक्स के अंदर** चलाना है, तो इस एग्रेस नियम को अपनी NemoClaw नेटवर्क पॉलिसी में जोड़ें ताकि यह ClawMetry इनजेस्ट API तक पहुंच सके:

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

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | आवश्यक |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डेमन क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` पर आउटबाउंड HTTPS कॉल करता है। कोई इनबाउंड पोर्ट की आवश्यकता नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## परीक्षण

इस प्रोजेक्ट का परीक्षण BrowserStack के साथ किया गया है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry एक नई मशीन पर पहली बार `clawmetry` CLI चलाने पर एक बार एक अनाम "पहली बार रन" पिंग `https://app.clawmetry.com/api/install` पर भेजता है। हम इसका उपयोग इंस्टॉल गिनने के लिए (एक OSS प्रोजेक्ट के लिए हमारे पास एकमात्र मार्केटिंग मेट्रिक) और यह जानने के लिए करते हैं कि हमारे उपयोगकर्ताओं ने कौन से एजेंट फ्रेमवर्क इंस्टॉल किए हैं।

**प्रति इंस्टॉल बिल्कुल एक POST**, जिसमें:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर संग्रहीत रैंडम UUID | डुप्लिकेट हटाना; आपके ईमेल या api_key से नहीं जुड़ा |
| `version` | `0.12.167` | कौन से वर्शन उपयोग में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएं |
| `python` | `3.11.15` | Python वर्शन समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड सर्वर-साइड पर अनुरोध से देश कोड प्राप्त करता है, फिर IP हटा देता है), होस्टनाम, उपयोगकर्ता नाम, वर्कस्पेस पथ, फ़ाइल सामग्री, आपका api_key, आपका ईमेल, कोई भी PII या वर्कस्पेस-विशिष्ट जानकारी। वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट योग्य है।

**ऑप्ट आउट** (इनमें से कोई भी एक इसे स्थायी रूप से अक्षम करता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहाँ नेटवर्क विफलता कभी `clawmetry` को चलने से नहीं रोकती — पिंग 3 सेकंड टाइमआउट के साथ एक डेमन थ्रेड पर फायर-एंड-फॉरगेट है।

## Star इतिहास

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
  <sub>निर्मित <a href="https://github.com/vivekchand">@vivekchand</a> द्वारा · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टम का हिस्सा</sub>
</p>
