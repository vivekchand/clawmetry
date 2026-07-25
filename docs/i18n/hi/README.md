<!-- i18n-src:8f42d460a973 -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **14 AI एजेंट रनटाइम** के लिए रियल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 10 अन्य। आपके पूरे एजेंट फ्लीट के लिए एक ही डैशबोर्ड।

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और भाषाएं →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ अपने आप डिटेक्ट हो जाता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और बस, आपका काम हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजेंट रनटाइम के साथ काम करता है

ClawMetry की शुरुआत OpenClaw की ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह एक ही डैशबोर्ड में आपके **पूरे एजेंट फ्लीट** को मीटर करता है, आपकी मशीन पर हर रनटाइम को अपने आप डिटेक्ट करते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम ClawMetry Cloud या सेल्फ-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें और हर टैब — कॉस्ट, टोकन, टूल्स, ट्रेसेज़ — उस रनटाइम पर फिर से स्कोप हो जाता है। सटीक मुफ़्त/पेड विभाजन, टियर मैट्रिक्स, `/api/entitlement` शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow** — चैनलों, ब्रेन, टूल्स और वापस होकर बहते संदेशों को दिखाने वाला लाइव एनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक, एक्टिविटी हीटमैप, सेशन काउंट, मॉडल जानकारी
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम एक्टिविटी के साथ सक्रिय एजेंट सेशन
- **Crons** — स्टेटस, अगली रन, अवधि के साथ शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रियल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउज़ करें
- **Transcripts** — सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप, एरर-रेट ट्रिगर, एजेंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर भेजता है
- **Approvals** — डिस्ट्रक्टिव डिलीट, फोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल्स को एक-क्लिक साइन-ऑफ के पीछे गेट करें

## स्क्रीनशॉट

### 🧠 Brain — लाइव एजेंट इवेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन उपयोग और सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रियल-टाइम टूल कॉल फ़ीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडल और सेशन के अनुसार कॉस्ट ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फ़ाइल ब्राउज़र
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोस्चर और ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजट कैप, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email को वेबहुक
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल्स को मैनुअल साइन-ऑफ के पीछे गेट करें; पॉलिसी-समर्थित सुरक्षा नियम
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

## v2 फ्रंटएंड डेवलपमेंट

v2 React ऐप `frontend/` में रहता है और जब Flask सर्वर v2 सक्षम के साथ शुरू किया जाता है
तो यह `/v2` पर सर्व होता है।

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

`http://localhost:5173/v2/` खोलें। Vite `/api` अनुरोधों को
`http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना किसी अतिरिक्त
CORS सेटअप के लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry कई AI-एजेंट रनटाइम को ऑब्ज़र्व करता है, न कि सिर्फ़ OpenClaw को। हर गैर-OpenClaw रनटाइम एक समर्पित रीडर एडाप्टर शिप करता है जो उसके नेटिव सेशन फॉर्मेट को ClawMetry के यूनिफाइड शेप में बदलता है; डेमन उन्हें उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इनजेस्ट करता है, रनटाइम के साथ टैग करके, और Session replay टैब एक से अधिक रनटाइम मौजूद होने पर एक **रनटाइम स्विचर** दिखाता है। पूरे मैट्रिक्स + नए रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-फैमिली प्राइमर के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

| रनटाइम / एजेंट | स्थिति | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव | संदर्भ रनटाइम, ऑटो-डिटेक्टेड |
| **PicoClaw** | बीटा एडाप्टर | फ्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट, मॉडल, टूल कॉल्स। |
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

"बीटा एडाप्टर" का मतलब है कि ClawMetry उस रनटाइम के वास्तविक ऑन-डिस्क फॉर्मेट के लिए एक रीडर शिप करता है, जो हर एक असली मशीन पर असली इंस्टॉल के विरुद्ध बनाया और सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। एडाप्टर रीड-ओनली हैं; हर एक इस बारे में ईमानदार है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (जैसे, PicoClaw/NanoClaw/Cursor डिस्क पर टोकन कॉस्ट नहीं लिखते)। जब एक नोड पर कई रनटाइम चल रहे हों, तो रनटाइम स्विचर सेशन व्यू को एक साफ़ डीप-डाइव के लिए एक रनटाइम तक सीमित कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट एट्रिब्यूशन

ऊपर दिए गए सभी रनटाइम सेशन को डिस्क पर लिखते हैं। आपका अपना **प्रोडक्शन एजेंट** — वह जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक साधारण `httpx` लूप पर बनाया है — ऐसा नहीं करता। ClawMetry का ज़ीरो-कॉन्फ़िग इंटरसेप्टर फिर भी `httpx`/`requests` को मंकी-पैच करके इसके LLM कॉल्स (कॉस्ट, टोकन, लेटेंसी, एरर) को कैप्चर करता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` एनवायरनमेंट वेरिएबल) हर कॉल को एक **नामित सोर्स** के साथ टैग करता है, ताकि आप जो भी प्रोडक्ट चलाते हैं वह डैशबोर्ड के Overview पर मौजूद **🔌 Out-loop sources** कार्ड में अपनी खुद की, फर्स्ट-क्लास, कॉस्ट-एट्रिब्यूटेबल लाइन के रूप में दिखे — प्रति एजेंट कॉल्स, प्रोवाइडर, लेटेंसी, एरर रेट। कोई सोर्स सेट नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; बस कार्ड छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जिसे रनटाइम एडाप्टर फीड करते हैं (DuckDB → क्लाउड स्नैपशॉट), इसलिए आउट-लूप सोर्स बाकी सब कुछ की तरह ही क्लाउड डैशबोर्ड पर सिंक होते हैं, एंड-टू-एंड एन्क्रिप्टेड।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI सिमेंटिक कन्वेंशन** का उपयोग करते हुए, ताकि आपके एजेंट ट्रेस कभी भी एक टूल में लॉक न हों।

