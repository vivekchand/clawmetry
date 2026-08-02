<!-- i18n-src:191e9094d7fa -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पाहा.** **14 AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी 10. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप शोधतो.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि तुमचे काम झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजंट रनटाइम्ससोबत काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्वेबिलिटी म्हणून झाली, आणि आता ते तुमच्या **संपूर्ण एजंट फ्लीट**चे मापन एकाच डॅशबोर्डमध्ये करते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप शोधून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw आणि NemoClaw हे ओपन-सोर्स ॲपमध्ये मोफत आहेत; उर्वरित रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम बदला, आणि प्रत्येक टॅब — कॉस्ट, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमसाठी पुन्हा-स्कोप होतो. नेमका फ्री/पेड विभाजन, टियर मॅट्रिक्स, `/api/entitlement` शेप आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, brain, टूल्स आणि परत यामधून वाहणारे संदेश दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, ॲक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउनसह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची ॲक्टिव्हिटी असलेली सक्रिय एजंट सेशन्स
- **Crons** — स्टेटस, पुढील रन, कालावधीसह शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनंदिन नोंदी ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन शोध; Slack, Discord, PagerDuty, Telegram, Email कडे रूट करते
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुश, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉल्स, नेटवर्क कॉल्स एका-क्लिकच्या साइन-ऑफमागे गेट करा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल-टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशननुसार खर्च ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाइल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोश्चर आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट कॅप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email कडे वेबहूक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखमीचे टूल कॉल्स मॅन्युअल साइन-ऑफमागे गेट करा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी प्री-एक्झिक्युशन ब्लॉकिंग** — एक कमांड जुळणारे टूल
कॉल्स *चालण्यापूर्वीच* थांबवणारा आणि तुमच्या निर्णयाची वाट पाहणारा PreToolUse
हूक इन्स्टॉल करते ([cloud push notifications](https://app.clawmetry.com/push)
सक्षम असल्यास तुमच्या फोनवरून एका टॅपमध्ये):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

नकार फक्त त्या एका टूल कॉलला ब्लॉक करतो — एजंट आपले सेशन कायम ठेवतो आणि
दुसरा दृष्टिकोन वापरून पाहू शकतो. तुमच्या फोनवर मंजूर केल्याने Claude Code चा
स्वतःचा परवानगी प्रॉम्प्ट वगळला जातो (तुम्ही आधीच उत्तर दिलेले असते).
न जुळणाऱ्या टूल्सना सुमारे 40ms खर्च येतो आणि ते Claude Code च्या नेहमीच्या
परवानगी फ्लोमध्ये पडतात. Claude Code स्वतः तुमची वाट पाहत असतानाही तुम्हाला
फोन पुश मिळतो (`permission_prompt` / `idle_prompt` सूचना).

## इन्स्टॉल करा

**वन-लायनर (शिफारस केलेले):**
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

v2 React ॲप `frontend/` मध्ये आहे आणि v2 सक्षम करून Flask सर्व्हर सुरू
केल्यावर `/v2` वर सर्व्ह केले जाते.

डेव्हलप करताना दोन टर्मिनल्स वापरा:

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
CORS सेटअपशिवाय लोकल Flask सर्व्हरशी बोलू शकते.

Python पॅकेजसोबत शिप होणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रॉडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिले जाते.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नव्हे तर अनेक AI-एजंट रनटाइम्सचे निरीक्षण करते.
प्रत्येक OpenClaw-नसलेला रनटाइम एक समर्पित रीडर ॲडॅप्टर शिप करतो जो त्या
रनटाइमचा नेटिव्ह सेशन फॉर्मॅट ClawMetry च्या एकसंध शेप्समध्ये रूपांतरित
करतो; डिमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये इनजेस्ट करतो,
रनटाइमसह टॅग करून, आणि एकापेक्षा जास्त रनटाइम्स उपस्थित असताना Session
replay टॅबमध्ये **रनटाइम स्विचर** दाखवला जातो. संपूर्ण मॅट्रिक्स + रनटाइम्स
जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md)
आणि OpenClaw-फॅमिली प्रायमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

