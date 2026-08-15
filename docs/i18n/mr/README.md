<!-- i18n-src:c422fb7dd0da -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पाहा.** **२० AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी १६. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्वकाही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## २० एजंट रनटाइम्ससोबत काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्वेबिलिटी म्हणून झाली आणि आता ते एकाच डॅशबोर्डमध्ये तुमच्या **संपूर्ण एजंट फ्लीटचे** मापन करते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप शोधून काढते:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw आणि NemoClaw हे ओपन-सोर्स ॲपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम बदला आणि प्रत्येक टॅब — खर्च, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमनुसार पुन्हा-स्कोप होतो. नेमका मोफत/पेड विभाग, टियर मॅट्रिक्स, `/api/entitlement` शेप, आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पाहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, ब्रेन, टूल्स आणि परत यामधून वाहणारे मेसेजेस दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, अ‍ॅक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक विभागणीसह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची अ‍ॅक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्थिती, पुढील रन, कालावधीसह शेड्युल्ड जॉब्स
- **Logs** — रंगकोड केलेले रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, ईमेलकडे मार्गस्थ करते
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुश, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉलेशन्स, नेटवर्क कॉल्स एका क्लिकच्या मंजुरीमागे थांबवा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल-टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशननुसार खर्च विभागणी
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाइल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोश्चर आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट कॅप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / ईमेलसाठी वेबहूक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखमीचे टूल कॉल्स मॅन्युअल सही-मंजुरीमागे थांबवा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी अंमलबजावणी-पूर्व ब्लॉकिंग** — एक कमांड जुळणारे टूल कॉल्स
*चालण्याआधीच* थांबवणारा आणि तुमच्या निर्णयाची वाट पाहणारा PreToolUse hook
इन्स्टॉल करते ([क्लाउड पुश नोटिफिकेशन्स](https://app.clawmetry.com/push)
सक्षम असल्यास तुमच्या फोनवरून एका टॅपमध्ये):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

नकार दिल्यास फक्त तेवढाच टूल कॉल ब्लॉक होतो — एजंटचे सेशन तसेच राहते आणि तो
दुसरा मार्ग वापरून पाहू शकतो. तुमच्या फोनवरून मंजुरी दिल्यास Claude Code च्या
स्वतःच्या परमिशन प्रॉम्प्टला वगळले जाते (तुम्ही आधीच उत्तर दिलेले असते).
न जुळणाऱ्या टूल्सना सुमारे ४० मिलिसेकंद खर्च येतो आणि ते Claude Code च्या
नेहमीच्या परमिशन फ्लोमध्ये जातात. Claude Code स्वतः तुमच्यावर थांबले असतानाही
तुम्हाला फोन पुश मिळतो (`permission_prompt` / `idle_prompt` नोटिफिकेशन्स).

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

v2 React ॲप `frontend/` मध्ये राहतो आणि Flask सर्व्हर v2 सक्षम करून
सुरू केला असता `/v2` वर सर्व्ह केला जातो.

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

`http://localhost:5173/v2/` उघडा. Vite `/api` रिक्वेस्ट्स
`http://localhost:8900` कडे प्रॉक्सी करते, त्यामुळे React ॲप
अतिरिक्त CORS सेटअपशिवाय लोकल Flask सर्व्हरशी बोलू शकतो.

Python पॅकेजसोबत पाठवला जाणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नव्हे तर अनेक AI-एजंट रनटाइम्सचे निरीक्षण करते. प्रत्येक नॉन-OpenClaw रनटाइमसाठी समर्पित रीडर अडॅप्टर पुरवला जातो जो त्या रनटाइमच्या मूळ सेशन फॉरमॅटला ClawMetry च्या एकसंध शेप्समध्ये भाषांतरित करतो; डीमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये, रनटाइमने टॅग करून, इनजेस्ट करतो, आणि एकापेक्षा जास्त रनटाइम्स असताना Session replay टॅबमध्ये **रनटाइम स्विचर** दिसतो. संपूर्ण मॅट्रिक्स + रनटाइम्स जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) पाहा, आणि OpenClaw-फॅमिली प्राइमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पाहा.