हर सेशन — LLM कॉल्स, टूल्स, सब-एजेंट, टोकन, कॉस्ट — को किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपका अपना OTel Collector) पर OTLP/HTTP GenAI स्पैन के रूप में **एक्सपोर्ट** करें:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर और पोल इंटरवल वैकल्पिक एनवायरनमेंट वेरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर किसी भी अन्य स्रोत से ट्रेस और मेट्रिक्स स्वीकार करता है (प्रोटोबफ़ इनजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फर्स्ट ClawMetry डैशबोर्ड **और** आपकी टीम पहले से जो भी बैकएंड चलाती है उसमें आपका डेटा मिलता है — कोई लॉक-इन नहीं, कोई दूसरा एजेंट इंस्टॉल करने की ज़रूरत नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग, सेशन और क्रॉन को अपने आप डिटेक्ट कर लेता है।

अगर आपको कस्टमाइज़ करने की ज़रूरत है:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके द्वारा कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव एक्टिविटी दिखाता है। केवल वे चैनल जो वास्तव में आपके `openclaw.json` में सेट अप हैं, Flow डायग्राम में दिखाई देते हैं — जो कॉन्फ़िगर नहीं हैं वे अपने आप छिप जाते हैं।

Flow में किसी भी चैनल नोड पर क्लिक करके इनकमिंग/आउटगोइंग मैसेज काउंट के साथ लाइव चैट बबल व्यू देखें।

| चैनल | स्थिति | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आँकड़े, 10s रिफ्रेश |
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
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE मैसेजिंग API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DM |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के ज़रिए चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपकी `~/.openclaw/openclaw.json` पढ़ता है और केवल उन्हीं चैनलों को रेंडर करता है जिन्हें आपने वास्तव में कॉन्फ़िगर किया है। किसी मैनुअल सेटअप की ज़रूरत नहीं है।

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

> **नोट:** Docker में चलाते समय, अपने एजेंट की डेटा + लॉग डायरेक्टरी (जैसे `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करें ताकि ClawMetry आपके सेटअप को अपने आप डिटेक्ट कर सके।

## आवश्यकताएँ

- Python 3.8+
- Flask (pip के ज़रिए अपने आप इंस्टॉल हो जाता है)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, या Deep Agents (या Docker के लिए माउंटेड वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) को अपने आप डिटेक्ट करता है — यह NVIDIA का एंटरप्राइज़ सुरक्षा रैपर है जो OpenClaw के लिए है और सैंडबॉक्स्ड OpenShell कंटेनरों के अंदर एजेंट चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक डेमन सेशन फ़ाइलों को अपने आप खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry NemoClaw को दो तरीकों से डिटेक्ट करता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — चल रहे Docker कंटेनरों को `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज के लिए स्कैन करता है, फिर वॉल्यूम माउंट या `docker cp` के ज़रिए सेशन पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलें क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा के साथ टैग की जाती हैं, ताकि आप उन्हें एक नज़र में स्टैंडर्ड OpenClaw सेशन से अलग बता सकें।

### अनुशंसित सेटअप: होस्ट पर सिंक डेमन

बेहतर अनुभव के लिए, ClawMetry के सिंक डेमन को **होस्ट मशीन** पर चलाएँ (सैंडबॉक्स के अंदर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी प्रतिबंधों से बचा जा सकता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशन को अपने आप खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स की ओर इशारा करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (एडवांस्ड)

अगर आपको सिंक डेमन **सैंडबॉक्स के अंदर** OpenShell में चलाना ही है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह एग्रेस नियम जोड़ें ताकि यह ClawMetry इनजेस्ट API तक पहुँच सके:

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
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` को आउटबाउंड HTTPS कॉल करता है। कोई इनबाउंड पोर्ट आवश्यक नहीं है।

---

## Cloud डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

इस प्रोजेक्ट का परीक्षण BrowserStack के साथ किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry नई मशीन पर पहली बार `clawmetry` CLI चलाने पर
`https://app.clawmetry.com/api/install` पर एक अनाम "फर्स्ट रन" पिंग
भेजता है। हम इसका उपयोग इंस्टॉल गिनने के लिए करते हैं (एक ओपन-सोर्स
प्रोजेक्ट के लिए हमारे पास यही एकमात्र मार्केटिंग मेट्रिक है) और यह जानने
के लिए कि हमारे उपयोगकर्ताओं ने कौन-से एजेंट फ्रेमवर्क इंस्टॉल कर रखे हैं।

**प्रति इंस्टॉल बिल्कुल एक POST**, जिसमें शामिल है:

| फ़ील्ड | उदाहरण | कारण |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर स्टोर की गई रैंडम UUID | डिडुप; आपके ईमेल या api_key से लिंक नहीं |
| `version` | `0.12.167` | कौन-से वर्ज़न इस्तेमाल में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट्स के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | ह्यूमन इंस्टॉल को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड रिक्वेस्ट से सर्वर-साइड पर देश कोड
निकालता है, फिर IP को त्याग देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस
पाथ, फ़ाइल कंटेंट, आपकी api_key, आपका ईमेल, कुछ भी PII या
वर्कस्पेस-विशिष्ट। वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट करने योग्य है।

**ऑप्ट आउट करें** (इनमें से कोई भी एक इसे स्थायी रूप से बंद कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

नेटवर्क विफलता यहाँ कभी भी `clawmetry` को चलने से नहीं रोकती — पिंग
डेमन थ्रेड पर 3s टाइमआउट के साथ फायर-एंड-फॉरगेट है।

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
  <sub>निर्माता <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टम का हिस्सा</sub>
</p>
