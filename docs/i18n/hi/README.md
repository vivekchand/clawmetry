<!-- i18n-src:56ff57310588 -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** [OpenClaw](https://github.com/openclaw/openclaw) AI एजेंट्स के लिए रियल-टाइम ऑब्ज़र्वेबिलिटी।

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िग। हर चीज़ का अपने-आप पता लगा लेता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और आपका काम हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## आपको क्या मिलता है

- **Flow** — लाइव एनिमेटेड डायग्राम जो दिखाता है कि मैसेज चैनलों, ब्रेन, टूल्स और वापस होते हुए कैसे प्रवाहित होते हैं
- **Overview** — हेल्थ चेक, एक्टिविटी हीटमैप, सेशन गिनती, मॉडल जानकारी
- **Usage** — दैनिक/साप्ताहिक/मासिक विश्लेषण के साथ टोकन और लागत ट्रैकिंग
- **Sessions** — मॉडल, टोकन और आखिरी गतिविधि के साथ सक्रिय एजेंट सेशन
- **Crons** — स्थिति, अगले रन और अवधि के साथ शेड्यूल किए गए जॉब
- **Logs** — रंग-कोडेड रियल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md और दैनिक नोट्स ब्राउज़ करें
- **Transcripts** — सेशन इतिहास पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट सीमाएं, एरर-रेट ट्रिगर, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email को रूट करता है
- **Approvals** — विनाशकारी डिलीट, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल और नेटवर्क कॉल को एक-क्लिक स्वीकृति के पीछे गेट करें

## स्क्रीनशॉट

### 🧠 Brain — लाइव एजेंट इवेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन उपयोग और सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रियल-टाइम टूल कॉल फ़ीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडल और सेशन के अनुसार लागत विश्लेषण
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फ़ाइल ब्राउज़र
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पॉश्चर और ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजट सीमाएं, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email के लिए वेबहुक
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल को मैनुअल स्वीकृति के पीछे गेट करें; पॉलिसी-समर्थित सुरक्षा नियम
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

v2 React ऐप `frontend/` में रहता है और जब Flask सर्वर v2 सक्षम के साथ शुरू किया जाता है तो इसे `/v2` पर सर्व किया जाता है।

डेवलपमेंट करते समय दो टर्मिनल उपयोग करें:

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

`http://localhost:5173/v2/` खोलें। Vite `/api` अनुरोधों को `http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना किसी अतिरिक्त CORS सेटअप के लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry सिर्फ़ OpenClaw ही नहीं, बल्कि कई AI-एजेंट रनटाइम का अवलोकन करता है। प्रत्येक गैर-OpenClaw रनटाइम एक समर्पित रीडर अडैप्टर के साथ आता है जो उसके नेटिव सेशन फ़ॉर्मेट को ClawMetry के एकीकृत शेप्स में अनुवादित करता है; डेमन उन्हें उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इंजेस्ट करता है, रनटाइम के साथ टैग किया गया, और जब एक से अधिक मौजूद हों तो Session रीप्ले टैब एक **रनटाइम स्विचर** दिखाता है। पूरे मैट्रिक्स और रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-परिवार के परिचय के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

| रनटाइम / एजेंट | स्थिति | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव | संदर्भ रनटाइम, अपने-आप पहचाना गया |
| **PicoClaw** | बीटा अडैप्टर | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट, मॉडल, टूल कॉल। |
| **NanoClaw** | बीटा अडैप्टर | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट + मैसेज गिनती। |
| **Hermes** | बीटा अडैप्टर | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट, मॉडल, टोकन/लागत। |
| **Claude Code** | बीटा अडैप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल + थिंकिंग, टोकन उपयोग। |
| **Codex** | बीटा अडैप्टर | रोलआउट JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन उपयोग। |
| **Cursor** | बीटा अडैप्टर | SQLite `state.vscdb`। चैट/कंपोज़र ट्रांसक्रिप्ट, मॉडल। |
| **Aider** | बीटा अडैप्टर | प्रति प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट, मॉडल, टोकन गिनती। |
| **Goose** | बीटा अडैप्टर | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन कुल। |

"बीटा अडैप्टर" का मतलब है कि ClawMetry उस रनटाइम के असल ऑन-डिस्क फ़ॉर्मेट के लिए एक रीडर शिप करता है, प्रत्येक को असल मशीन पर असल इंस्टॉल के विरुद्ध बनाया + सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। अडैप्टर रीड-ओनली हैं; प्रत्येक इस बारे में ईमानदार है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (उदाहरण के लिए PicoClaw/NanoClaw/Cursor टोकन लागत डिस्क पर नहीं लिखते)। जब एक नोड पर कई रनटाइम चलते हैं, तो रनटाइम स्विचर एक साफ़ डीप-डाइव के लिए सेशन व्यू को एक तक सीमित कर देता है।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI सिमैंटिक कन्वेंशन** का उपयोग करते हुए, ताकि आपके एजेंट ट्रेस कभी एक टूल में लॉक न हों।

हर सेशन को OTLP/HTTP GenAI स्पैन के रूप में किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपका अपना OTel Collector) में **एक्सपोर्ट** करें: LLM कॉल, टूल, सब-एजेंट, टोकन, लागत:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर और पोल इंटरवल वैकल्पिक env वैरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इंजेस्ट** — बिल्ट-इन OTLP रिसीवर किसी भी अन्य स्रोत से `/v1/traces` और `/v1/metrics` पर ट्रेस और मेट्रिक्स स्वीकार करता है (protobuf इंजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फर्स्ट ClawMetry डैशबोर्ड **और** आपका डेटा उस बैकएंड में मिलता है जो आपकी टीम पहले से चलाती है: कोई लॉक-इन नहीं, इंस्टॉल करने के लिए कोई दूसरा एजेंट नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग, सेशन और cron का अपने-आप पता लगा लेता है।

अगर आपको कस्टमाइज़ करने की ज़रूरत है:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके द्वारा कॉन्फ़िगर किए गए हर OpenClaw चैनल की लाइव गतिविधि दिखाता है। Flow डायग्राम में केवल वही चैनल दिखते हैं जो वास्तव में आपके `openclaw.json` में सेट किए गए हैं; जो कॉन्फ़िगर नहीं हैं वे अपने-आप छिप जाते हैं।

लाइव चैट बबल व्यू देखने के लिए Flow में किसी भी चैनल नोड पर क्लिक करें, जिसमें इनकमिंग/आउटगोइंग मैसेज की गिनती होती है।

| चैनल | स्थिति | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मैसेज, आंकड़े, 10s रिफ़्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` को सीधे पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के ज़रिए |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के ज़रिए |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | Guild + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के ज़रिए iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक के ज़रिए |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन के ज़रिए |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DM |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के ज़रिए चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपके `~/.openclaw/openclaw.json` को पढ़ता है और केवल उन्हीं चैनलों को रेंडर करता है जिन्हें आपने वास्तव में कॉन्फ़िगर किया है। किसी मैनुअल सेटअप की ज़रूरत नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को किसी कंटेनर में चलाना चाहते हैं? कोई समस्या नहीं! 🐳

**Docker के साथ क्विक स्टार्ट:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **नोट:** Docker में चलाते समय, सुनिश्चित करें कि आप अपना OpenClaw वर्कस्पेस और लॉग डायरेक्टरी माउंट करें ताकि ClawMetry आपके सेटअप का अपने-आप पता लगा सके।

## आवश्यकताएं

- Python 3.8+
- Flask (pip के ज़रिए अपने-आप इंस्टॉल हो जाता है)
- उसी मशीन पर चल रहा OpenClaw (या Docker के लिए माउंट किए गए वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry अपने-आप [NemoClaw](https://github.com/NVIDIA/NemoClaw) का पता लगा लेता है, जो OpenClaw के लिए NVIDIA का एंटरप्राइज़ सिक्योरिटी रैपर है और एजेंट्स को सैंडबॉक्स्ड OpenShell कंटेनरों के अंदर चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं होती। सिंक डेमन सेशन फ़ाइलों को अपने-आप खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या किसी OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry NemoClaw का दो तरीकों से पता लगाता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जांच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — चल रहे Docker कंटेनरों में `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज को स्कैन करता है, फिर वॉल्यूम माउंट या `docker cp` के ज़रिए सेशन पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलों को क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा के साथ टैग किया जाता है, ताकि आप उन्हें एक नज़र में मानक OpenClaw सेशन से अलग बता सकें।

### अनुशंसित सेटअप: HOST पर सिंक डेमन

सर्वोत्तम अनुभव के लिए, ClawMetry के सिंक डेमन को **होस्ट मशीन** पर चलाएं (सैंडबॉक्स के अंदर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी प्रतिबंधों से बचा जा सकता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशन अपने-आप ढूंढ लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स की ओर इंगित करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (एडवांस्ड)

अगर आपको सिंक डेमन को OpenShell सैंडबॉक्स के **अंदर** चलाना ही है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह एग्रेस नियम जोड़ें ताकि वह ClawMetry इंजेस्ट API तक पहुंच सके:

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
| `ingest.clawmetry.com` | 443 | HTTPS | हां (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हां (लोकल डैशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` पर आउटबाउंड HTTPS कॉल करता है। किसी इनबाउंड पोर्ट की आवश्यकता नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

इस प्रोजेक्ट का परीक्षण BrowserStack के साथ किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry किसी नई मशीन पर पहली बार `clawmetry` CLI चलाने पर `https://app.clawmetry.com/api/install` को एक एकल अनाम "first run" पिंग भेजता है। हम इसका उपयोग इंस्टॉल गिनने के लिए करते हैं (किसी OSS प्रोजेक्ट के लिए हमारे पास यही एकमात्र मार्केटिंग मेट्रिक है) और यह जानने के लिए कि हमारे उपयोगकर्ताओं ने कौन-से एजेंट फ्रेमवर्क इंस्टॉल किए हैं।

**प्रति इंस्टॉल ठीक एक POST**, जिसमें होता है:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर संग्रहीत रैंडम UUID | डीडुप; आपके ईमेल या api_key से जुड़ा नहीं |
| `version` | `0.12.167` | कौन-से संस्करण उपयोग में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएं |
| `python` | `3.11.15` | Python संस्करण समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट्स के साथ एकीकृत होना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड अनुरोध से सर्वर-साइड पर देश कोड निकालता है, फिर IP को त्याग देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस पथ, फ़ाइल सामग्री, आपका api_key, आपका ईमेल, या कोई भी PII या वर्कस्पेस-विशिष्ट चीज़। वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट किया जा सकता है।

**ऑप्ट आउट करें** (इनमें से कोई भी एक इसे स्थायी रूप से अक्षम कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहां कोई नेटवर्क विफलता `clawmetry` को चलने से कभी नहीं रोकती: यह पिंग 3 s टाइमआउट के साथ एक डेमन थ्रेड पर फ़ायर-एंड-फ़ॉरगेट है।

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
  <strong>🦞 See your agent think</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