[Perplexity चे numbat](https://github.com/perplexityai/numbat) हे एजंट-सुरक्षा टूल वापरत आहात? ClawMetry त्याचे निष्कर्ष आणि अंमलबजावणी निर्णय आधीपासूनच इनजेस्ट करते — [`docs/NUMBAT.md`](docs/NUMBAT.md) पाहा.

| रनटाइम / एजंट | स्थिती | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप शोधले जाते |
| **PicoClaw** | बीटा अडॅप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अडॅप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + मेसेज काउंट्स. |
| **Hermes** | बीटा अडॅप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/खर्च. |
| **Claude Code** | बीटा अडॅप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स + थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अडॅप्टर | रोलआउट JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अडॅप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अडॅप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन काउंट्स. |
| **Goose** | बीटा अडॅप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन एकूण. |
| **opencode** | बीटा अडॅप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Qwen Code** | बीटा अडॅप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा अडॅप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Deep Agents** | बीटा अडॅप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **n8n** | बीटा अडॅप्टर | SQLite `~/.n8n/database.sqlite`. वर्कफ्लो एक्झिक्युशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, n8n जिथे नोंदवते तिथे मॉडेल + टोकन्स. |
| **Antigravity** | बीटा अडॅप्टर | `~/.gemini/<flavor>/brain/` खाली ब्रेन JSONL. संभाषणे, टूल स्टेप्स, थिंकिंग, प्रति-जनरेशन Gemini टोकन विभागणी + खर्च, बॅकग्राउंड-जनरेशन बर्न. |
| **GitHub Copilot** | बीटा अडॅप्टर | Copilot CLI चे `events.jsonl` `~/.copilot/session-state/` खाली + प्रति-कॉल वापर लेजर असणारा `session-store.db`. संभाषणे, टूल कॉल्स, मॉडेल राउटिंग, कॅश-जागरूक टोकन विभागणी, विक्रेता-बिल्ड AI-क्रेडिट खर्च. |
| **Grok** | बीटा अडॅप्टर | xAI Grok Build CLI (`~/.grok/bin/grok` खालील Rust बायनरी): ग्लोबल इव्हेंट लॉग `~/.grok/logs/unified.jsonl` + प्रति-सेशन `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. संभाषणे, प्रति-टर्न टोकन विभागणी, मॉडेल राउटिंग, आणि तुमच्या मशीनमधून काय बाहेर गेले हे दिसावे यासाठी `~/.grok/upload_queue/` खाली स्टेज केलेला CLI चा आउटबाउंड रिपो पेलोड. |

"बीटा अडॅप्टर" म्हणजे ClawMetry त्या रनटाइमच्या डिस्कवरील खऱ्या फॉरमॅटसाठी रीडर पाठवते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलविरुद्ध तयार + पडताळलेला (पाहा `tests/fixtures/runtimes/<rt>/`). अडॅप्टर्स रीड-ओन्ली आहेत; प्रत्येक त्या रनटाइमने प्रत्यक्षात काय साठवले आहे याबाबत प्रामाणिक असतो (उदा. PicoClaw/NanoClaw/Cursor डिस्कवर टोकन खर्च लिहीत नाहीत). एका नोडवर अनेक रनटाइम्स चालत असताना, रनटाइम स्विचर सेशन्स व्ह्यूला स्वच्छ डीप-डाइव्हसाठी एका रनटाइमपुरता स्कोप करतो.

## कोणताही SDK एजंट ट्रॅक करा — आउट-लूप खर्च गुणधर्म

वरील रनटाइम्स सर्व सेशन्स डिस्कवर लिहितात. तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा साध्या `httpx` लूपवर बनवलेला तुमचा स्वतःचा **प्रोडक्शन एजंट** असे करत नाही. ClawMetry चा शून्य-कॉन्फिग इंटरसेप्टर `httpx`/`requests` वर मंकी-पॅचिंग करून त्याचे LLM कॉल्स (खर्च, टोकन्स, लेटन्सी, एरर्स) तरीही टिपतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` env व्हेरिएबल) प्रत्येक कॉलला एका **नामांकित स्रोता**सह टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक प्रोडक्ट डॅशबोर्डच्या Overview मधील **🔌 आउट-लूप स्रोत** कार्डमध्ये स्वतःची पहिल्या-दर्जाची, खर्च-गुणधर्म देण्यायोग्य ओळ म्हणून दिसते — प्रति-एजंट कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. स्रोत सेट केला नसेल? कॉल्स तरीही ट्रॅक होतात; फक्त कार्ड लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

