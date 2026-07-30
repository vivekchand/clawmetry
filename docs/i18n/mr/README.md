<!-- i18n-src:9a05336fbdc1 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पहा.** **१४ AI एजंट रनटाइम्स** साठी रिअल-टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी १०. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एकच कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप डिटेक्ट होते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि काम झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## १४ एजंट रनटाइम्ससोबत काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्व्हेबिलिटी म्हणून झाली, आणि आता ते **तुमचा संपूर्ण एजंट फ्लीट** एकाच डॅशबोर्डमध्ये मीटर करते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप डिटेक्ट करून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw आणि NemoClaw हे ओपन-सोर्स अ‍ॅपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम्स बदला आणि प्रत्येक टॅब — कॉस्ट, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमनुसार पुन्हा-स्कोप होतो. नेमका मोफत/पेड विभागणी, टियर मॅट्रिक्स, `/api/entitlement` शेप, आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, ब्रेन, टूल्स आणि परत यामधून वाहणारे मेसेजेस दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, अ‍ॅक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउनसह टोकन आणि कॉस्ट ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटच्या अ‍ॅक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्टेटस, पुढील रन, कालावधीसह शेड्यूल्ड जॉब्स
- **Logs** — रंग-कोडेड रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email कडे रूट होते
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुशेस, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉल्स, नेटवर्क कॉल्स एका क्लिकच्या साइन-ऑफमागे गेट करा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल-टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशननुसार कॉस्ट ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाइल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोश्चर आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट कॅप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email कडे वेबहूक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखमीचे टूल कॉल्स मॅन्युअल साइन-ऑफमागे गेट करा; धोरण-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी प्री-एक्झिक्युशन ब्लॉकिंग** — एक कमांड PreToolUse हूक इन्स्टॉल करते जी
जुळणारे टूल कॉल्स ते चालण्या *आधी* थांबवते आणि तुमच्या निर्णयाची वाट पाहते (तुमच्या फोनवरून
एका टॅपमध्ये [क्लाउड पुश नोटिफिकेशन्स](https://app.clawmetry.com/push) सक्षम केले असल्यास):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

नकार फक्त तो एक टूल कॉल ब्लॉक करतो — एजंट आपले सेशन ठेवतो आणि
दुसरा मार्ग वापरून पाहू शकतो. तुमच्या फोनवर मंजूर केल्यास Claude Code चा स्वतःचा
परवानगी प्रॉम्प्ट वगळला जातो (तुम्ही आधीच उत्तर दिलेले असते). न जुळणाऱ्या टूल्ससाठी
सुमारे ४० ms खर्च होतो आणि ते Claude Code च्या सामान्य परवानगी प्रवाहाकडे जातात.
Claude Code स्वतः तुमच्यावर थांबले असतानाही तुम्हाला फोन पुश मिळतो
(`permission_prompt` / `idle_prompt` नोटिफिकेशन्स).

## इन्स्टॉल

**वन-लाइनर (शिफारस केलेले):**
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

## v2 फ्रंटएंड डेव्हलपमेंट

v2 React अ‍ॅप `frontend/` मध्ये आहे आणि Flask सर्व्हर v2 सक्षम करून सुरू केल्यावर
`/v2` वर सर्व्ह केले जाते.

डेव्हलपमेंट करताना दोन टर्मिनल्स वापरा:

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
`http://localhost:8900` कडे प्रॉक्सी करते, त्यामुळे React अ‍ॅप अतिरिक्त CORS सेटअपशिवाय
लोकल Flask सर्व्हरशी बोलू शकते.

Python पॅकेजसोबत शिप होणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिले जाते.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नव्हे, तर अनेक AI-एजंट रनटाइम्स ऑब्झर्व्ह करते. प्रत्येक नॉन-OpenClaw रनटाइम एक समर्पित रीडर अ‍ॅडाप्टर शिप करते जो त्याच्या नेटिव्ह सेशन फॉरमॅटला ClawMetry च्या युनिफाइड शेप्समध्ये रूपांतरित करतो; डिमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये इनजेस्ट करतो, रनटाइमने टॅग करून, आणि Session replay टॅब एकापेक्षा जास्त उपस्थित असल्यास **रनटाइम स्विचर** दाखवतो. संपूर्ण मॅट्रिक्स + रनटाइम्स जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) आणि OpenClaw-फॅमिली प्राइमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

| रनटाइम / एजंट | स्थिती | नोंदी |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप डिटेक्ट होते |
| **PicoClaw** | बीटा अ‍ॅडाप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अ‍ॅडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्स्क्रिप्ट्स + मेसेज काउंट्स. |
| **Hermes** | बीटा अ‍ॅडाप्टर | SQLite `~/.hermes/state.db`. ट्रान्स्क्रिप्ट्स, मॉडेल, टोकन्स/कॉस्ट. |
| **Claude Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स + थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अ‍ॅडाप्टर | रोलआउट JSONL `~/.codex/sessions/...`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अ‍ॅडाप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्स्क्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अ‍ॅडाप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्स्क्रिप्ट्स, मॉडेल, टोकन काउंट्स. |
| **Goose** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/goose`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन एकूण. |
| **opencode** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/opencode`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + कॉस्ट. |
| **Qwen Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा अ‍ॅडाप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + कॉस्ट. |
| **Deep Agents** | बीटा अ‍ॅडाप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्स्क्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + कॉस्ट. |
| **n8n** | बीटा अ‍ॅडाप्टर | SQLite `~/.n8n/database.sqlite`. वर्कफ्लो एक्झिक्युशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, n8n जिथे रेकॉर्ड करते तिथे मॉडेल + टोकन्स. |

"बीटा अ‍ॅडाप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या ऑन-डिस्क फॉरमॅटसाठी एक रीडर शिप करते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलविरुद्ध बनवलेला + पडताळलेला (पहा `tests/fixtures/runtimes/<rt>/`). अ‍ॅडाप्टर्स रीड-ओन्ली आहेत; प्रत्येक आपल्या रनटाइमने प्रत्यक्षात डिस्कवर काय साठवले आहे याबाबत प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor टोकन कॉस्ट डिस्कवर लिहीत नाहीत). एका नोडवर अनेक रनटाइम्स चालत असताना, रनटाइम स्विचर सेशन्स व्ह्यूला एका स्वच्छ डीप-डाइव्हसाठी एका रनटाइमपुरते मर्यादित करतो.

## कोणताही SDK एजंट ट्रॅक करा — आउट-लूप कॉस्ट अ‍ॅट्रिब्युशन

वरील रनटाइम्स सर्व सेशन्स डिस्कवर लिहितात. तुमचा स्वतःचा **प्रोडक्शन एजंट** — जो तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा साध्या `httpx` लूपवर बनवला — तो लिहीत नाही. ClawMetry चा शून्य-कॉन्फिग इंटरसेप्टर `httpx`/`requests` ला मंकी-पॅच करून त्याचे LLM कॉल्स (कॉस्ट, टोकन्स, लेटन्सी, एरर्स) तरीही कॅप्चर करतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` एन्व्ह व्हेरिएबल) प्रत्येक कॉलला एका **नामित सोर्स** ने टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक प्रॉडक्ट डॅशबोर्डच्या Overview वरील **🔌 आउट-लूप सोर्सेस** कार्डमध्ये स्वतःची पहिल्या-दर्जाची, कॉस्ट-अ‍ॅट्रिब्युटेबल ओळ म्हणून दिसते — प्रति एजंट कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. सोर्स सेट केलेला नसेल? कॉल्स तरीही ट्रॅक होतात; कार्ड फक्त लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ही तीच डेटा लेयर आहे जी रनटाइम अ‍ॅडाप्टर्स फीड करतात (DuckDB → क्लाउड स्नॅपशॉट), त्यामुळे आउट-लूप सोर्सेस बाकी सर्व गोष्टींप्रमाणेच क्लाउड डॅशबोर्डशी सिंक होतात, E2E-एनक्रिप्टेड.

## OpenTelemetry — व्हेंडर-न्यूट्रल, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry **GenAI सिमॅंटिक कन्व्हेन्शन्स** वापरून दोन्ही दिशांना **OpenTelemetry** बोलतो, त्यामुळे तुमचे एजंट ट्रेसेस कधीच एका टूलमध्ये लॉक होत नाहीत.

प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, कॉस्ट — कोणत्याही कलेक्टरकडे (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्सपोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल हे पर्यायी एन्व्ह व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीव्हर `/v1/traces` आणि `/v1/metrics` वर इतर कोणत्याही ठिकाणाहून ट्रेसेस आणि मेट्रिक्स स्वीकारतो (प्रोटोबफ इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला शून्य-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा डेटा तुमची टीम आधीच चालवत असलेल्या कोणत्याही बॅकएंडमध्ये मिळतो — लॉक-इन नाही, दुसरा एजंट इन्स्टॉल करण्याची गरज नाही.

## कॉन्फिगरेशन

बहुतांश लोकांना कोणत्याही कॉन्फिगची गरज नाही. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स आणि क्रॉन्स आपोआप डिटेक्ट करते.

तुम्हाला कस्टमाइझ करायचे असल्यास:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

ClawMetry तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी लाइव्ह अ‍ॅक्टिव्हिटी दाखवते. तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेट केलेले चॅनेल्सच Flow डायग्राममध्ये दिसतात — कॉन्फिगर न केलेले आपोआप लपवले जातात.

Flow मध्ये कोणत्याही चॅनेल नोडवर क्लिक करून इनकमिंग/आउटगोइंग मेसेज काउंट्ससह लाइव्ह चॅट बबल व्ह्यू पहा.

| चॅनेल | स्थिती | लाइव्ह पॉपअप | नोंदी |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मेसेजेस, स्टॅट्स, १० सेकंद रिफ्रेश |
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
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रीकृत, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रीकृत NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **आपोआप डिटेक्शन:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचते आणि तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल्सच रेंडर करते. मॅन्युअल सेटअपची गरज नाही.

## Docker डिप्लॉयमेंट

ClawMetry कंटेनरमध्ये चालवायचे आहे? काही अडचण नाही! 🐳

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

> **टीप:** Docker मध्ये चालवताना, तुमच्या एजंटचा डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमचा सेटअप आपोआप डिटेक्ट करू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, किंवा n8n (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA चा एंटरप्राइझ सिक्युरिटी रॅपर जो सँडबॉक्स्ड OpenShell कंटेनर्समध्ये एजंट्स चालवतो — आपोआप डिटेक्ट करते.

बहुतांश प्रकरणांमध्ये अतिरिक्त कॉन्फिगरेशनची गरज नाही. सिंक डिमन सेशन फाइल्स आपोआप शोधतो, मग त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरच्या आत.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे डिटेक्ट करते:

1. **बायनरी डिटेक्शन** — `nemoclaw` CLI तपासते आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवते
2. **कंटेनर डिटेक्शन** — चालू असलेल्या Docker कंटेनर्समध्ये `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेस शोधते, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचते

NemoClaw कंटेनर्समधून सिंक झालेल्या सेशन फाइल्स क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केल्या जातात, त्यामुळे तुम्ही त्यांना एका दृष्टिक्षेपात स्टँडर्ड OpenClaw सेशन्सपासून वेगळे ओळखू शकता.

### शिफारस केलेला सेटअप: होस्टवर सिंक डिमन

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डिमन **होस्ट मशीन** वर चालवा (सँडबॉक्सच्या आत नाही). हे NemoClaw नेटवर्क धोरण निर्बंध टाळते.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डिमन कोणत्याही चालू असलेल्या OpenShell कंटेनर्सच्या आत असलेली सेशन्स आपोआप शोधेल.

### पर्यायी: स्पष्ट सँडबॉक्स नाव

आपोआप डिटेक्शन काम करत नसल्यास, ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

सिंक डिमन **सँडबॉक्सच्या आत** OpenShell मध्ये चालवायचा असल्यास, ते ClawMetry इनजेस्ट API पर्यंत पोहोचू शकेल यासाठी तुमच्या NemoClaw नेटवर्क धोरणात हा एग्रेस नियम जोडा:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

यासह लागू करा:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट्स आणि एंडपॉइंट्स

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | आवश्यक |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डिमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (लोकल डॅशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन शोधासाठी |

सिंक डिमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. इनबाउंड पोर्ट्सची गरज नाही.

---

## क्लाउड डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## टेस्टिंग

हा प्रोजेक्ट BrowserStack सह टेस्ट केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry नवीन मशीनवर `clawmetry` CLI पहिल्यांदा चालवल्यावर
`https://app.clawmetry.com/api/install` कडे एकच निनावी "फर्स्ट रन" पिंग पाठवते.
आम्ही याचा वापर इन्स्टॉल्स मोजण्यासाठी (OSS प्रोजेक्टसाठी असलेली एकमेव मार्केटिंग मेट्रिक)
आणि आमच्या वापरकर्त्यांनी कोणते एजंट फ्रेमवर्क्स इन्स्टॉल केले आहेत हे जाणून घेण्यासाठी करतो.

**प्रति इन्स्टॉल नेमके एक POST**, यामध्ये असते:

| फील्ड | उदाहरण | कारण |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डिडुप; तुमच्या ईमेल किंवा api_key शी जोडलेले नाही |
| `version` | `0.12.167` | कोणत्या व्हर्जन्स प्रत्यक्षात वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म सपोर्ट प्राधान्ये |
| `python` | `3.11.15` | Python व्हर्जन सपोर्ट मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | पुढे आम्ही कोणत्या एजंट्ससोबत इंटिग्रेट करायला हवे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्स आणि CI नॉईज वेगळे करणे |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर विनंतीतून कंट्री कोड मिळवते,
नंतर IP टाकून देते), होस्टनेम, युजरनेम, वर्कस्पेस
पाथ, फाइल कंटेंट्स, तुमची api_key, तुमचा ईमेल, PII किंवा
वर्कस्पेस-विशिष्ट काहीही. वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) मध्ये ऑडिट करण्यायोग्य आहे.

**ऑप्ट आउट** (यापैकी कोणतेही एक कायमचे बंद करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

नेटवर्क अपयश येथे `clawmetry` चालण्यात कधीही अडथळा आणत नाही — पिंग
३ सेकंद टाइमआउटसह डिमन थ्रेडवर फायर-अँड-फॉरगेट असते.

## स्टार इतिहास

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लायसन्स

MIT

---

<p align="center">
  <strong>🦞 तुमचा एजंट कसा विचार करतो ते पहा</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> द्वारे बनवलेले · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
