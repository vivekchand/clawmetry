<!-- i18n-src:8252f6b1d31d -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**अपने एजेंट को सोचते हुए देखें।** **14 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 10 और। आपके पूरे एजेंट फ़्लीट के लिए एक ही डैशबोर्ड।

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। कोई कॉन्फ़िगरेशन नहीं। सब कुछ ऑटो-डिटेक्ट होता है।

```bash
pip install clawmetry && clawmetry
```

यह **http://localhost:8900** पर खुलता है और आपका काम पूरा हो जाता है।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजेंट रनटाइम के साथ काम करता है

ClawMetry की शुरुआत OpenClaw के लिए ऑब्ज़र्वेबिलिटी के रूप में हुई थी, और अब यह आपके **पूरे एजेंट फ़्लीट** को एक ही डैशबोर्ड में मापता है, आपकी मशीन पर मौजूद हर रनटाइम को ऑटो-डिटेक्ट करते हुए:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw और NemoClaw ओपन-सोर्स ऐप में मुफ़्त हैं; बाकी रनटाइम ClawMetry Cloud या सेल्फ़-होस्टेड Pro लाइसेंस के साथ सक्रिय हो जाते हैं। हेडर से रनटाइम बदलें और हर टैब, कॉस्ट, टोकन, टूल्स, ट्रेस, उस रनटाइम के हिसाब से फिर से स्कोप हो जाता है। सटीक फ्री/पेड बंटवारा, टियर मैट्रिक्स, `/api/entitlement` का शेप, और `clawmetry license` CLI के लिए **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** देखें।

## आपको क्या मिलता है

- **Flow** — चैनलों, ब्रेन, टूल्स से होकर आने-जाने वाले मैसेजों को दिखाने वाला लाइव एनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक, एक्टिविटी हीटमैप, सेशन काउंट, मॉडल जानकारी
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउन के साथ टोकन और कॉस्ट ट्रैकिंग
- **Sessions** — मॉडल, टोकन, अंतिम गतिविधि के साथ सक्रिय एजेंट सेशन
- **Crons** — स्टेटस, अगला रन, अवधि के साथ शेड्यूल की गई जॉब्स
- **Logs** — कलर-कोडेड रीयल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउज़ करें
- **Transcripts** — सेशन हिस्ट्री पढ़ने के लिए चैट-बबल UI
- **Alerts** — बजट कैप, एरर-रेट ट्रिगर, एजेंट-ऑफ़लाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email पर रूट होता है
- **Approvals** — डिस्ट्रक्टिव डिलीट, फ़ोर्स पुश, DB म्यूटेशन, sudo, पैकेज इंस्टॉल, नेटवर्क कॉल्स को एक-क्लिक साइन-ऑफ़ के पीछे रोकें

## स्क्रीनशॉट

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

