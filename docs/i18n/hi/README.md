<!-- i18n-src:0e34918f8f2e -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **14 AI एजेंट रनटाइम्स** के लिए रियल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 10 और। आपके पूरे एजेंट फ्लीट के लिए एक डैशबोर्ड।

> 🌐 **इसे पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िग। सब कुछ ऑटो-डिटेक्ट होता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और आपका काम हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजेंट रनटाइम्स के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह आपके **पूरे एजेंट फ्लीट** को एक ही डैशबोर्ड में मापता है, आपकी मशीन पर हर रनटाइम को ऑटो-डिटेक्ट करते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम्स ClawMetry Cloud या सेल्फ़-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें और हर टैब — कॉस्ट, टोकन, टूल्स, ट्रेस — उस रनटाइम के अनुसार फिर से स्कोप हो जाता है। सटीक मुफ़्त/पेड विभाजन, टियर मैट्रिक्स, `/api/entitlement` शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow** — एक लाइव एनिमेटेड डायग्राम जो चैनलों, ब्रेन, टूल्स और वापस के बीच बहते मैसेजों को दिखाता है
- **Overview** — हेल्थ चेक्स, एक्टिविटी हीटमैप, सेशन काउंट्स, मॉडल जानकारी
- **Usage** — डेली/वीकली/मंथली ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम गतिविधि के साथ सक्रिय एजेंट सेशन
- **Crons** — स्टेटस, अगला रन, अवधि के साथ शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रियल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, डेली नोट्स ब्राउज़ करें
- **Transcripts** — सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप्स, एरर-रेट ट्रिगर्स, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर रूट करता है
- **Approvals** — विनाशकारी डिलीट्स, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल्स को एक-क्लिक साइन-ऑफ़ के पीछे गेट करें

## स्क्रीनशॉट्स

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

