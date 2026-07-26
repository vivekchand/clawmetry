<!-- i18n-src:bab48eec552f -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पहा.** **14 AI एजंट रनटाइम्ससाठी** रिअल टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि इतर 10. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अजून →](docs/i18n/)

एकच कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजंट रनटाइम्ससोबत काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्व्हेबिलिटी म्हणून झाली, आणि आता ते तुमच्या **संपूर्ण एजंट फ्लीटला** एकाच डॅशबोर्डमध्ये मोजते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप शोधून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw आणि NemoClaw ओपन-सोर्स ॲपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम बदला आणि प्रत्येक टॅब, खर्च, टोकन्स, टूल्स, ट्रेसेस, त्या रनटाइमसाठी पुन्हा-स्कोप होतो. नेमका फ्री/पेड विभाग, टियर मॅट्रिक्स, `/api/entitlement` शेप, आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, ब्रेन, टूल्स, आणि परत असा संदेशांचा प्रवाह दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, ॲक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनंदिन/साप्ताहिक/मासिक विभाजनासह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची ॲक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्थिती, पुढील रन, कालावधीसह शेड्यूल्ड जॉब्स
- **Logs** — रंगीत रिअल टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनंदिन नोंदी ब्राउझ करा
- **Transcripts** — सेशन हिस्टरी वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email कडे मार्गस्थ
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुश, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉल्स, नेटवर्क कॉल्स एका क्लिकच्या मंजुरीमागे थांबवा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशननुसार खर्चाचे विभाजन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाइल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोश्चर आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट कॅप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email कडे वेबहूक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखमीचे टूल कॉल्स मॅन्युअल मंजुरीमागे थांबवा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी पूर्व-अंमलबजावणी ब्लॉकिंग** — एकच कमांड जुळणारे टूल कॉल्स
ते चालण्या*आधी* थांबवणारा आणि तुमच्या निर्णयाची वाट पाहणारा PreToolUse hook
इन्स्टॉल करते ([क्लाउड पुश नोटिफिकेशन्स](https://app.clawmetry.com/push) सक्षम असल्यास
तुमच्या फोनवरून एका टॅपने):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

नकार दिल्यास फक्त तो एक टूल कॉल ब्लॉक होतो, एजंटचे सेशन तसेच राहते आणि तो
दुसरा मार्ग अवलंबू शकतो. तुमच्या फोनवरून मंजुरी दिल्यास Claude Code चा स्वतःचा
परवानगी प्रॉम्प्ट वगळला जातो (तुम्ही आधीच उत्तर दिले आहे). न जुळणाऱ्या टूल्सना
सुमारे 40ms लागतात आणि ते Claude Code च्या सामान्य परवानगी प्रवाहाकडे वळतात.
Claude Code स्वतः तुमची वाट पाहत असतानाही तुम्हाला फोन पुश मिळतो
(`permission_prompt` / `idle_prompt` सूचना).

## इन्स्टॉल

**एक-लायनर (शिफारस केलेले):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**सोर्समधून:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 फ्रंटएंड विकास

v2 React ॲप `frontend/` मध्ये आहे आणि v2 सक्षम करून Flask सर्व्हर
सुरू केल्यावर ते `/v2` वर सर्व्ह केले जाते.

विकास करताना दोन टर्मिनल्स वापरा:

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

`http://localhost:5173/v2/` उघडा. Vite `/api` विनंत्या
`http://localhost:8900` कडे प्रॉक्सी करते, त्यामुळे React ॲप अतिरिक्त
CORS सेटअपशिवाय स्थानिक Flask सर्व्हरशी बोलू शकते.

Python पॅकेजसोबत पाठवला जाणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रॉडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नव्हे तर अनेक AI-एजंट रनटाइम्सचे निरीक्षण करते. प्रत्येक OpenClaw-व्यतिरिक्त रनटाइम एक समर्पित रीडर अ‍ॅडाप्टर पाठवतो जो त्याच्या मूळ सेशन फॉरमॅटला ClawMetry च्या एकसंध शेप्समध्ये रूपांतरित करतो; डीमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये, रनटाइमसह टॅग करून, अंतर्भूत करतो, आणि जेव्हा एकापेक्षा जास्त रनटाइम्स उपस्थित असतात तेव्हा Session replay टॅब एक **रनटाइम स्विचर** दाखवतो. संपूर्ण मॅट्रिक्स + रनटाइम्स जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) पहा, आणि OpenClaw-फॅमिली प्रायमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