[Perplexity चे numbat](https://github.com/perplexityai/numbat) एजंट-सुरक्षा टूल वापरत आहात? ClawMetry त्याचे फाइंडिंग्स आणि एन्फोर्समेंट निर्णय जशाच्या तशा इनजेस्ट करते — पाहा [`docs/NUMBAT.md`](docs/NUMBAT.md).

| रनटाइम / एजंट | स्थिती | टिपा |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप शोधले जाते |
| **PicoClaw** | बीटा ॲडॅप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा ॲडॅप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + संदेश संख्या. |
| **Hermes** | बीटा ॲडॅप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/खर्च. |
| **Claude Code** | बीटा ॲडॅप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स + thinking, टोकन वापर. |
| **Codex** | बीटा ॲडॅप्टर | रोलआउट JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा ॲडॅप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा ॲडॅप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन काउंट्स. |
| **Goose** | बीटा ॲडॅप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, एकूण टोकन्स. |
| **opencode** | बीटा ॲडॅप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Qwen Code** | बीटा ॲडॅप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा ॲडॅप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Deep Agents** | बीटा ॲडॅप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **n8n** | बीटा ॲडॅप्टर | SQLite `~/.n8n/database.sqlite`. वर्कफ्लो एक्झिक्युशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, n8n नोंदवते तिथे मॉडेल + टोकन्स. |
| **Antigravity** | बीटा ॲडॅप्टर | `~/.gemini/<flavor>/brain/` अंतर्गत Brain JSONL. संभाषणे, टूल स्टेप्स, thinking, प्रति-जनरेशन Gemini टोकन विभाजन + खर्च, बॅकग्राउंड-जनरेशन बर्न. |

"बीटा ॲडॅप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या ऑन-डिस्क फॉर्मॅटसाठी
रीडर शिप करते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलविरुद्ध तयार + पडताळलेला
(`tests/fixtures/runtimes/<rt>/` पहा). ॲडॅप्टर्स रीड-ओन्ली आहेत; प्रत्येक
आपला रनटाइम प्रत्यक्षात डिस्कवर काय साठवतो याबाबत प्रामाणिक आहे (उदा.
PicoClaw/NanoClaw/Cursor डिस्कवर टोकन खर्च लिहीत नाहीत). एका नोडवर अनेक
रनटाइम्स चालत असताना, रनटाइम स्विचर सेशन्स व्ह्यूला स्वच्छ डीप-डाइव्हसाठी
एकावर स्कोप करतो.

## कोणत्याही SDK एजंटला ट्रॅक करा — आउट-लूप खर्च अट्रिब्युशन

वरील रनटाइम्स सर्व सेशन्स डिस्कवर लिहितात. तुमचा स्वतःचा **प्रॉडक्शन एजंट**
— जो तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B,
किंवा साधा `httpx` लूप वापरून बनवला आहे — तसे करत नाही. ClawMetry चा
झिरो-कॉन्फिग इंटरसेप्टर तरीही `httpx`/`requests` ला मंकी-पॅच करून त्याचे
LLM कॉल्स (खर्च, टोकन्स, लेटन्सी, एरर्स) कॅप्चर करतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` env व्हेरिएबल)
प्रत्येक कॉलला **नामांकित स्रोत**ने टॅग करतो, त्यामुळे तुम्ही चालवत असलेले
प्रत्येक प्रॉडक्ट Overview च्या **🔌 Out-loop sources** कार्डावर स्वतःची
पहिल्या-वर्गाची, खर्च-अट्रिब्यूटेबल ओळ म्हणून दिसते — प्रति एजंट कॉल्स,
प्रोव्हायडर्स, लेटन्सी, एरर रेट. स्रोत सेट केलेला नाही? कॉल्स तरीही
ट्रॅक होतातच; कार्ड फक्त लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

हा तोच डेटा लेयर आहे जो रनटाइम ॲडॅप्टर्स फीड करतात (DuckDB → क्लाउड
स्नॅपशॉट), त्यामुळे आउट-लूप स्रोत बाकी सर्व गोष्टींप्रमाणेच, E2E-एन्क्रिप्टेड
पद्धतीने क्लाउड डॅशबोर्डशी सिंक होतात.

## OpenTelemetry — व्हेंडर-न्यूट्रल, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry दोन्ही दिशांनी **OpenTelemetry** बोलते, **GenAI सिमँटिक
कन्व्हेन्शन्स** वापरून, त्यामुळे तुमचे एजंट ट्रेसेस कधीही एकाच टूलमध्ये
लॉक-इन होत नाहीत.

प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च — कोणत्याही
कलेक्टरकडे (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel
Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्सपोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटर्व्हल हे ऐच्छिक env व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीव्हर इतर कोणत्याही स्रोतांकडून
`/v1/traces` आणि `/v1/metrics` वर ट्रेसेस आणि मेट्रिक्स स्वीकारतो
(protobuf इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला झिरो-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमच्या
टीमकडे आधीच असलेल्या बॅकएंडमध्ये तुमचा डेटा दोन्ही मिळतात — लॉक-इन नाही,
इन्स्टॉल करण्यासाठी दुसरा एजंट नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणत्याही कॉन्फिगची गरज नसते. ClawMetry तुमचा वर्कस्पेस,
लॉग्स, सेशन्स आणि क्रॉन्स आपोआप शोधतो.

जर तुम्हाला कस्टमाइझ करायचे असेल तर:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

ClawMetry तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी लाइव्ह
ॲक्टिव्हिटी दाखवते. तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेटअप
केलेले चॅनेलच Flow डायग्राममध्ये दिसतात — कॉन्फिगर न केलेले आपोआप लपवले
जातात.

Flow मधील कोणत्याही चॅनेल नोडवर क्लिक केल्यास येणाऱ्या/जाणाऱ्या संदेश
संख्येसह लाइव्ह चॅट बबल व्ह्यू दिसतो.

| चॅनेल | स्थिती | लाइव्ह पॉपअप | टिपा |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आकडेवारी, 10s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचते |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) मार्गे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli मार्गे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चॅनेल शोध |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चॅनेल शोध |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-शैली बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API मार्गे iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहूक्समार्गे |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइनमार्गे |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चॅट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **आपोआप शोध:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचतो आणि
> तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल्सच रेंडर करतो. मॅन्युअल सेटअपची
> गरज नाही.

## Docker डिप्लॉयमेंट

ClawMetry कंटेनरमध्ये चालवायचे आहे? काहीच अडचण नाही! 🐳

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

> **टीप:** Docker मध्ये चालवताना, तुमचा एजंटचा डेटा + लॉग डिरेक्टरीज
> (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून
> ClawMetry तुमचा सेटअप आपोआप शोधू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, किंवा Antigravity (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA चे
OpenClaw साठी एंटरप्राइझ सुरक्षा रॅपर जे एजंट्सना सँडबॉक्स केलेल्या
OpenShell कंटेनर्समध्ये चालवते — आपोआप शोधतो.

बहुतेक प्रकरणांत अतिरिक्त कॉन्फिगरेशनची गरज नाही. सिंक डिमन सेशन फाइल्स
आपोआप शोधतो, मग त्या होस्टवर `~/.openclaw/` मध्ये असोत किंवा OpenShell
कंटेनरच्या आत.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे शोधतो:

1. **बायनरी शोध** — `nemoclaw` CLI तपासतो आणि सँडबॉक्स माहितीसाठी
   `nemoclaw status` चालवतो
2. **कंटेनर शोध** — चालू Docker कंटेनर्समध्ये `openshell`, `nemoclaw`,
   किंवा `ghcr.io/nvidia/` इमेजेस स्कॅन करतो, नंतर व्हॉल्यूम माउंट्स
   किंवा `docker cp` द्वारे सेशन्स वाचतो

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्सला क्लाउड डॅशबोर्डमध्ये
`runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केले जाते, त्यामुळे
तुम्ही एका नजरेत त्यांना स्टँडर्ड OpenClaw सेशन्सपासून वेगळे ओळखू शकता.

### शिफारस केलेला सेटअप: होस्टवर सिंक डिमन

सर्वोत्तम अनुभवासाठी, ClawMetry चे सिंक डिमन **होस्ट मशीन**वर (सँडबॉक्सच्या
आत नव्हे) चालवा. हे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळते.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डिमन कोणत्याही चालू असलेल्या OpenShell कंटेनर्समधील सेशन्स आपोआप
शोधेल.

### ऐच्छिक: स्पष्ट सँडबॉक्स नाव

आपोआप शोध काम करत नसल्यास, ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

जर तुम्हाला सिंक डिमन **सँडबॉक्सच्या आत** चालवायचे असेल, तर ते
ClawMetry ingest API पर्यंत पोहोचू शकेल यासाठी तुमच्या NemoClaw नेटवर्क
पॉलिसीमध्ये हा egress नियम जोडा:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

लागू करण्यासाठी:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट्स आणि एंडपॉइंट्स

| एंडपॉइंट | पोर्ट | प्रोटोकॉल | आवश्यक |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डिमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (लोकल डॅशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन शोधासाठी |

सिंक डिमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो.
कोणत्याही इनबाउंड पोर्ट्सची गरज नाही.

---

## क्लाउड डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## चाचणी

हा प्रोजेक्ट BrowserStack सह चाचणी केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry `https://app.clawmetry.com/api/install` कडे निनावी
इन्स्टॉल-लाइफसायकल पिंग्स पाठवते: नवीन मशीनवर `clawmetry` CLI पहिल्यांदा
चालवल्यावर एक `install` पिंग, नवीन व्हर्जनमध्ये अपग्रेड केल्यानंतरच्या
पहिल्या रनवर एक `update` पिंग, आणि तुम्ही डॅशबोर्डमधील ऑनबोर्डिंग निवड
पूर्ण केल्यावर एक `onboarded` पिंग. आम्ही याचा वापर खऱ्या इन्स्टॉल्सची
संख्या मोजण्यासाठी करतो (कच्च्या PyPI डाउनलोड संख्या सुमारे 98% मिरर्स,
CI, आणि ऑटो-अपडेट री-डाउनलोड्स असतात) आणि प्रत्यक्षात कोणते एजंट
फ्रेमवर्क्स आणि व्हर्जन्स वापरात आहेत हे जाणून घेण्यासाठी.

**प्रति लाइफसायकल इव्हेंट प्रति व्हर्जन जास्तीत जास्त एक POST**, ज्यात
हे असते:

| फील्ड | उदाहरण | कारण |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डिड्युप; तुम्ही स्पष्टपणे Cloud sync कनेक्ट करेपर्यंत निनावी (त्यानंतर ऑथेंटिकेटेड डिमन हार्टबीट हे वाहून नेतो, हे इन्स्टॉल तुमच्या खात्याशी जोडते) |
| `event` | `install` / `update` / `onboarded` | नवीन इन्स्टॉल विरुद्ध अस्तित्वात असलेल्याचे अपग्रेड |
| `version` | `0.12.167` | वापरात कोणती व्हर्जन्स आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्ये |
| `python` | `3.11.15` | Python व्हर्जन समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | पुढे कोणत्या एजंट्ससोबत आम्ही इंटिग्रेट करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्स आणि CI आवाज वेगळे करणे |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर विनंतीतून देश कोड
काढतो, नंतर IP टाकून देतो), होस्टनेम, युजरनेम, वर्कस्पेस पाथ, फाइल
कंटेंट, तुमची api_key, तुमचा ईमेल, कोणतीही PII किंवा वर्कस्पेस-विशिष्ट
माहिती. वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
मध्ये ऑडिट करण्यायोग्य आहे.

**ऑप्ट आउट** (यापैकी कोणताही एक ते कायमचे बंद करतो):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

येथे नेटवर्क अपयश कधीही `clawmetry` चालण्यास अडथळा आणत नाही — पिंग
डिमन थ्रेडवर 3 सेकंद टाइमआउटसह फायर-अँड-फर्गेट आहे.

## Star History

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
  <strong>🦞 तुमचा एजंट कसा विचार करतो ते पाहा</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> यांनी तयार केले · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