### 🔐 Security — पोज़्चर और ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजट कैप, एरर-रेट ट्रिगर, Slack / Discord / PagerDuty / Email के लिए वेबहुक
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखिम भरे टूल कॉल्स को मैनुअल साइन-ऑफ़ के पीछे रोकें; पॉलिसी-समर्थित प्रोटेक्शन नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code के लिए प्री-एक्ज़ीक्यूशन ब्लॉकिंग** — एक कमांड एक
PreToolUse हुक इंस्टॉल करता है जो मैचिंग टूल कॉल्स को चलने *से पहले* रोकता है और आपके फ़ैसले का इंतज़ार करता है
([क्लाउड पुश नोटिफिकेशन](https://app.clawmetry.com/push) सक्षम होने पर आपके फ़ोन से एक टैप में):

```bash
clawmetry hooks install     # ~/.claude/settings.json लिखता है (इडेम्पोटेंट)
clawmetry hooks status      # क्या-क्या जुड़ा है + कितनी पॉलिसियाँ सक्रिय हैं
clawmetry hooks uninstall   # केवल ClawMetry की एंट्रियाँ हटाता है
```

एक डिनाय केवल उस एक टूल कॉल को रोकता है, एजेंट अपना सेशन बनाए रखता है और
दूसरा तरीका आज़मा सकता है। आपके फ़ोन पर अनुमोदन करने से Claude Code का अपना
परमिशन प्रॉम्प्ट स्किप हो जाता है (आप पहले ही जवाब दे चुके हैं)। बिना मैच वाले टूल्स में लगभग 40ms का समय लगता है और
वे Claude Code के सामान्य परमिशन फ़्लो में चले जाते हैं। साथ ही जब Claude Code खुद आपका इंतज़ार कर रहा हो तो आपको फ़ोन पुश भी मिलता है
(`permission_prompt` / `idle_prompt` नोटिफिकेशन)।

## इंस्टॉल करें

**वन-लाइनर (सुझाया गया):**
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

v2 React ऐप `frontend/` में रहता है और जब Flask
सर्वर v2 सक्षम करके शुरू किया जाता है तो यह `/v2` पर सर्व होता है।

डेवलपमेंट के दौरान दो टर्मिनल इस्तेमाल करें:

```bash
# टर्मिनल 1: :8900 पर Flask API/सर्वर
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# टर्मिनल 2: :5173 पर Vite डेव सर्वर
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` खोलें। Vite `/api` रिक्वेस्ट को
`http://localhost:8900` पर प्रॉक्सी करता है, इसलिए React ऐप
बिना अतिरिक्त CORS सेटअप के लोकल Flask सर्वर से बात कर सकता है।

Python पैकेज के साथ शिप होने वाला बंडल बनाने के लिए:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` में लिखा जाता है।

## रनटाइम / एजेंट कम्पैटिबिलिटी

ClawMetry सिर्फ़ OpenClaw नहीं, बल्कि कई AI-एजेंट रनटाइम को ऑब्ज़र्व करता है। हर नॉन-OpenClaw रनटाइम एक डेडिकेटेड रीडर एडाप्टर शिप करता है जो उसके नेटिव सेशन फ़ॉर्मैट को ClawMetry के यूनिफ़ाइड शेप में बदलता है; डेमन इन्हें उसी DuckDB स्टोर + क्लाउड स्नैपशॉट में इनजेस्ट करता है, रनटाइम के साथ टैग किया जाता है, और जब एक से ज़्यादा रनटाइम मौजूद हों तो Session replay टैब एक **रनटाइम स्विचर** दिखाता है। पूरा मैट्रिक्स + रनटाइम जोड़ने की गाइड के लिए [`docs/compatibility.md`](docs/compatibility.md) देखें, और OpenClaw-फ़ैमिली प्राइमर के लिए [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) देखें।

| रनटाइम / एजेंट | स्टेटस | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव | संदर्भ रनटाइम, ऑटो-डिटेक्टेड |
| **PicoClaw** | बीटा एडाप्टर | फ़्लैट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ट्रांसक्रिप्ट, मॉडल, टूल कॉल। |
| **NanoClaw** | बीटा एडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`)। ट्रांसक्रिप्ट + मैसेज काउंट। |
| **Hermes** | बीटा एडाप्टर | SQLite `~/.hermes/state.db`। ट्रांसक्रिप्ट, मॉडल, टोकन/कॉस्ट। |
| **Claude Code** | बीटा एडाप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल + थिंकिंग, टोकन उपयोग। |
| **Codex** | बीटा एडाप्टर | रोलआउट JSONL `~/.codex/sessions/...`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन उपयोग। |
| **Cursor** | बीटा एडाप्टर | SQLite `state.vscdb`। चैट/कम्पोज़र ट्रांसक्रिप्ट, मॉडल। |
| **Aider** | बीटा एडाप्टर | हर प्रोजेक्ट के लिए `.aider.chat.history.md`। ट्रांसक्रिप्ट, मॉडल, टोकन काउंट। |
| **Goose** | बीटा एडाप्टर | SQLite `~/.local/share/goose`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन टोटल। |
| **opencode** | बीटा एडाप्टर | SQLite `~/.local/share/opencode`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन + कॉस्ट। |
| **Qwen Code** | बीटा एडाप्टर | JSONL `~/.qwen/projects/.../chats`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन उपयोग। |
| **Pi** | बीटा एडाप्टर | JSONL `~/.pi/agent/sessions`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन + कॉस्ट। |
| **Deep Agents** | बीटा एडाप्टर | SQLite `~/.deepagents/.state/sessions.db`। ट्रांसक्रिप्ट, मॉडल, टूल कॉल, टोकन + कॉस्ट। |
| **n8n** | बीटा एडाप्टर | SQLite `~/.n8n/database.sqlite`। वर्कफ़्लो एक्ज़ीक्यूशन, नोड रन, AI Agent प्रॉम्प्ट, मॉडल + टोकन जहाँ n8n उन्हें रेकॉर्ड करता है। |

"बीटा एडाप्टर" का मतलब है कि ClawMetry उस रनटाइम के असली ऑन-डिस्क फ़ॉर्मैट के लिए एक रीडर शिप करता है, हर एक को असली मशीन पर असली इंस्टॉल के आधार पर बनाया और सत्यापित किया गया है (देखें `tests/fixtures/runtimes/<rt>/`)। एडाप्टर रीड-ओनली हैं; हर एक इस बारे में स्पष्ट है कि उसका रनटाइम वास्तव में क्या स्टोर करता है (उदाहरण के लिए PicoClaw/NanoClaw/Cursor टोकन कॉस्ट डिस्क पर नहीं लिखते)। जब एक नोड पर कई रनटाइम चल रहे हों, तो रनटाइम स्विचर सेशन व्यू को एक साफ़ डीप-डाइव के लिए एक रनटाइम तक सीमित कर देता है।

## किसी भी SDK एजेंट को ट्रैक करें — आउट-लूप कॉस्ट अट्रिब्यूशन

ऊपर दिए गए सभी रनटाइम सेशन को डिस्क पर लिखते हैं। आपका अपना **प्रोडक्शन एजेंट**, वह जो आपने OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, या एक सादे `httpx` लूप पर बनाया है, ऐसा नहीं करता। ClawMetry का ज़ीरो-कॉन्फ़िग इंटरसेप्टर फिर भी `httpx`/`requests` को मंकी-पैच करके उसकी LLM कॉल्स (कॉस्ट, टोकन, लेटेंसी, एरर) कैप्चर करता है:

```python
import clawmetry.track            # इंटरसेप्टर सक्रिय करें
clawmetry.track.set_source("support-agent")   # इस प्रोडक्ट का नाम रखें

# ...आपका एजेंट सामान्य रूप से चलता है; हर LLM कॉल अब ट्रैक + अट्रिब्यूटेड है।
```

`set_source()` (या `CLAWMETRY_SOURCE=support-agent` एनवायरनमेंट वेरिएबल) हर कॉल को एक **नामित सोर्स** से टैग करता है, इसलिए आपके द्वारा चलाया जाने वाला हर प्रोडक्ट डैशबोर्ड के Overview पर मौजूद **🔌 आउट-लूप सोर्सेज़** कार्ड में अपनी खुद की, फ़र्स्ट-क्लास, कॉस्ट-अट्रिब्यूटेबल लाइन के रूप में दिखता है, हर एजेंट के लिए कॉल्स, प्रोवाइडर, लेटेंसी, एरर रेट। कोई सोर्स सेट नहीं किया? कॉल्स फिर भी ट्रैक होती हैं; कार्ड बस छिपा रहता है।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

यह वही डेटा लेयर है जिसे रनटाइम एडाप्टर फ़ीड करते हैं (DuckDB → क्लाउड स्नैपशॉट), इसलिए आउट-लूप सोर्सेज़ बाकी सब चीज़ों की तरह ही, E2E-एन्क्रिप्टेड, क्लाउड डैशबोर्ड में सिंक होते हैं।

## OpenTelemetry — वेंडर-न्यूट्रल, अपने ट्रेस कहीं भी भेजें

ClawMetry दोनों दिशाओं में **OpenTelemetry** बोलता है, **GenAI सिमैंटिक कन्वेंशन** का उपयोग करते हुए, ताकि आपके एजेंट ट्रेस कभी भी किसी एक टूल में लॉक न हों।

हर सेशन को, LLM कॉल्स, टूल्स, सब-एजेंट, टोकन, कॉस्ट को, किसी भी कलेक्टर (Datadog, Grafana, Honeycomb, या आपका अपना OTel Collector) पर OTLP/HTTP GenAI स्पैन के रूप में **एक्सपोर्ट** करें:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# समान रूप से:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर और पोल इंटरवल वैकल्पिक एनवायरनमेंट वेरिएबल हैं:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # अतिरिक्त HTTP हेडर
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # सेकंड (डिफ़ॉल्ट 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीवर `/v1/traces` और `/v1/metrics` पर किसी भी और चीज़ से ट्रेस और मेट्रिक्स स्वीकार करता है (प्रोटोबफ़ इनजेस्ट के लिए `pip install clawmetry[otel]`)।

आपको ज़ीरो-कॉन्फ़िग, लोकल-फ़र्स्ट ClawMetry डैशबोर्ड **और** आपकी टीम जो भी बैकएंड पहले से चलाती है उसमें आपका डेटा, दोनों मिलते हैं, कोई लॉक-इन नहीं, कोई दूसरा एजेंट इंस्टॉल करने की ज़रूरत नहीं।

## कॉन्फ़िगरेशन

ज़्यादातर लोगों को किसी कॉन्फ़िग की ज़रूरत नहीं होती। ClawMetry आपके वर्कस्पेस, लॉग्स, सेशन, और क्रॉन को ऑटो-डिटेक्ट करता है।

अगर आपको कस्टमाइज़ करना है:

```bash
clawmetry --port 9000              # कस्टम पोर्ट (डिफ़ॉल्ट: 8900)
clawmetry --host 127.0.0.1         # केवल लोकलहोस्ट से बाइंड करें
clawmetry --workspace ~/mybot      # कस्टम वर्कस्पेस पथ
clawmetry --name "Alice"           # Flow विज़ुअलाइज़ेशन में आपका नाम
```

सभी विकल्प: `clawmetry --help`

## सपोर्टेड चैनल

ClawMetry आपके कॉन्फ़िगर किए गए हर OpenClaw चैनल के लिए लाइव गतिविधि दिखाता है। केवल वे चैनल जो वास्तव में आपके `openclaw.json` में सेटअप किए गए हैं, Flow डायग्राम में दिखते हैं, बिना कॉन्फ़िगर किए हुए स्वचालित रूप से छिप जाते हैं।

Flow में किसी भी चैनल नोड पर क्लिक करने से आपको इनकमिंग/आउटगोइंग मैसेज काउंट के साथ एक लाइव चैट बबल व्यू दिखता है।

| चैनल | स्टेटस | लाइव पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मैसेज, आँकड़े, 10s रिफ़्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | सीधे `~/Library/Messages/chat.db` पढ़ता है |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) के माध्यम से |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli के माध्यम से |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चैनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चैनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API के माध्यम से iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक के माध्यम से |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन के माध्यम से |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ़-होस्टेड टीम चैट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | डीसेंट्रलाइज़्ड, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | डीसेंट्रलाइज़्ड NIP-04 DM |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शन के माध्यम से चैट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इवेंट सब्सक्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry आपकी `~/.openclaw/openclaw.json` पढ़ता है और केवल उन चैनलों को रेंडर करता है जो आपने वास्तव में कॉन्फ़िगर किए हैं। किसी मैनुअल सेटअप की ज़रूरत नहीं।

