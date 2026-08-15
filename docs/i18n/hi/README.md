<!-- i18n-src:c422fb7dd0da -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **20 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 16 और। आपके पूरे एजेंट फ़्लीट के लिए एक ही डैशबोर्ड।

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। बिना किसी कॉन्फ़िगरेशन के। सब कुछ अपने आप पहचानता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है और बस, हो गया।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20 एजेंट रनटाइम के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह एक ही डैशबोर्ड में आपके **पूरे एजेंट फ़्लीट** को मीटर करता है, आपकी मशीन पर हर रनटाइम को अपने आप पहचानते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम ClawMetry Cloud या सेल्फ़-होस्टेड Pro लाइसेंस के साथ सक्रिय होते हैं। हेडर से रनटाइम बदलें और हर टैब — कॉस्ट, टोकन, टूल्स, ट्रेसेस — उस रनटाइम पर फिर से स्कोप हो जाता है। सटीक फ़्री/पेड बंटवारे, टियर मैट्रिक्स, `/api/entitlement` शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow** — चैनलों, ब्रेन, टूल्स से होकर बहते और वापस लौटते संदेशों को दिखाने वाला लाइव एनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक, एक्टिविटी हीटमैप, सेशन काउंट, मॉडल जानकारी
- **Usage** — डेली/वीकली/मंथली ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम एक्टिविटी के साथ सक्रिय एजेंट सेशन
- **Crons** — स्टेटस, अगला रन, अवधि के साथ शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रीयल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, डेली नोट्स ब्राउज़ करें
- **Transcripts** — सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप, एरर-रेट ट्रिगर, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर रूट होता है
- **Approvals** — विनाशकारी डिलीट, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल को एक-क्लिक साइन-ऑफ़ के पीछे गेट करें

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

