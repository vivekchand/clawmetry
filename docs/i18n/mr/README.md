<!-- i18n-src:0e34918f8f2e -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट विचार करताना पहा.** **14 AI एजंट रनटाइम्स**साठी रिअल-टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी 10. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप ओळखतो.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि तुमचे काम झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजंट रनटाइम्ससोबत काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्व्हेबिलिटी म्हणून झाली आणि आता ते एका डॅशबोर्डमध्ये तुमचा **संपूर्ण एजंट फ्लीट** मीटर करते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप ओळखून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw आणि NemoClaw ओपन-सोर्स अ‍ॅपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम्स बदला आणि प्रत्येक टॅब — खर्च, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमनुसार पुन्हा-स्कोप होतो. नेमके फ्री/पेड विभाजन, टियर मॅट्रिक्स, `/api/entitlement` शेप आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, brain, टूल्स आणि परत असा संदेशांचा प्रवाह दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, अ‍ॅक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक विभाजनासह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची अ‍ॅक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्टेटस, पुढील रन, कालावधीसह शेड्युल्ड जॉब्स
- **Logs** — रंग-कोडेड रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email कडे रूट होते
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुश, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉल्स, नेटवर्क कॉल्स एका-क्लिक साइन-ऑफच्या मागे गेट करा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल-टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशननुसार खर्च विभाजन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाइल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पवित्रा आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट कॅप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email कडे वेबहूक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखमीचे टूल कॉल्स मॅन्युअल साइन-ऑफच्या मागे गेट करा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी प्री-एक्झिक्युशन ब्लॉकिंग** — एक कमांड एक PreToolUse hook
इन्स्टॉल करते जो जुळणारे टूल कॉल्स *चालण्यापूर्वी* थांबवतो आणि तुमच्या निर्णयाची वाट पाहतो
([cloud push notifications](https://app.clawmetry.com/push) सक्षम केल्यास तुमच्या फोनवरून एका टॅपमध्ये):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक डिनाय फक्त तो एक टूल कॉल ब्लॉक करते — एजंटचे सेशन तसेच राहते आणि तो
दुसरा मार्ग वापरून पाहू शकतो. तुमच्या फोनवर मंजूर केल्याने Claude Code चा स्वतःचा
परवानगी प्रॉम्प्ट वगळला जातो (तुम्ही आधीच उत्तर दिलेले असते). न जुळणाऱ्या टूल्सना
सुमारे ४०ms लागतात आणि ते Claude Code च्या नेहमीच्या परवानगी प्रवाहात जातात.
जेव्हा Claude Code स्वतः तुमची वाट पाहत असतो तेव्हाही तुम्हाला फोन पुश मिळतो
(`permission_prompt` / `idle_prompt` सूचना).

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

v2 React अ‍ॅप `frontend/` मध्ये आहे आणि जेव्हा v2 सक्षम करून Flask सर्व्हर सुरू केला जातो
तेव्हा तो `/v2` वर सर्व्ह केला जातो.

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
`http://localhost:8900` कडे प्रॉक्सी करते, त्यामुळे React अ‍ॅप अतिरिक्त CORS सेटअपशिवाय
स्थानिक Flask सर्व्हरशी बोलू शकतो.

Python पॅकेजसोबत शिप होणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रॉडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry केवळ OpenClaw नव्हे तर अनेक AI-एजंट रनटाइम्स ऑब्झर्व्ह करते. प्रत्येक नॉन-OpenClaw रनटाइम एक समर्पित रीडर अ‍ॅडाप्टर पाठवतो जो त्या रनटाइमच्या नेटिव्ह सेशन फॉरमॅटला ClawMetry च्या युनिफाइड शेप्समध्ये रूपांतरित करतो; डिमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये इनजेस्ट करतो, रनटाइमने टॅग केलेले, आणि जेव्हा एकापेक्षा जास्त रनटाइम असतात तेव्हा Session replay टॅब **रनटाइम स्विचर** दाखवतो. संपूर्ण मॅट्रिक्स + रनटाइम्स जोडण्यासाठी मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) पहा, आणि OpenClaw-family प्राइमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

[Perplexity चे numbat](https://github.com/perplexityai/numbat) एजंट-सिक्युरिटी टूल वापरत आहात? ClawMetry त्याचे निष्कर्ष आणि अंमलबजावणी निर्णय आउट ऑफ द बॉक्स इनजेस्ट करते — [`docs/NUMBAT.md`](docs/NUMBAT.md) पहा.

| रनटाइम / एजंट | स्टेटस | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप ओळखले जाते |
| **PicoClaw** | बीटा अ‍ॅडाप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अ‍ॅडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + संदेश काउंट्स. |
| **Hermes** | बीटा अ‍ॅडाप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/खर्च. |
| **Claude Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स + थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अ‍ॅडाप्टर | रोलआउट JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अ‍ॅडाप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अ‍ॅडाप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन काउंट्स. |
| **Goose** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन एकूण. |
| **opencode** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Qwen Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा अ‍ॅडाप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Deep Agents** | बीटा अ‍ॅडाप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **n8n** | बीटा अ‍ॅडाप्टर | SQLite `~/.n8n/database.sqlite`. वर्कफ्लो एक्झिक्यूशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, n8n जिथे नोंदवते तिथे मॉडेल + टोकन्स. |
| **Antigravity** | बीटा अ‍ॅडाप्टर | `~/.gemini/<flavor>/brain/` अंतर्गत Brain JSONL. संभाषणे, टूल स्टेप्स, थिंकिंग, प्रति-जनरेशन Gemini टोकन विभाजन + खर्च, बॅकग्राउंड-जनरेशन बर्न. |
| **GitHub Copilot** | बीटा अ‍ॅडाप्टर | `~/.copilot/session-state/` अंतर्गत Copilot CLI चे `events.jsonl` + प्रति-कॉल वापर लेजर असलेले `session-store.db`. संभाषणे, टूल कॉल्स, मॉडेल राउटिंग, कॅश-अवेअर टोकन विभाजन, विक्रेता-बिल्ड AI-क्रेडिट खर्च. |

"बीटा अ‍ॅडाप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या ऑन-डिस्क फॉरमॅटसाठी एक रीडर पाठवते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलवर तयार + पडताळलेला (`tests/fixtures/runtimes/<rt>/` पहा). अ‍ॅडाप्टर्स रीड-ओन्ली आहेत; प्रत्येक त्या रनटाइमने प्रत्यक्षात डिस्कवर काय साठवते याबद्दल प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor डिस्कवर टोकन खर्च लिहीत नाहीत). एका नोडवर अनेक रनटाइम्स चालत असताना, रनटाइम स्विचर स्वच्छ डीप-डाइव्हसाठी सेशन्स व्ह्यू एकावर स्कोप करतो.

## कोणताही SDK एजंट ट्रॅक करा — आउट-लूप खर्च विशेषण

वरील रनटाइम्स सर्व सेशन्स डिस्कवर लिहितात. तुमचा स्वतःचा **प्रॉडक्शन एजंट** — जो तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा साधा `httpx` लूप वापरून बनवला आहे — असे करत नाही. ClawMetry चे शून्य-कॉन्फिग इंटरसेप्टर तरीही `httpx`/`requests` ला मंकी-पॅच करून त्याचे LLM कॉल्स (खर्च, टोकन्स, लेटन्सी, एरर्स) कॅप्चर करते:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` env व्हेरिएबल) प्रत्येक कॉलला एका **नामांकित सोर्स**ने टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक प्रॉडक्ट डॅशबोर्डच्या Overview वरील **🔌 Out-loop sources** कार्डमध्ये स्वतःची फर्स्ट-क्लास, खर्च-विशेषणीय ओळ म्हणून दिसते — प्रति एजंट कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. सोर्स सेट केला नाही? कॉल्स तरीही ट्रॅक होतात; कार्ड फक्त लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

हा तोच डेटा लेयर आहे जो रनटाइम अ‍ॅडाप्टर्स फीड करतात (DuckDB → क्लाउड स्नॅपशॉट), त्यामुळे आउट-लूप सोर्सेस बाकी सर्व गोष्टींप्रमाणेच क्लाउड डॅशबोर्डशी, E2E-एन्क्रिप्टेड सिंक होतात.

## OpenTelemetry — विक्रेता-निरपेक्ष, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry दोन्ही दिशांनी **GenAI सिमँटिक कन्व्हेन्शन्स** वापरून **OpenTelemetry** बोलतो, त्यामुळे तुमचे एजंट ट्रेसेस कधीच एका टूलमध्ये लॉक होत नाहीत.

**एक्सपोर्ट** करा प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च — कोणत्याही कलेक्टरला (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल पर्यायी env व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीव्हर `/v1/traces` आणि `/v1/metrics` वर इतर कोणत्याही ठिकाणाहून ट्रेसेस आणि मेट्रिक्स स्वीकारतो (प्रोटोबफ इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला शून्य-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा डेटा तुमची टीम आधीच चालवत असलेल्या कोणत्याही बॅकएंडमध्ये मिळतो — लॉक-इन नाही, दुसरा एजंट इन्स्टॉल करण्याची गरज नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणत्याही कॉन्फिगची गरज नसते. ClawMetry तुमचा वर्कस्पेस, लॉग्स, सेशन्स आणि क्रॉन्स आपोआप ओळखतो.

जर तुम्हाला कस्टमाइझ करायचे असेल तर:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

ClawMetry तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी लाइव्ह अ‍ॅक्टिव्हिटी दाखवते. तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेटअप केलेले चॅनेल्सच Flow डायग्राममध्ये दिसतात — कॉन्फिगर न केलेले आपोआप लपवले जातात.

Flow मधील कोणत्याही चॅनेल नोडवर क्लिक करा म्हणजे इनकमिंग/आउटगोइंग संदेश काउंट्ससह लाइव्ह चॅट बबल व्ह्यू दिसेल.

| चॅनेल | स्टेटस | लाइव्ह पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आकडेवारी, 10s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचतो |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) द्वारे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli द्वारे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चॅनेल ओळख |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चॅनेल ओळख |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | बिल्ट-इन वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-शैली बबल UI |
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

> **टीप:** Docker मध्ये चालवताना, तुमच्या एजंटची डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमचा सेटअप आपोआप ओळखू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, किंवा GitHub Copilot (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) आपोआप ओळखते — NVIDIA चे एंटरप्राइझ सिक्युरिटी रॅपर जे OpenClaw एजंट्सना सँडबॉक्स्ड OpenShell कंटेनर्समध्ये चालवते.

बहुतेक प्रकरणांमध्ये अतिरिक्त कॉन्फिगरेशनची गरज नाही. सिंक डिमन सेशन फाइल्स आपोआप शोधतो, त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरच्या आत.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे ओळखते:

1. **बायनरी डिटेक्शन** — `nemoclaw` CLI तपासते आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवते
2. **कंटेनर डिटेक्शन** — `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी चालू असलेले Docker कंटेनर्स स्कॅन करते, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचते

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्स क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केल्या जातात, त्यामुळे तुम्ही त्यांना एका दृष्टीक्षेपात स्टँडर्ड OpenClaw सेशन्सपासून वेगळे ओळखू शकता.

### शिफारस केलेला सेटअप: होस्टवर सिंक डिमन

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डिमन **होस्ट मशीन**वर चालवा (सँडबॉक्सच्या आत नाही). यामुळे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळले जातात.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डिमन कोणत्याही चालू असलेल्या OpenShell कंटेनर्समधील सेशन्स आपोआप शोधेल.

### पर्यायी: स्पष्ट सँडबॉक्स नाव

जर ऑटो-डिटेक्शन काम करत नसेल, तर ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

जर तुम्हाला सिंक डिमन OpenShell सँडबॉक्सच्या **आत** चालवावाच लागला, तर तो ClawMetry ingest API पर्यंत पोहोचू शकेल यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा एग्रेस नियम जोडा:

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
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कवरीसाठी |

सिंक डिमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. इनबाउंड पोर्ट्सची गरज नाही.

---

## Cloud डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## टेस्टिंग

हा प्रोजेक्ट BrowserStack सह टेस्ट केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry `https://app.clawmetry.com/api/install` वर अनामिक इन्स्टॉल-लाइफसायकल
पिंग्स पाठवते: नवीन मशीनवर पहिल्यांदा `clawmetry` CLI चालवताना एक `install`
पिंग, नवीन व्हर्जनमध्ये अपग्रेड केल्यानंतरच्या पहिल्या रनसाठी एक `update` पिंग,
आणि तुम्ही इन-डॅशबोर्ड ऑनबोर्डिंग निवड पूर्ण केल्यावर एक `onboarded` पिंग.
आम्ही याचा वापर खऱ्या इन्स्टॉल्सची संख्या मोजण्यासाठी करतो (कच्चे PyPI डाउनलोड
आकडे सुमारे ९८% मिरर्स, CI आणि ऑटो-अपडेट री-डाउनलोड्स असतात) आणि प्रत्यक्षात
वापरात असलेले एजंट फ्रेमवर्क्स आणि व्हर्जन्स कोणते आहेत हे जाणून घेण्यासाठी.

**प्रति व्हर्जन प्रति लाइफसायकल इव्हेंट जास्तीत जास्त एक POST**, ज्यात हे असते:

| फील्ड | उदाहरण | का |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेले रँडम UUID | डिडुप; तुम्ही स्पष्टपणे Cloud sync कनेक्ट करेपर्यंत अनामिक (त्यानंतर ऑथेंटिकेटेड डिमन हार्टबीट ते वाहून नेतो, या इन्स्टॉलला तुमच्या खात्याशी लिंक करतो) |
| `event` | `install` / `update` / `onboarded` | नवीन इन्स्टॉल विरुद्ध अस्तित्वात असलेल्याचे अपग्रेड |
| `version` | `0.12.167` | कोणती व्हर्जन्स प्रत्यक्षात वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्ये |
| `python` | `3.11.15` | Python व्हर्जन समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | पुढे आम्ही कोणत्या एजंट्ससोबत इंटिग्रेट करायला हवे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्सना CI नॉईझपासून वेगळे करणे |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर विनंतीवरून देश कोड
काढतो, नंतर IP टाकून देतो), होस्टनेम, युजरनेम, वर्कस्पेस पाथ, फाइल कंटेंट,
तुमची api_key, तुमचा ईमेल, कोणतीही PII किंवा वर्कस्पेस-विशिष्ट माहिती. वायर पेलोड
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) मध्ये ऑडिट करण्यायोग्य आहे.

**ऑप्ट आउट** (यापैकी कोणतेही एक हे कायमचे अक्षम करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

नेटवर्क अपयश यामुळे `clawmetry` चालण्यापासून कधीही अडत नाही — पिंग हा
डिमन थ्रेडवर ३ सेकंद टाइमआउटसह फायर-अँड-फर्गेट असतो.

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
  <strong>🦞 तुमचा एजंट विचार करताना पहा</strong><br>
  <sub>निर्मिती <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