## Docker डिप्लॉयमेंट

ClawMetry को कंटेनर में चलाना चाहते हैं? कोई समस्या नहीं! 🐳

**Docker के साथ क्विक स्टार्ट:**

```bash
# इमेज बनाएं
docker build -t clawmetry .

# डिफ़ॉल्ट सेटिंग्स के साथ चलाएं
docker run -p 8900:8900 clawmetry

# या अपने एजेंट की डेटा डायरेक्टरी माउंट करें (दिखाया गया: OpenClaw का ~/.openclaw)
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
- Flask (pip के माध्यम से स्वचालित रूप से इंस्टॉल होता है)
- उसी मशीन पर एक AI एजेंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, या n8n (या Docker के लिए माउंटेड वॉल्यूम)
- Linux या macOS

## NemoClaw / OpenShell समर्थन

ClawMetry स्वचालित रूप से [NemoClaw](https://github.com/NVIDIA/NemoClaw) का पता लगाता है, NVIDIA का एंटरप्राइज़ सिक्योरिटी रैपर OpenClaw के लिए जो एजेंट को सैंडबॉक्स्ड OpenShell कंटेनर के भीतर चलाता है।

ज़्यादातर मामलों में किसी अतिरिक्त कॉन्फ़िगरेशन की ज़रूरत नहीं है। सिंक डेमन सेशन फ़ाइलों को स्वचालित रूप से खोज लेता है, चाहे वे होस्ट पर `~/.openclaw/` में हों या किसी OpenShell कंटेनर के भीतर।

### यह कैसे काम करता है

ClawMetry NemoClaw का पता दो तरीकों से लगाता है:

1. **बाइनरी डिटेक्शन** — `nemoclaw` CLI की जाँच करता है और सैंडबॉक्स जानकारी पाने के लिए `nemoclaw status` चलाता है
2. **कंटेनर डिटेक्शन** — चल रहे Docker कंटेनरों में `openshell`, `nemoclaw`, या `ghcr.io/nvidia/` इमेज खोजता है, फिर वॉल्यूम माउंट या `docker cp` के माध्यम से सेशन पढ़ता है

NemoClaw कंटेनरों से सिंक की गई सेशन फ़ाइलों को क्लाउड डैशबोर्ड में `runtime=nemoclaw` और `container_id` मेटाडेटा के साथ टैग किया जाता है, ताकि आप एक नज़र में उन्हें स्टैंडर्ड OpenClaw सेशन से अलग बता सकें।

### सुझाया गया सेटअप: होस्ट पर सिंक डेमन

बेहतरीन अनुभव के लिए, ClawMetry का सिंक डेमन **होस्ट मशीन** पर चलाएं (सैंडबॉक्स के भीतर नहीं)। इससे NemoClaw नेटवर्क पॉलिसी प्रतिबंधों से बचा जा सकता है।

```bash
# होस्ट पर (सैंडबॉक्स के बाहर)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन किसी भी चल रहे OpenShell कंटेनर के भीतर सेशन को स्वचालित रूप से खोज लेगा।