### 🚨 Alerts — बजट कैप, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email को वेबहुक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल्स को मैन्युअल साइन-ऑफ़ के पीछे गेट करें; पॉलिसी-समर्थित सुरक्षा नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code के लिए एग्ज़ीक्यूशन-पूर्व ब्लॉकिंग** — एक कमांड एक
PreToolUse हुक इंस्टॉल करता है जो मिलते-जुलते टूल कॉल्स को उनके चलने *से पहले*
रोक देता है और आपके फ़ैसले का इंतज़ार करता है (आपके फ़ोन से एक टैप, जब
[क्लाउड पुश नोटिफ़िकेशन](https://app.clawmetry.com/push) चालू हों):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक deny सिर्फ़ उसी एक टूल कॉल को ब्लॉक करता है — एजेंट अपना सेशन बनाए रखता है और
कोई और तरीक़ा आज़मा सकता है। अपने फ़ोन पर अप्रूव करना Claude Code के अपने
परमिशन प्रॉम्प्ट को स्किप कर देता है (आप पहले ही जवाब दे चुके हैं)। बिना मिलान वाले टूल्स
की लागत ~40ms होती है और वे Claude Code के सामान्य परमिशन फ़्लो में चले जाते हैं।
जब Claude Code खुद आपका इंतज़ार कर रहा हो (`permission_prompt` /
`idle_prompt` नोटिफ़िकेशन) तब भी आपको फ़ोन पुश मिलता है।

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

v2 React ऐप `frontend/` में रहता है और `/v2` पर सर्व होता है जब Flask
सर्वर को v2 सक्षम करके शुरू किया जाता है।

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

`http://localhost:5173/v2/` खोलें। Vite `/api` रिक्वेस्ट्स को
`http://localhost:8900` पर प्रॉक्सी करता है, ताकि React ऐप बिना अतिरिक्त
CORS सेटअप के लोकल Flask सर्वर से बात कर सके।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट संगतता

ClawMetry केवल OpenClaw ही नहीं, बल्कि कई AI-एजेंट रनटाइम को ऑब्ज़र्व करता है। हर गैर-OpenClaw रनटाइम एक समर्पित रीडर एडाप्टर शिप करता है जो उसके नेटिव सेशन फ़ॉर्मैट को ClawMetry के यूनिफ़ाइड शेप्स में बदलता है; डेमन इन्हें उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इनजेस्ट करता है, रनटाइम के साथ टैग किया हुआ, और जब एक से अधिक रनटाइम मौजूद हों तो Session replay टैब में एक **रनटाइम स्विचर** दिखता है। पूरे मैट्रिक्स + रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-फ़ैमिली प्राइमर के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

[Perplexity का numbat](https://github.com/perplexityai/numbat) एजेंट-सिक्योरिटी टूल चला रहे हैं? ClawMetry इसकी फ़ाइंडिंग्स और एनफ़ोर्समेंट डिसीज़न्स को बिना किसी अतिरिक्त सेटअप के इनजेस्ट करता है — देखें [`docs/NUMBAT.md`](docs/NUMBAT.md)।

| रनटाइम / एजेंट | स्टेटस | नोट्स |
|---|---|---|
| **OpenClaw** | Native | संदर्भ रनटाइम, अपने आप पहचाना जाता है |
| **PicoClaw** | Beta adapter | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स। |
| **NanoClaw** | Beta adapter | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट्स + संदेश गिनती। |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट्स, मॉडल, टोकन/कॉस्ट। |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स + थिंकिंग, टोकन उपयोग। |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Cursor** | Beta adapter | SQLite `state.vscdb`। चैट/कंपोज़र ट्रांसक्रिप्ट्स, मॉडल। |
| **Aider** | Beta adapter | प्रति-प्रोजेक्ट `.aider.chat.history.md`। ट्रांसक्रिप्ट्स, मॉडल, टोकन गिनती। |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन योग। |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन उपयोग। |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`। ट्रांसक्रिप्ट्स, मॉडल, टूल कॉल्स, टोकन + कॉस्ट। |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`। वर्कफ़्लो एग्ज़ीक्यूशन, नोड रन, AI Agent प्रॉम्प्ट्स, जहाँ n8n रिकॉर्ड करता है वहाँ मॉडल + टोकन। |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` के अंतर्गत ब्रेन JSONL। बातचीत, टूल स्टेप्स, थिंकिंग, प्रति-जनरेशन Gemini टोकन विभाजन + कॉस्ट, बैकग्राउंड-जनरेशन बर्न। |
| **GitHub Copilot** | Beta adapter | `~/.copilot/session-state/` के अंतर्गत Copilot CLI `events.jsonl` + प्रति-कॉल उपयोग लेजर `session-store.db`। बातचीत, टूल कॉल्स, मॉडल रूटिंग, कैश-अवेयर टोकन विभाजन, वेंडर-बिल्ड AI-क्रेडिट कॉस्ट। |
| **Grok** | Beta adapter | xAI Grok Build CLI (`~/.grok/bin/grok` के अंतर्गत Rust बाइनरी): ग्लोबल इवेंट लॉग `~/.grok/logs/unified.jsonl` + प्रति-सेशन `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`। बातचीत, प्रति-टर्न टोकन विभाजन, मॉडल रूटिंग, और CLI का आउटबाउंड रीपो पेलोड जो `~/.grok/upload_queue/` में स्टेज होता है ताकि आप देख सकें कि आपकी मशीन से क्या बाहर गया। |

"Beta adapter" का मतलब है कि ClawMetry उस रनटाइम के असल ऑन-डिस्क फ़ॉर्मैट के लिए एक रीडर शिप करता है, हर एक को असल मशीन पर असल इंस्टॉल के ख़िलाफ़ बनाया और सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। एडाप्टर रीड-ओनली हैं; हर एक इस बारे में ईमानदार है कि उसका रनटाइम असल में क्या स्टोर करता है (उदाहरण के लिए PicoClaw/NanoClaw/Cursor डिस्क पर टोकन कॉस्ट नहीं लिखते)। जब एक नोड पर कई रनटाइम चल रहे हों, तो रनटाइम स्विचर एक साफ़ डीप-डाइव के लिए सेशन व्यू को एक ही रनटाइम पर स्कोप कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट अट्रिब्यूशन

ऊपर बताए गए सभी रनटाइम सेशन को डिस्क पर लिखते हैं। आपका अपना **प्रोडक्शन एजेंट** — वह जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक साधारण `httpx` लूप पर बनाया है — ऐसा नहीं करता। ClawMetry का ज़ीरो-कॉन्फ़िग इंटरसेप्टर फिर भी `httpx`/`requests` को मंकी-पैच करके इसके LLM कॉल्स (कॉस्ट, टोकन, लेटेंसी, एरर) कैप्चर कर लेता है:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` एनवायरनमेंट वेरिएबल) हर कॉल को एक **नामित सोर्स** से टैग करता है, ताकि आपके द्वारा चलाया जाने वाला हर प्रोडक्ट डैशबोर्ड के Overview पर मौजूद **🔌 आउट-लूप सोर्स** कार्ड में अपनी ख़ुद की, प्रथम-श्रेणी की, कॉस्ट-अट्रिब्यूटेबल लाइन के रूप में दिखे — प्रति-एजेंट कॉल्स, प्रोवाइडर, लेटेंसी, एरर रेट। कोई सोर्स सेट नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; बस कार्ड छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जो रनटाइम एडाप्टर्स को फ़ीड करती है (DuckDB → क्लाउड स्नैपशॉट), इसलिए आउट-लूप सोर्स बाक़ी सब चीज़ों की तरह ही, E2E-एन्क्रिप्टेड रूप में क्लाउड डैशबोर्ड से सिंक होते हैं।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI सिमैंटिक कन्वेंशन्स** का उपयोग करते हुए, ताकि आपके एजेंट ट्रेस कभी भी किसी एक टूल में लॉक-इन न हों।

हर सेशन — LLM कॉल्स, टूल्स, सब-एजेंट्स, टोकन, कॉस्ट — को किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपका अपना OTel Collector) में OTLP/HTTP GenAI स्पैन के रूप में **एक्सपोर्ट** करें:

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

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces`, `/v1/logs`, और `/v1/metrics` पर किसी भी अन्य स्रोत से ट्रेस, लॉग, और मेट्रिक्स स्वीकार करता है। किसी भी OpenTelemetry-इंस्ट्रुमेंटेड ऐप को इसकी ओर पॉइंट करें:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON ट्रेस और लॉग एक सामान्य `pip install clawmetry` पर बिना किसी एक्स्ट्रा के काम करते हैं। Protobuf इनजेस्ट (और OTLP/JSON मेट्रिक्स) के लिए `pip install clawmetry[otel]` चाहिए। जो ऐप अपना ख़ुद का `service.name` सेट करता है वह रनटाइम स्विचर में अपने ख़ुद के एजेंट के रूप में, अपने कॉस्ट और टोकन के साथ दिखता है।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फ़र्स्ट ClawMetry डैशबोर्ड **और** आपकी टीम जो भी बैकएंड पहले से चलाती है उसमें आपका डेटा **दोनों** मिलते हैं — कोई लॉक-इन नहीं, कोई दूसरा एजेंट इंस्टॉल करने की ज़रूरत नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िगरेशन की ज़रूरत नहीं पड़ती। ClawMetry आपके वर्कस्पेस, लॉग, सेशन, और cron को अपने आप पहचान लेता है।

अगर आपको कस्टमाइज़ करने की ज़रूरत है:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सभी विकल्प: `clawmetry --help`

## समर्थित चैनल

ClawMetry आपके द्वारा कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव एक्टिविटी दिखाता है। सिर्फ़ वही चैनल जो आपके `openclaw.json` में असल में सेट अप हैं वे Flow डायग्राम में दिखते हैं — जो कॉन्फ़िगर नहीं हैं वे अपने आप छिपे रहते हैं।

Flow में किसी भी चैनल नोड पर क्लिक करने पर आने वाले/जाने वाले संदेशों की गिनती के साथ एक लाइव चैट बबल व्यू दिखता है।

| चैनल | स्टेटस | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | संदेश, आँकड़े, 10s रिफ़्रेश |
| 💬 **iMessage** | ✅ Full | ✅ | सीधे `~/Library/Messages/chat.db` पढ़ता है |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) के ज़रिए |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli के ज़रिए |
| 🟣 **Discord** | ✅ Full | ✅ | गिल्ड + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ Full | ✅ | वर्कस्पेस + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ Full | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ Full | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API के ज़रिए iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API वेबहुक्स के ज़रिए |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams बॉट प्लगइन के ज़रिए |
| 🔷 **Mattermost** | ✅ Full | ✅ | सेल्फ़-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ Full | ✅ | डीसेंट्रलाइज़्ड, E2EE समर्थन |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | डीसेंट्रलाइज़्ड NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC कनेक्शन के ज़रिए चैट |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपकी `~/.openclaw/openclaw.json` पढ़ता है और सिर्फ़ वही चैनल रेंडर करता है जो आपने असल में कॉन्फ़िगर किए हैं। किसी मैनुअल सेटअप की ज़रूरत नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को कंटेनर में चलाना चाहते हैं? कोई बात नहीं! 🐳

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

> **नोट:** Docker में चलाते समय, अपने एजेंट की डेटा + लॉग डायरेक्टरी माउंट करें (जैसे `~/.openclaw`, `~/.claude`, `~/.codex`) ताकि ClawMetry आपके सेटअप को अपने आप पहचान सके।

## आवश्यकताएँ

- Python 3.8+
- Flask (pip के ज़रिए अपने आप इंस्टॉल हो जाता है)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, या QM (या Docker के लिए माउंटेड वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) को अपने आप पहचान लेता है — यह OpenClaw के लिए NVIDIA का एंटरप्राइज़ सिक्योरिटी रैपर है जो एजेंट्स को सैंडबॉक्स्ड OpenShell कंटेनरों के अंदर चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक डेमन सेशन फ़ाइलों को अपने आप खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या किसी OpenShell कंटेनर के अंदर।

### यह कैसे काम करता है

ClawMetry दो तरीक़ों से NemoClaw का पता लगाता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज के लिए चल रहे Docker कंटेनरों को स्कैन करता है, फिर वॉल्यूम माउंट या `docker cp` के ज़रिए सेशन पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलें क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा से टैग होती हैं, ताकि आप एक नज़र में उन्हें मानक OpenClaw सेशन से अलग बता सकें।

### अनुशंसित सेटअप: होस्ट पर सिंक डेमन

सबसे अच्छे अनुभव के लिए, ClawMetry के सिंक डेमन को **होस्ट मशीन** पर चलाएँ (सैंडबॉक्स के अंदर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी प्रतिबंध नहीं आते।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के अंदर सेशन को अपने आप खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स की ओर पॉइंट करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के अंदर चलाना (एडवांस्ड)

अगर आपको सिंक डेमन को OpenShell सैंडबॉक्स के **अंदर** चलाना ही है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह ईग्रेस नियम जोड़ें ताकि यह ClawMetry इनजेस्ट API तक पहुँच सके:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

लागू करें:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट और एंडपॉइंट

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | ज़रूरी |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कवरी के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` को आउटबाउंड HTTPS कॉल करता है। किसी इनबाउंड पोर्ट की ज़रूरत नहीं है।

---

## Cloud डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी, और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

यह प्रोजेक्ट BrowserStack के साथ टेस्ट किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry `https://app.clawmetry.com/api/install` पर गुमनाम
इंस्टॉल-लाइफ़साइकिल पिंग भेजता है: नई मशीन पर पहली बार `clawmetry`
CLI चलाने पर एक `install` पिंग, किसी नए वर्ज़न में अपग्रेड करने के बाद
पहले रन पर एक `update` पिंग, और जब आप इन-डैशबोर्ड ऑनबोर्डिंग चुनाव
पूरा करते हैं तब एक `onboarded` पिंग। हम इसका उपयोग असल इंस्टॉल्स
गिनने के लिए करते हैं (कच्चे PyPI डाउनलोड नंबर ~98% मिरर, CI, और
ऑटो-अपडेट री-डाउनलोड होते हैं) और यह जानने के लिए कि असल में कौन-से
एजेंट फ़्रेमवर्क और वर्ज़न इस्तेमाल में हैं।

**प्रति लाइफ़साइकिल इवेंट प्रति वर्ज़न अधिकतम एक POST**, जिसमें शामिल है:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर स्टोर की गई रैंडम UUID | डीडुप; जब तक आप स्पष्ट रूप से Cloud sync कनेक्ट नहीं करते तब तक गुमनाम (उसके बाद ऑथेंटिकेटेड डेमन हार्टबीट इसे साथ ले जाता है, इस इंस्टॉल को आपके अकाउंट से जोड़ते हुए) |
| `event` | `install` / `update` / `onboarded` | नया इंस्टॉल बनाम मौजूदा का अपग्रेड |
| `version` | `0.12.167` | कौन-से वर्ज़न इस्तेमाल में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | आगे हमें किन एजेंट्स के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | इंसानी इंस्टॉल्स को CI शोर से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड सर्वर-साइड पर रिक्वेस्ट से देश कोड
निकालता है, फिर IP को छोड़ देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस पाथ,
फ़ाइल कंटेंट, आपकी api_key, आपका ईमेल, कुछ भी PII या वर्कस्पेस-विशिष्ट।
वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py) में
ऑडिट के लिए उपलब्ध है।

**ऑप्ट आउट करें** (इनमें से कोई भी एक इसे स्थायी रूप से बंद कर देता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

यहाँ नेटवर्क विफलता कभी भी `clawmetry` को चलने से नहीं रोकती — यह पिंग
डेमन थ्रेड पर 3s टाइमआउट के साथ फ़ायर-एंड-फ़ॉरगेट है।

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
  <sub>निर्मित <a href="https://github.com/vivekchand">@vivekchand</a> द्वारा · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ईकोसिस्टम का हिस्सा</sub>
</p>