रनटाइम अडॅप्टर्स ज्या डेटा लेयरवर चालतात (DuckDB → क्लाउड स्नॅपशॉट) हा तोच लेयर आहे, त्यामुळे आउट-लूप स्रोत बाकी सगळ्याप्रमाणेच, E2E-एनक्रिप्टेड पद्धतीने क्लाउड डॅशबोर्डशी सिंक होतात.

## OpenTelemetry — विक्रेता-निरपेक्ष, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry दोन्ही दिशांनी **OpenTelemetry** बोलतो, **GenAI सिमॅंटिक कन्व्हेन्शन्स** वापरून, त्यामुळे तुमचे एजंट ट्रेसेस कधीही एका टूलमध्ये लॉक होत नाहीत.

प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च — कोणत्याही कलेक्टरला (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्सपोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल हे ऐच्छिक env व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — अंगभूत OTLP रिसीव्हर `/v1/traces`, `/v1/logs`, आणि `/v1/metrics` वर इतर कोणत्याही स्रोतापासून ट्रेसेस, लॉग्स आणि मेट्रिक्स स्वीकारतो. कोणतेही OpenTelemetry-इन्स्ट्रुमेंटेड ॲप त्याकडे पॉइंट करा:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON ट्रेसेस आणि लॉग्स साध्या `pip install clawmetry` वर काम करतात, कोणत्याही एक्स्ट्राशिवाय. Protobuf इनजेस्ट (आणि OTLP/JSON मेट्रिक्स) साठी `pip install clawmetry[otel]` लागते. स्वतःचे `service.name` सेट करणारे ॲप रनटाइम स्विचरमध्ये स्वतःचा एजंट म्हणून, स्वतःच्या खर्च आणि टोकन्ससह दिसते.

तुम्हाला शून्य-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा डेटा तुमची टीम आधीच चालवत असलेल्या कोणत्याही बॅकएंडमध्ये मिळतो — कोणतेही लॉक-इन नाही, दुसरा एजंट इन्स्टॉल करण्याची गरज नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणत्याही कॉन्फिगची गरज नसते. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स, आणि क्रॉन्स आपोआप शोधते.

तुम्हाला कस्टमाइझ करायचे असल्यास:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी ClawMetry लाइव्ह अ‍ॅक्टिव्हिटी दाखवतो. तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेट अप केलेले चॅनेल्सच Flow डायग्राममध्ये दिसतात — कॉन्फिगर न केलेले आपोआप लपवले जातात.

Flow मधील कोणत्याही चॅनेल नोडवर क्लिक करून येणाऱ्या/जाणाऱ्या मेसेज काउंट्ससह लाइव्ह चॅट बबल व्ह्यू पाहा.

| चॅनेल | स्थिती | लाइव्ह पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मेसेजेस, स्टॅट्स, १० सेकंद रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचते |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) द्वारे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli द्वारे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चॅनेल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चॅनेल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | अंगभूत वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-शैलीतील बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API द्वारे iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहूक्सद्वारे |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइनद्वारे |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चॅट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचतो आणि तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल्सच रेंडर करतो. मॅन्युअल सेटअपची गरज नाही.

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

> **टीप:** Docker मध्ये चालवताना, तुमचा एजंटची डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमचे सेटअप आपोआप शोधू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवरील AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, किंवा QM (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) — OpenShell कंटेनर्समध्ये सँडबॉक्स्ड पद्धतीने एजंट्स चालवणारे NVIDIA चे OpenClaw साठीचे एंटरप्राइझ सुरक्षा रॅपर — आपोआप शोधतो.

बहुतेक प्रकरणांमध्ये अतिरिक्त कॉन्फिगरेशनची गरज नसते. सिंक डीमन सेशन फाइल्स आपोआप शोधतो, मग त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरच्या आत.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे शोधतो:

