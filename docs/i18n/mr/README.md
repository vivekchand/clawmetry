<!-- i18n-src:7cfb63716507 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पहा.** **१४ AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी १० हून अधिक. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्वकाही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## १४ एजंट रनटाइम्सबरोबर काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्वेबिलिटी म्हणून झाली, आणि आता ते तुमच्या **संपूर्ण एजंट फ्लीटला** एकाच डॅशबोर्डमध्ये मोजते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप शोधून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw आणि NemoClaw हे ओपन-सोर्स अ‍ॅपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्सने कार्यान्वित होतात. हेडरमधून रनटाइम बदला आणि प्रत्येक टॅब - खर्च, टोकन्स, टूल्स, ट्रेसेस - त्या रनटाइमपुरता मर्यादित होतो. नेमकी मोफत/सशुल्क विभागणी, टियर मॅट्रिक्स, `/api/entitlement` स्वरूप, आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनल्स, ब्रेन, टूल्स आणि परत यामधून वाहणारे संदेश दाखवणारा लाइव्ह अ‍ॅनिमेटेड आकृती
- **Overview** — हेल्थ चेक्स, अ‍ॅक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनंदिन/साप्ताहिक/मासिक विभाजनासह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची अ‍ॅक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्थिती, पुढील रन, कालावधीसह शेड्यूल्ड जॉब्स
- **Logs** — रंग-कोडेड रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनंदिन नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट मर्यादा, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email कडे मार्गस्थ होते
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुश, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉलेशन्स, नेटवर्क कॉल्स एका क्लिकच्या मंजुरीमागे गेट करा

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