### 🚨 Alerts — बजट कैप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email के लिए वेबहुक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल्स को मैन्युअल साइन-ऑफ़ के पीछे गेट करें; पॉलिसी-समर्थित प्रोटेक्शन नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code के लिए प्री-एक्ज़ीक्यूशन ब्लॉकिंग** — एक कमांड एक
PreToolUse हुक इंस्टॉल करता है जो मैच होने वाले टूल कॉल्स को चलने से *पहले* रोकता है और आपके निर्णय
की प्रतीक्षा करता है ([क्लाउड पुश नोटिफिकेशन](https://app.clawmetry.com/push) सक्षम होने पर
आपके फ़ोन से एक टैप):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक डिनाय सिर्फ़ उस एक टूल कॉल को ब्लॉक करता है — एजेंट अपना सेशन बनाए रखता है और
कोई और तरीका आज़मा सकता है। अपने फ़ोन पर अप्रूव करना Claude Code के अपने
परमिशन प्रॉम्प्ट को स्किप कर देता है (आपने पहले ही जवाब दे दिया है)। अनमैच्ड टूल्स की लागत ~40ms होती है और
वे Claude Code के सामान्य परमिशन फ़्लो में फ़ॉल थ्रू हो जाते हैं। जब Claude Code खुद आपकी
प्रतीक्षा कर रहा हो (`permission_prompt` / `idle_prompt` नोटिफिकेशन) तब भी आपको फ़ोन पुश मिलता है।

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
सर्वर को v2 सक्षम करके शुरू किया जाता है तो यह `/v2` पर सर्व होता है।

डेवलपमेंट करते समय दो टर्मिनल का उपयोग करें:

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
`http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना अतिरिक्त CORS सेटअप के
लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry सिर्फ़ OpenClaw ही नहीं, बल्कि कई AI-एजेंट रनटाइम्स को ऑब्ज़र्व करता है। हर गैर-OpenClaw रनटाइम एक समर्पित रीडर अडैप्टर शिप करता है जो उसके नेटिव सेशन फ़ॉर्मैट को ClawMetry के यूनिफ़ाइड शेप्स में बदलता है; डीमन उन्हें उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इनजेस्ट करता है, रनटाइम के साथ टैग करके, और Session replay टैब जब एक से ज़्यादा रनटाइम मौजूद होते हैं तो एक **रनटाइम स्विचर** दिखाता है। पूरे मैट्रिक्स + रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) और OpenClaw-फ़ैमिली प्राइमर के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

[Perplexity का numbat](https://github.com/perplexityai/numbat) एजेंट-सिक्योरिटी टूल चला रहे हैं? ClawMetry इसके फ़ाइंडिंग्स और एनफ़ोर्समेंट निर्णयों को बिना किसी अतिरिक्त कॉन्फ़िगरेशन के इनजेस्ट करता है — देखें [`docs/NUMBAT.md`](docs/NUMBAT.md)।

| Runtime / Agent | स्थिति | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव | संदर्भ रनटाइम, ऑटो-डिटेक्टेड |
| **PicoClaw** | बीटा अडैप्टर | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स। |
| **NanoClaw** | बीटा अडैप्टर | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट्स + मैसेज काउंट्स। |
| **Hermes** | बीटा अडैप्टर | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट्स, मॉडल, टोकन/कॉस्ट। |
| **Claude Code** | बीटा अडैप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स + थिंकिंग, टोकन उपयोग। |
| **Codex** | बीटा अडैप्टर | रोलआउट JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Cursor** | बीटा अडैप्टर | SQLite `state.vscdb`। चैट/कम्पोज़र ट्रांसक्रिप्ट्स, मॉडल। |
| **Aider** | बीटा अडैप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट्स, मॉडल, टोकन काउंट्स। |
| **Goose** | बीटा अडैप्टर | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन टोटल्स। |
| **opencode** | बीटा अडैप्टर | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Qwen Code** | बीटा अडैप्टर | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Pi** | बीटा अडैप्टर | JSONL `~/.pi/agent/sessions`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Deep Agents** | बीटा अडैप्टर | SQLite `~/.deepagents/.state/sessions.db`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **n8n** | बीटा अडैप्टर | SQLite `~/.n8n/database.sqlite`। वर्कफ़्लो एक्ज़ीक्यूशन, नोड रन, AI Agent प्रॉम्प्ट्स, मॉडल + टोकन जहाँ n8n उन्हें रिकॉर्ड करता है। |
| **Antigravity** | बीटा अडैप्टर | `~/.gemini/<flavor>/brain/` के तहत ब्रेन JSONL। कन्वर्सेशन्स, टूल स्टेप्स, थिंकिंग, प्रति-जेनरेशन Gemini टोकन विभाजन + कॉस्ट, बैकग्राउंड-जेनरेशन बर्न। |
| **GitHub Copilot** | बीटा अडैप्टर | `~/.copilot/session-state/` के तहत Copilot CLI का `events.jsonl` + प्रति-कॉल उपयोग लेजर `session-store.db`। कन्वर्सेशन्स, टूल कॉल्स, मॉडल राउटिंग, कैश-अवेयर टोकन विभाजन, वेंडर-बिल्ड AI-क्रेडिट कॉस्ट। |

"बीटा अडैप्टर" का मतलब है कि ClawMetry उस रनटाइम के वास्तविक ऑन-डिस्क फ़ॉर्मैट के लिए एक रीडर शिप करता है, जिसे एक वास्तविक मशीन पर वास्तविक इंस्टॉल के विरुद्ध बनाया और सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। अडैप्टर्स रीड-ओनली हैं; हर एक इस बारे में ईमानदार है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (जैसे PicoClaw/NanoClaw/Cursor डिस्क पर टोकन कॉस्ट नहीं लिखते)। जब एक नोड पर कई रनटाइम्स चलते हैं, तो रनटाइम स्विचर सेशन व्यू को साफ़ डीप-डाइव के लिए एक तक स्कोप कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट अट्रिब्यूशन

ऊपर के सभी रनटाइम्स सेशन को डिस्क पर लिखते हैं। आपका खुद का **प्रोडक्शन एजेंट** — जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक साधारण `httpx` लूप पर बनाया है — ऐसा नहीं करता। ClawMetry का ज़ीरो-कॉन्फ़िग इंटरसेप्टर `httpx`/`requests` को मंकी-पैच करके उसकी LLM कॉल्स (कॉस्ट, टोकन, लेटेंसी, एरर्स) को फिर भी कैप्चर करता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` env वेरिएबल) हर कॉल को एक **नामित सोर्स** से टैग करता है, ताकि आपके द्वारा चलाया गया हर प्रोडक्ट डैशबोर्ड के Overview पर **🔌 Out-loop sources** कार्ड में अपनी खुद की, फ़र्स्ट-क्लास, कॉस्ट-अट्रिब्यूटेबल लाइन के रूप में दिखे — प्रति एजेंट कॉल्स, प्रोवाइडर्स, लेटेंसी, एरर रेट। कोई सोर्स सेट नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; कार्ड बस छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जिसे रनटाइम अडैप्टर्स फ़ीड करते हैं (DuckDB → क्लाउड स्नैपशॉट), इसलिए आउट-लूप सोर्स बाकी सब कुछ की तरह ही क्लाउड डैशबोर्ड से सिंक होते हैं, E2E-एन्क्रिप्टेड।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI सिमैंटिक कन्वेंशन्स** का उपयोग करते हुए, ताकि आपके एजेंट ट्रेस कभी भी एक टूल में लॉक न हों।