1. **बायनरी डिटेक्शन** — `nemoclaw` CLI तपासतो आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवतो
2. **कंटेनर डिटेक्शन** — चालू असलेल्या Docker कंटेनर्समध्ये `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी स्कॅन करतो, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचतो

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्सना क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केले जाते, जेणेकरून तुम्ही त्यांना एका दृष्टीक्षेपात प्रमाणित OpenClaw सेशन्सपासून वेगळे ओळखू शकाल.

### शिफारस केलेले सेटअप: होस्टवर सिंक डीमन

उत्तम अनुभवासाठी, ClawMetry चा सिंक डीमन **होस्ट मशीनवर** चालवा (सँडबॉक्सच्या आत नाही). हे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळते.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डीमन कोणत्याही चालू OpenShell कंटेनर्सच्या आतील सेशन्स आपोआप शोधेल.

### ऐच्छिक: स्पष्ट सँडबॉक्स नाव

ऑटो-डिटेक्शन काम करत नसल्यास, ClawMetry ला योग्य सँडबॉक्सकडे पॉइंट करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

सिंक डीमन **सँडबॉक्सच्या आत** OpenShell मध्ये चालवावाच लागल्यास, त्याला ClawMetry ingest API पर्यंत पोहोचता यावे यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा एग्रेस नियम जोडा:

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
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डीमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (लोकल डॅशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | कंटेनर सेशन डिस्कव्हरीसाठी |

सिंक डीमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. कोणत्याही इनबाउंड पोर्ट्सची गरज नाही.

---

## क्लाउड डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पाहा.

## चाचणी

हा प्रोजेक्ट BrowserStack सह टेस्ट केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry `https://app.clawmetry.com/api/install` कडे निनावी
इन्स्टॉल-लाइफसायकल पिंग्स पाठवते: नवीन मशीनवर `clawmetry` CLI पहिल्यांदा
चालवल्यावर एक `install` पिंग, नव्या व्हर्जनमध्ये अपग्रेड केल्यावर पहिल्या
रनला एक `update` पिंग, आणि तुम्ही डॅशबोर्डमधील ऑनबोर्डिंग निवड पूर्ण
केल्यावर एक `onboarded` पिंग. आम्ही याचा वापर खऱ्या इन्स्टॉल्सची गणना
करण्यासाठी करतो (कच्चे PyPI डाउनलोड आकडे ~९८% मिरर्स, CI, आणि
ऑटो-अपडेट पुनर्डाउनलोड्स असतात) आणि प्रत्यक्षात कोणते एजंट फ्रेमवर्क्स
आणि व्हर्जन्स वापरात आहेत हे जाणून घेण्यासाठी करतो.

**प्रत्येक व्हर्जनसाठी प्रति-लाइफसायकल-इव्हेंट जास्तीत जास्त एक POST**, ज्यात हे असते:

| फील्ड | उदाहरण | कारण |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डिडुप; तुम्ही स्पष्टपणे Cloud sync कनेक्ट करेपर्यंत निनावी (त्यानंतर ऑथेंटिकेटेड डीमन हार्टबीट तो वाहून नेतो, हा इन्स्टॉल तुमच्या खात्याशी जोडतो) |
| `event` | `install` / `update` / `onboarded` | नवीन इन्स्टॉल विरुद्ध विद्यमानचे अपग्रेड |
| `version` | `0.12.167` | कोणती व्हर्जन्स वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्यक्रम |
| `python` | `3.11.15` | Python व्हर्जन समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | पुढे आम्ही कोणत्या एजंट्ससोबत इंटिग्रेट करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्स आणि CI आवाज वेगळे करण्यासाठी |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर रिक्वेस्टमधून देश
कोड मिळवतो, नंतर IP टाकून देतो), होस्टनेम, युजरनेम, वर्कस्पेस पाथ,
फाइल कंटेंट्स, तुमची api_key, तुमचा ईमेल, कोणतीही PII किंवा
वर्कस्पेस-विशिष्ट माहिती. वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) मध्ये ऑडिट करण्यायोग्य आहे.

**ऑप्ट आउट करा** (यापैकी कोणतीही एक कायमची अक्षम करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

नेटवर्क अपयश यामुळे `clawmetry` चालण्यात कधीही अडथळा येत नाही — पिंग
डीमन थ्रेडवर ३ सेकंद टाइमआउटसह फायर-अँड-फर्गेट असते.

## स्टार हिस्ट्री

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## परवाना

MIT

---

<p align="center">
  <strong>🦞 तुमचा एजंट कसा विचार करतो ते पाहा</strong><br>
  <sub>निर्माता <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टीमचा भाग</sub>
</p>