### 🔐 Security — स्थिती आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट मर्यादा, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email कडे वेबहूक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — धोकादायक टूल कॉल्स मॅन्युअल मंजुरीमागे गेट करा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी पूर्व-अंमलबजावणी ब्लॉकिंग** — एक कमांड PreToolUse hook
इन्स्टॉल करते जो जुळणाऱ्या टूल कॉल्सना *ते चालण्यापूर्वी* थांबवतो आणि तुमच्या
निर्णयाची वाट पाहतो (फोनवरून एका टॅपने, जेव्हा
[क्लाउड पुश नोटिफिकेशन्स](https://app.clawmetry.com/push) सक्षम असतात):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

एक नकार फक्त त्याच एका टूल कॉलला ब्लॉक करतो — एजंटचे सेशन तसेच राहते आणि तो
दुसरा दृष्टिकोन वापरून पाहू शकतो. तुमच्या फोनवर मंजुरी दिल्याने Claude Code चा
स्वतःचा परवानगी प्रॉम्प्ट वगळला जातो (तुम्ही आधीच उत्तर दिले आहे). न जुळणाऱ्या
टूल्सना सुमारे ४० ms खर्च येतो आणि ते Claude Code च्या सामान्य परवानगी
प्रवाहात पडतात. जेव्हा Claude Code स्वतः तुमची वाट पाहत असतो तेव्हाही तुम्हाला
फोन पुश मिळतो (`permission_prompt` / `idle_prompt` नोटिफिकेशन्स).

## इन्स्टॉल

**वन-लाइनर (शिफारसीय):**
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

v2 React अ‍ॅप `frontend/` मध्ये राहतो आणि जेव्हा v2 सक्षम करून Flask
सर्व्हर सुरू केला जातो तेव्हा `/v2` वर सर्व्ह केला जातो.

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
`http://localhost:8900` कडे प्रॉक्सी करतो, त्यामुळे React अ‍ॅप अतिरिक्त
CORS सेटअपशिवाय स्थानिक Flask सर्व्हरशी बोलू शकतो.

Python पॅकेजबरोबर पाठवला जाणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रॉडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नव्हे तर अनेक AI-एजंट रनटाइम्स निरीक्षतो. प्रत्येक OpenClaw-व्यतिरिक्त रनटाइम एक समर्पित रीडर अ‍ॅडाप्टर पाठवतो जो त्याच्या नेटिव्ह सेशन फॉरमॅटला ClawMetry च्या एकत्रित स्वरूपांमध्ये भाषांतरित करतो; डीमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये, रनटाइमने टॅग करून, ingest करतो, आणि जेव्हा एकापेक्षा जास्त रनटाइम असतात तेव्हा Session replay टॅब **रनटाइम स्विचर** दाखवतो. पूर्ण मॅट्रिक्स + रनटाइम्स जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) पहा, आणि OpenClaw-फॅमिली प्रायमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

[Perplexity चे numbat](https://github.com/perplexityai/numbat) एजंट-सिक्युरिटी टूल वापरत आहात? ClawMetry त्याचे निष्कर्ष आणि अंमलबजावणी निर्णय आपोआप ingest करतो — पहा [`docs/NUMBAT.md`](docs/NUMBAT.md).

| रनटाइम / एजंट | स्थिती | नोंदी |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप शोधले जाते |
| **PicoClaw** | बीटा अ‍ॅडाप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अ‍ॅडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + संदेश गणना. |
| **Hermes** | बीटा अ‍ॅडाप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/खर्च. |
| **Claude Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स + थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अ‍ॅडाप्टर | रोलआउट JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अ‍ॅडाप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अ‍ॅडाप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन गणना. |
| **Goose** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन एकूण. |
| **opencode** | बीटा अ‍ॅडाप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Qwen Code** | बीटा अ‍ॅडाप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा अ‍ॅडाप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **Deep Agents** | बीटा अ‍ॅडाप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + खर्च. |
| **n8n** | बीटा अ‍ॅडाप्टर | SQLite `~/.n8n/database.sqlite`. वर्कफ्लो एक्झिक्युशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, n8n जिथे नोंदवते तिथे मॉडेल + टोकन्स. |
| **Antigravity** | बीटा अ‍ॅडाप्टर | `~/.gemini/<flavor>/brain/` अंतर्गत ब्रेन JSONL. संभाषणे, टूल स्टेप्स, थिंकिंग, प्रति-जनरेशन Gemini टोकन विभाजन + खर्च, बॅकग्राउंड-जनरेशन बर्न. |
| **GitHub Copilot** | बीटा अ‍ॅडाप्टर | Copilot CLI चे `events.jsonl` `~/.copilot/session-state/` अंतर्गत + प्रति-कॉल वापर लेजर असणारा `session-store.db`. संभाषणे, टूल कॉल्स, मॉडेल राऊटिंग, कॅश-जागरूक टोकन विभाजन, विक्रेता-बिल्ड केलेला AI-क्रेडिट खर्च. |
| **Grok** | बीटा अ‍ॅडाप्टर | xAI Grok Build CLI (`~/.grok/bin/grok` अंतर्गत Rust बायनरी): ग्लोबल इव्हेंट लॉग `~/.grok/logs/unified.jsonl` + प्रति-सेशन `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. संभाषणे, प्रति-टर्न टोकन विभाजन, मॉडेल राऊटिंग, आणि CLI चा आउटबाउंड रेपो पेलोड `~/.grok/upload_queue/` अंतर्गत स्टेज केलेला, जेणेकरून तुमच्या मशीनमधून काय बाहेर गेले ते तुम्ही पाहू शकता. |

"बीटा अ‍ॅडाप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या ऑन-डिस्क फॉरमॅटसाठी एक रीडर पाठवते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलेशनविरुद्ध तयार + पडताळणी केलेला (पहा `tests/fixtures/runtimes/<rt>/`). अ‍ॅडाप्टर्स फक्त-वाचनीय आहेत; प्रत्येक त्याच्या रनटाइमने प्रत्यक्षात डिस्कवर काय साठवते याबाबत प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor टोकन खर्च डिस्कवर लिहित नाहीत). जेव्हा एका नोडवर अनेक रनटाइम्स चालतात, तेव्हा रनटाइम स्विचर सेशन्स व्ह्यूला एका स्वच्छ डीप-डाइव्हसाठी एका रनटाइमपुरता मर्यादित करतो.

## कोणत्याही SDK एजंटला ट्रॅक करा — आउट-लूप कॉस्ट अ‍ॅट्रिब्युशन

वरील रनटाइम्स सर्व सेशन्स डिस्कवर लिहितात. तुमचा स्वतःचा **प्रॉडक्शन एजंट** — जो तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा साध्या `httpx` लूपवर तयार केला आहे — तसे करत नाही. ClawMetry चा शून्य-कॉन्फिगरेशन इंटरसेप्टर तरीही `httpx`/`requests` ला मंकी-पॅच करून त्याचे LLM कॉल्स (खर्च, टोकन्स, लेटन्सी, एरर्स) कॅप्चर करतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` एनव्ह व्हेरिएबल) प्रत्येक कॉलला एका **नामांकित सोर्स**ने टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक प्रॉडक्ट डॅशबोर्डच्या Overview वरील **🔌 आउट-लूप सोर्सेस** कार्डमध्ये स्वतःची पहिल्या-दर्जाची, खर्च-अ‍ॅट्रिब्युटेबल ओळ म्हणून दिसते — प्रति एजंट कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. सोर्स सेट केलेला नाही? कॉल्स तरीही ट्रॅक होतात; फक्त कार्ड लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

रनटाइम अ‍ॅडाप्टर्स ज्या डेटा लेयरला फीड करतात तोच हा आहे (DuckDB → क्लाउड स्नॅपशॉट), त्यामुळे आउट-लूप सोर्सेस बाकी सर्वकाहीप्रमाणेच क्लाउड डॅशबोर्डशी सिंक होतात, E2E-एनक्रिप्टेड.

## OpenTelemetry — विक्रेता-निरपेक्ष, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry दोन्ही दिशांना **OpenTelemetry** बोलतो, **GenAI सिमॅंटिक कन्व्हेन्शन्स** वापरून, त्यामुळे तुमचे एजंट ट्रेसेस कधीच एका टूलमध्ये लॉक होत नाहीत.

प्रत्येक सेशन - LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च - कोणत्याही कलेक्टरकडे (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्सपोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल ऐच्छिक एनव्ह व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — अंगभूत OTLP रिसीव्हर `/v1/traces` आणि `/v1/metrics` वर इतर कशाहीकडूनही ट्रेसेस आणि मेट्रिक्स स्वीकारतो (protobuf ingest साठी `pip install clawmetry[otel]`).

तुम्हाला शून्य-कॉन्फिगरेशन, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा डेटा तुमची टीम आधीच चालवत असलेल्या कोणत्याही बॅकएंडमध्ये मिळतो — लॉक-इन नाही, दुसरा एजंट इन्स्टॉल करण्याची गरज नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणत्याही कॉन्फिगरेशनची गरज नसते. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स आणि क्रॉन्स आपोआप शोधते.

जर तुम्हाला कस्टमाइझ करायचे असेल तर:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनल्स

तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनलसाठी ClawMetry लाइव्ह अ‍ॅक्टिव्हिटी दाखवते. फक्त तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेटअप केलेले चॅनल्सच Flow आकृतीत दिसतात - कॉन्फिगर न केलेले आपोआप लपवले जातात.

Flow मधील कोणत्याही चॅनल नोडवर क्लिक करून येणाऱ्या/जाणाऱ्या संदेश गणनेसह लाइव्ह चॅट बबल व्ह्यू पहा.

| चॅनल | स्थिती | लाइव्ह पॉपअप | नोंदी |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आकडेवारी, १० सेकंद रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचते |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) द्वारे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli द्वारे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चॅनल डिटेक्शन |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चॅनल डिटेक्शन |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | अंगभूत वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-शैली बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API द्वारे iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहूक्सद्वारे |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइनद्वारे |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चॅट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE मेसेजिंग API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | वेबसॉकेट इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **आपोआप शोध:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचते आणि फक्त तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनल्सच रेंडर करते. कोणत्याही मॅन्युअल सेटअपची गरज नाही.

## Docker डिप्लॉयमेंट

कंटेनरमध्ये ClawMetry चालवायचे आहे? काहीच अडचण नाही! 🐳

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

> **टीप:** Docker मध्ये चालवताना, तुमच्या एजंटची डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमचे सेटअप आपोआप शोधू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, किंवा QM (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) आपोआप शोधते — NVIDIA चा OpenClaw साठीचा एंटरप्राइझ सिक्युरिटी रॅपर जो एजंट्सना सँडबॉक्स्ड OpenShell कंटेनर्समध्ये चालवतो.

बहुतेक प्रकरणांमध्ये अतिरिक्त कॉन्फिगरेशनची गरज नाही. सिंक डीमन सेशन फाइल्स आपोआप शोधतो, त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरमध्ये.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे शोधते:

1. **बायनरी डिटेक्शन** — `nemoclaw` CLI तपासते आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवते
2. **कंटेनर डिटेक्शन** — `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी चालू असलेले Docker कंटेनर्स स्कॅन करते, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचते

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्स क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केल्या जातात, त्यामुळे तुम्ही त्यांना एका दृष्टीक्षेपात मानक OpenClaw सेशन्सपासून वेगळे ओळखू शकता.

### शिफारसीय सेटअप: होस्टवर सिंक डीमन

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डीमन **होस्ट मशीनवर** चालवा (सँडबॉक्सच्या आत नव्हे). यामुळे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळले जातात.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डीमन कोणत्याही चालू असलेल्या OpenShell कंटेनर्समधील सेशन्स आपोआप शोधेल.

### ऐच्छिक: स्पष्ट सँडबॉक्स नाव

जर आपोआप शोध काम करत नसेल, तर ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

जर तुम्हाला सिंक डीमन OpenShell सँडबॉक्सच्या **आत** चालवायचा असेल, तर ClawMetry ingest API पर्यंत पोहोचता यावे यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा एग्रेस नियम जोडा:

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
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कव्हरीसाठी |

सिंक डीमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. कोणत्याही इनबाउंड पोर्ट्सची गरज नाही.

---

## क्लाउड डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[क्लाउड टेस्टिंग गाइड](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## टेस्टिंग

हा प्रोजेक्ट BrowserStack ने टेस्ट केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry `https://app.clawmetry.com/api/install` कडे अनामिक
इन्स्टॉल-लाइफसायकल पिंग्ज पाठवते: नवीन मशीनवर पहिल्यांदा `clawmetry`
CLI चालवल्यावर एक `install` पिंग, नवीन आवृत्तीत अपग्रेड केल्यानंतरच्या
पहिल्या रनवर एक `update` पिंग, आणि डॅशबोर्डमधील ऑनबोर्डिंग निवड पूर्ण
केल्यावर एक `onboarded` पिंग. आम्ही याचा वापर वास्तविक इन्स्टॉल्सची
गणना करण्यासाठी करतो (कच्च्या PyPI डाउनलोड आकड्यांपैकी सुमारे ९८% मिरर्स,
CI, आणि ऑटो-अपडेट पुन्हा-डाउनलोड्स असतात) आणि कोणते एजंट फ्रेमवर्क्स
आणि आवृत्त्या प्रत्यक्षात वापरात आहेत हे जाणून घेण्यासाठी.

**प्रति लाइफसायकल इव्हेंट प्रति आवृत्ती जास्तीत जास्त एक POST**, यामध्ये:

| फील्ड | उदाहरण | का |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डिड्युप; तुम्ही स्पष्टपणे Cloud sync कनेक्ट करेपर्यंत अनामिक (त्यानंतर ऑथेंटिकेटेड डीमन हार्टबीट ते वाहून नेतो, हे इन्स्टॉल तुमच्या खात्याशी जोडून) |
| `event` | `install` / `update` / `onboarded` | नवीन इन्स्टॉल विरुद्ध विद्यमानाचे अपग्रेड |
| `version` | `0.12.167` | कोणत्या आवृत्त्या वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्ये |
| `python` | `3.11.15` | Python आवृत्ती समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | आम्ही पुढे कोणत्या एजंट्सशी इंटिग्रेट करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्स आणि CI नॉइज वेगळे करण्यासाठी |

**आम्ही काय पाठवत नाही**: IP (क्लाउड विनंतीवरून सर्व्हर-साइडवर देश कोड
काढते, नंतर IP टाकून देते), होस्टनेम, युजरनेम, वर्कस्पेस पाथ, फाइल
कंटेंट्स, तुमची api_key, तुमचा ईमेल, कोणतीही PII किंवा वर्कस्पेस-विशिष्ट
माहिती. वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
मध्ये पडताळण्यायोग्य आहे.

**ऑप्ट आउट** (यापैकी कोणतीही एक ते कायमचे बंद करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

नेटवर्क अपयश यामुळे `clawmetry` चालण्यास कधीही अडथळा येत नाही — पिंग
डीमन थ्रेडवर फायर-अँड-फर्गेट असते, ३ सेकंद टाइमआउटसह.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ने तयार केले · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