| रनटाइम / एजंट | स्थिती | टिपा |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप शोधले जाते |
| **PicoClaw** | बीटा अ‍ॅडाप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अ‍ॅडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + संदेश संख्या. |
| **Hermes** | बीटा अ‍ॅडाप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/खर्च. |
| **Claude Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स + थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अ‍ॅडाप्टर | रोलआउट JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अ‍ॅडाप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अ‍ॅडाप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन संख्या. |
| **Goose** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, एकूण टोकन्स. |
| **opencode** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Qwen Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा अ‍ॅडाप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Deep Agents** | बीटा अ‍ॅडाप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |

"बीटा अ‍ॅडाप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या डिस्कवरील फॉरमॅटसाठी एक रीडर पाठवते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलविरुद्ध तयार केलेला + पडताळलेला (`tests/fixtures/runtimes/<rt>/` पहा). अ‍ॅडाप्टर्स फक्त-वाचनीय आहेत; प्रत्येक त्याच्या रनटाइम खरोखर काय साठवते याबद्दल प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor टोकन खर्च डिस्कवर लिहीत नाहीत). एका नोडवर अनेक रनटाइम्स चालत असताना, रनटाइम स्विचर सेशन्स दृश्याला एका स्वच्छ सखोल-अभ्यासासाठी एका रनटाइमवर स्कोप करतो.

## कोणताही SDK एजंट ट्रॅक करा — आऊट-लूप खर्च श्रेय

वरील रनटाइम्स सर्व सेशन्स डिस्कवर लिहितात. तुमचा स्वतःचा **प्रॉडक्शन एजंट**, जो तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा साधा `httpx` लूप वापरून बनवला आहे, तो लिहीत नाही. ClawMetry चा शून्य-कॉन्फिग इंटरसेप्टर `httpx`/`requests` वर मंकी-पॅचिंग करून त्याचे LLM कॉल्स (खर्च, टोकन्स, लेटन्सी, एरर्स) तरीही कॅप्चर करतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` एन्व्ह व्हेरिएबल) प्रत्येक कॉलला एका **नामांकित स्रोताने** टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक उत्पादन डॅशबोर्डच्या Overview वरील **🔌 आऊट-लूप स्रोत** कार्डमध्ये स्वतःची पहिल्या-दर्जाची, खर्च-श्रेय-देण्यायोग्य ओळ म्हणून दिसते, प्रति-एजंट कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. स्रोत सेट केला नाही? कॉल्स तरीही ट्रॅक होतात; कार्ड फक्त लपून राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

रनटाइम अ‍ॅडाप्टर्स ज्या डेटा लेयरला फीड करतात (DuckDB → क्लाउड स्नॅपशॉट) तीच ही आहे, त्यामुळे आऊट-लूप स्रोत इतर सर्व गोष्टींप्रमाणेच क्लाउड डॅशबोर्डशी, एंड-टू-एंड एन्क्रिप्टेड, सिंक होतात.

## OpenTelemetry — विक्रेता-निरपेक्ष, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry **GenAI सिमॅंटिक कन्व्हेन्शन्स** वापरून दोन्ही दिशांनी **OpenTelemetry** बोलते, त्यामुळे तुमचे एजंट ट्रेसेस कधीही एका टूलमध्ये लॉक होत नाहीत.

प्रत्येक सेशन, LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च, कोणत्याही कलेक्टरकडे (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्स्पोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल ऐच्छिक एन्व्ह व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीव्हर `/v1/traces` आणि `/v1/metrics` वर इतर कशाहीकडून ट्रेसेस आणि मेट्रिक्स स्वीकारतो (प्रोटोबफ इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला शून्य-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा टीम आधीच वापरत असलेल्या कोणत्याही बॅकएंडमध्ये तुमचा डेटा मिळतो, कोणतेही लॉक-इन नाही, इन्स्टॉल करण्यासाठी दुसरा एजंट नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणत्याही कॉन्फिगची गरज नसते. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स, आणि क्रॉन्स आपोआप शोधते.

तुम्हाला सानुकूलित करायचे असल्यास:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी ClawMetry लाइव्ह ॲक्टिव्हिटी दाखवते. तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेटअप केलेले चॅनेल्सच Flow डायग्राममध्ये दिसतात, कॉन्फिगर न केलेले आपोआप लपवले जातात.

Flow मधील कोणत्याही चॅनेल नोडवर क्लिक करून येणाऱ्या/जाणाऱ्या संदेश संख्येसह लाइव्ह चॅट बबल दृश्य पहा.

| चॅनेल | स्थिती | लाइव्ह पॉपअप | टिपा |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आकडेवारी, 10s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचते |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) द्वारे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli द्वारे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चॅनेल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चॅनेल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API द्वारे iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहूक्स द्वारे |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन द्वारे |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चॅट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DM |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचते आणि तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल्सच रेंडर करते. कोणतेही मॅन्युअल सेटअप आवश्यक नाही.

## Docker डिप्लॉयमेंट

ClawMetry ला कंटेनरमध्ये चालवायचे आहे? काही अडचण नाही! 🐳

**Docker सह क्विक स्टार्ट:**

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

> **टीप:** Docker मध्ये चालवताना, ClawMetry तुमचा सेटअप आपोआप शोधू शकेल यासाठी तुमच्या एजंटची डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, किंवा Deep Agents (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry आपोआप [NemoClaw](https://github.com/NVIDIA/NemoClaw) शोधते, NVIDIA चा एंटरप्राइझ सुरक्षा रॅपर जो OpenClaw एजंट्सना सँडबॉक्स्ड OpenShell कंटेनर्समध्ये चालवतो.

बहुतेक प्रकरणांमध्ये कोणत्याही अतिरिक्त कॉन्फिगरेशनची गरज नाही. सेशन फाइल्स होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरच्या आत, सिंक डीमन त्या आपोआप शोधतो.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे शोधते:

1. **बायनरी डिटेक्शन** — `nemoclaw` CLI ची तपासणी करते आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवते
2. **कंटेनर डिटेक्शन** — चालू असलेल्या Docker कंटेनर्समध्ये `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी स्कॅन करते, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचते

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्सना क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटाने टॅग केले जाते, त्यामुळे तुम्ही त्यांना नेहमीच्या OpenClaw सेशन्सपासून एका दृष्टीक्षेपात वेगळे ओळखू शकता.