हर सेशन को — LLM कॉल्स, टूल्स, सब-एजेंट्स, टोकन, कॉस्ट — किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपका अपना OTel Collector) को OTLP/HTTP GenAI स्पैन्स के रूप में **एक्सपोर्ट** करें:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स और पोल इंटरवल वैकल्पिक env वेरिएबल्स हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर किसी भी अन्य स्रोत से ट्रेस और मेट्रिक्स स्वीकार करता है (प्रोटोबफ़ इनजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फ़र्स्ट ClawMetry डैशबोर्ड **और** आपकी टीम पहले से चला रही किसी भी बैकएंड में आपका डेटा मिलता है — कोई लॉक-इन नहीं, इंस्टॉल करने के लिए कोई दूसरा एजेंट नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग्स, सेशन्स और क्रॉन्स को ऑटो-डिटेक्ट करता है।

अगर आपको कस्टमाइज़ करने की ज़रूरत है:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव गतिविधि दिखाता है। सिर्फ़ वे चैनल जो आपके `openclaw.json` में वास्तव में सेटअप हैं, Flow डायग्राम में दिखाई देते हैं — अनकॉन्फ़िगर्ड चैनल स्वचालित रूप से छिपे रहते हैं।

Flow में किसी भी चैनल नोड पर क्लिक करके इनकमिंग/आउटगोइंग मैसेज काउंट्स के साथ एक लाइव चैट बबल व्यू देखें।

| Channel | स्थिति | Live Popup | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मैसेज, आँकड़े, 10s रीफ़्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | सीधे `~/Library/Messages/chat.db` पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के ज़रिए |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के ज़रिए |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | Guild + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | Workspace + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के ज़रिए iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक्स के ज़रिए |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन के ज़रिए |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ़-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के ज़रिए चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपकी `~/.openclaw/openclaw.json` पढ़ता है और सिर्फ़ उन्हीं चैनलों को रेंडर करता है जो आपने वास्तव में कॉन्फ़िगर किए हैं। किसी मैन्युअल सेटअप की ज़रूरत नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को कंटेनर में चलाना चाहते हैं? कोई समस्या नहीं! 🐳

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

> **नोट:** Docker में चलाते समय, अपने एजेंट की डेटा + लॉग डायरेक्टरी (जैसे `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करें ताकि ClawMetry आपके सेटअप को ऑटो-डिटेक्ट कर सके।

## आवश्यकताएँ

- Python 3.8+
- Flask (pip के ज़रिए स्वचालित रूप से इंस्टॉल)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, या GitHub Copilot (या Docker के लिए माउंटेड वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) को स्वचालित रूप से डिटेक्ट करता है — NVIDIA का एंटरप्राइज़ सिक्योरिटी रैपर जो OpenClaw के लिए है और सैंडबॉक्स्ड OpenShell कंटेनरों के अंदर एजेंट्स चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक डीमन सेशन फ़ाइलों को स्वचालित रूप से खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry NemoClaw को दो तरीकों से डिटेक्ट करता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज के लिए चल रहे Docker कंटेनरों को स्कैन करता है, फिर वॉल्यूम माउंट या `docker cp` के ज़रिए सेशन पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलों को क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा के साथ टैग किया जाता है, ताकि आप उन्हें एक नज़र में स्टैंडर्ड OpenClaw सेशन से अलग बता सकें।

### अनुशंसित सेटअप: होस्ट पर सिंक डीमन

सबसे अच्छे अनुभव के लिए, ClawMetry का सिंक डीमन **होस्ट मशीन** पर चलाएँ (सैंडबॉक्स के अंदर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी प्रतिबंधों से बचा जा सकता है।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डीमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशन को स्वचालित रूप से खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स की ओर इंगित करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (एडवांस्ड)

अगर आपको सिंक डीमन को OpenShell सैंडबॉक्स के **अंदर** चलाना ज़रूरी है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह एग्रेस नियम जोड़ें ताकि यह ClawMetry इनजेस्ट API तक पहुँच सके:

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

### पोर्ट्स और एंडपॉइंट्स

| Endpoint | Port | Protocol | ज़रूरी |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डीमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डीमन सिर्फ़ `ingest.clawmetry.com` पर आउटबाउंड HTTPS कॉल्स करता है। किसी इनबाउंड पोर्ट की ज़रूरत नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी, और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

इस प्रोजेक्ट का परीक्षण BrowserStack के साथ किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry `https://app.clawmetry.com/api/install` पर अनाम इंस्टॉल-लाइफ़साइकल
पिंग भेजता है: जब आप किसी नई मशीन पर पहली बार `clawmetry` CLI चलाते हैं तो एक `install` पिंग,
किसी नए वर्ज़न में अपग्रेड करने के बाद पहले रन पर एक `update` पिंग,
और जब आप इन-डैशबोर्ड ऑनबोर्डिंग विकल्प पूरा करते हैं तो एक `onboarded`
पिंग। हम इसका उपयोग वास्तविक इंस्टॉल गिनने के लिए करते हैं (कच्चे PyPI डाउनलोड नंबर ~98% मिरर, CI,
और ऑटो-अपडेट री-डाउनलोड होते हैं) और यह जानने के लिए कि कौन से एजेंट फ़्रेमवर्क और
वर्ज़न वास्तव में उपयोग में हैं।

**प्रति लाइफ़साइकल इवेंट प्रति वर्ज़न अधिकतम एक POST**, जिसमें शामिल है:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर संग्रहीत रैंडम UUID | डिडुप; अनाम जब तक आप स्पष्ट रूप से Cloud sync कनेक्ट नहीं करते (फिर प्रामाणिक डीमन हार्टबीट इसे साथ ले जाता है, इस इंस्टॉल को आपके अकाउंट से जोड़ते हुए) |
| `event` | `install` / `update` / `onboarded` | नया इंस्टॉल बनाम मौजूदा का अपग्रेड |
| `version` | `0.12.167` | कौन से वर्ज़न उपयोग में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट्स के साथ एकीकृत होना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड सर्वर-साइड अनुरोध से देश कोड निकालता है,
फिर IP को छोड़ देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस
पथ, फ़ाइल सामग्री, आपकी api_key, आपका ईमेल, कुछ भी PII या
वर्कस्पेस-विशिष्ट। वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट योग्य है।

**ऑप्ट आउट** (इनमें से कोई भी एक इसे स्थायी रूप से अक्षम कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहाँ नेटवर्क विफलता कभी भी `clawmetry` को चलने से नहीं रोकती — यह पिंग
एक डीमन थ्रेड पर 3 s टाइमआउट के साथ फ़ायर-एंड-फ़ॉरगेट है।

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> द्वारा निर्मित · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टम का हिस्सा</sub>
</p>