### वैकल्पिक: स्पष्ट सैंडबॉक्स नाम

अगर ऑटो-डिटेक्शन काम नहीं करता, तो ClawMetry को सही सैंडबॉक्स की ओर इंगित करें:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सैंडबॉक्स के भीतर चलाना (एडवांस्ड)

अगर आपको सिंक डेमन सैंडबॉक्स के **भीतर** चलाना ही है, तो अपनी NemoClaw नेटवर्क पॉलिसी में यह इग्रेस नियम जोड़ें ताकि यह ClawMetry ingest API तक पहुँच सके:

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

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | आवश्यक |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हाँ (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | हाँ (लोकल डैशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन खोज के लिए |

सिंक डेमन केवल `ingest.clawmetry.com` पर आउटबाउंड HTTPS कॉल करता है। किसी इनबाउंड पोर्ट की ज़रूरत नहीं है।

---

## क्लाउड डिप्लॉयमेंट

SSH टनल, रिवर्स प्रॉक्सी, और Docker के लिए **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** देखें।

## टेस्टिंग

इस प्रोजेक्ट का टेस्टिंग BrowserStack के साथ किया जाता है।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry `https://app.clawmetry.com/api/install` पर अनाम इंस्टॉल-लाइफ़साइकल पिंग भेजता है:
एक `install` पिंग जब आप किसी नई मशीन पर पहली बार `clawmetry` CLI चलाते हैं, एक `update` पिंग
किसी नए वर्ज़न में अपग्रेड करने के बाद पहली रन पर, और एक `onboarded`
पिंग जब आप डैशबोर्ड के भीतर ऑनबोर्डिंग चयन पूरा करते हैं। हम इसका उपयोग वास्तविक इंस्टॉल गिनने के लिए करते हैं
(कच्चे PyPI डाउनलोड नंबर लगभग 98% मिरर, CI,
और ऑटो-अपडेट री-डाउनलोड होते हैं) और यह जानने के लिए कि वास्तव में कौन से एजेंट फ़्रेमवर्क और
वर्ज़न इस्तेमाल में हैं।

**हर लाइफ़साइकल इवेंट प्रति वर्ज़न पर अधिकतम एक POST**, जिसमें शामिल है:

| फ़ील्ड | उदाहरण | क्यों |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर स्टोर किया गया रैंडम UUID | डिडुप; तब तक अनाम जब तक आप स्पष्ट रूप से Cloud sync कनेक्ट नहीं करते (उसके बाद ऑथेंटिकेटेड डेमन हार्टबीट में यह शामिल होता है, जो इस इंस्टॉल को आपके अकाउंट से जोड़ता है) |
| `event` | `install` / `update` / `onboarded` | नया इंस्टॉल बनाम मौजूदा का अपग्रेड |
| `version` | `0.12.167` | कौन से वर्ज़न इस्तेमाल में हैं |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफ़ॉर्म समर्थन प्राथमिकताएँ |
| `python` | `3.11.15` | Python वर्ज़न समर्थन मैट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | हमें आगे किन एजेंट के साथ इंटीग्रेट करना चाहिए |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इंस्टॉल को CI नॉइज़ से अलग करना |

**हम क्या नहीं भेजते**: IP (क्लाउड सर्वर-साइड पर रिक्वेस्ट से देश कोड निकालता है, फिर
IP को हटा देता है), होस्टनेम, यूज़रनेम, वर्कस्पेस पथ, फ़ाइल सामग्री, आपकी api_key, आपका ईमेल, कुछ भी PII या
वर्कस्पेस-विशिष्ट। वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) में ऑडिट करने योग्य है।

**ऑप्ट आउट करें** (इनमें से किसी एक से इसे स्थायी रूप से बंद किया जा सकता है):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # प्रति-शेल
export DO_NOT_TRACK=1                          # W3C क्रॉस-टूल स्टैंडर्ड
touch ~/.clawmetry/notelemetry                 # स्थायी फ़ाइल मार्कर
```

यहाँ नेटवर्क फ़ेलियर कभी भी `clawmetry` को चलने से नहीं रोकता, पिंग
एक डेमन थ्रेड पर 3s टाइमआउट के साथ फ़ायर-एंड-फ़ॉरगेट होती है।

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