### शिफारस केलेला सेटअप: होस्टवर सिंक डीमन

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डीमन **होस्ट मशीनवर** चालवा (सँडबॉक्सच्या आत नाही). हे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळते.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डीमन कोणत्याही चालू असलेल्या OpenShell कंटेनर्सच्या आत सेशन्स आपोआप शोधेल.

### ऐच्छिक: स्पष्ट सँडबॉक्स नाव

ऑटो-डिटेक्शन काम करत नसल्यास, ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

तुम्हाला सिंक डीमन OpenShell सँडबॉक्सच्या **आत** चालवायचा असल्यास, ते ClawMetry इनजेस्ट API पर्यंत पोहोचू शकेल यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा एग्रेस नियम जोडा:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

लागू करा:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट्स आणि एंडपॉइंट्स

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | आवश्यक |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डीमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (स्थानिक डॅशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन शोधण्यासाठी |

सिंक डीमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. कोणत्याही इनबाउंड पोर्ट्सची गरज नाही.

---

## Cloud डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## चाचणी

हा प्रकल्प BrowserStack सह चाचणी केला आहे.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

तुम्ही नवीन मशीनवर पहिल्यांदा `clawmetry` CLI चालवता तेव्हा ClawMetry
`https://app.clawmetry.com/api/install` वर एकच अनामिक "फर्स्ट रन" पिंग
पाठवते. इन्स्टॉल्स मोजण्यासाठी (OSS प्रकल्पासाठी आमच्याकडे असलेले
एकमेव मार्केटिंग मेट्रिक) आणि आमच्या वापरकर्त्यांनी कोणते एजंट फ्रेमवर्क्स
इन्स्टॉल केले आहेत हे जाणून घेण्यासाठी आम्ही हे वापरतो.

**प्रति इन्स्टॉल नेमके एक POST**, यात असते:

| फील्ड | उदाहरण | कारण |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डुप्लिकेट टाळण्यासाठी; तुमच्या ईमेल किंवा api_key शी जोडलेला नाही |
| `version` | `0.12.167` | कोणत्या आवृत्त्या वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्ये |
| `python` | `3.11.15` | Python आवृत्ती समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | आम्ही पुढे कोणत्या एजंट्ससोबत एकीकरण करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्स आणि CI आवाज वेगळे करण्यासाठी |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर विनंतीवरून देश कोड
काढतो, नंतर IP टाकून देतो), होस्टनेम, युजरनेम, वर्कस्पेस पाथ, फाइल
कंटेंट्स, तुमची api_key, तुमचा ईमेल, कोणतेही PII किंवा वर्कस्पेस-विशिष्ट
काहीही. वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
मध्ये ऑडिटेबल आहे.

**ऑप्ट आउट** (यापैकी कोणतेही एक ते कायमचे अक्षम करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

येथील नेटवर्क अपयश `clawmetry` चालण्यास कधीही अडथळा आणत नाही, पिंग
डीमन थ्रेडवर 3 सेकंद टाइमआउटसह फायर-अँड-फर्गेट आहे.

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT

---

<p align="center">
  <strong>🦞 तुमचा एजंट कसा विचार करतो ते पहा</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> यांनी बनवले · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
