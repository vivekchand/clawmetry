<!-- i18n-src:8252f6b1d31d -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पहा.** **१४ AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी १० रनटाइम्स. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही आपोआप ओळखते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि तुमचे काम झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## १४ एजंट रनटाइम्ससोबत काम करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्वेबिलिटी म्हणून झाली, आणि आता ते तुमच्या **संपूर्ण एजंट फ्लीटचे** मोजमाप एकाच डॅशबोर्डमध्ये करते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप ओळखून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw आणि NemoClaw ओपन-सोर्स अ‍ॅपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम बदला आणि प्रत्येक टॅब — खर्च, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमनुसार पुन्हा-स्कोप होतो. नेमका मोफत/पेड फरक, टियर मॅट्रिक्स, `/api/entitlement` शेप, आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, ब्रेन, टूल्स, आणि परत यामधून वाहणारे मेसेजेस दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, अ‍ॅक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउनसह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची अ‍ॅक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्टेटस, पुढील रन, कालावधीसह शेड्यूल्ड जॉब्स
- **Logs** — कलर-कोडेड रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email कडे रूट होते
- **Approvals** — विध्वंसक डिलीट्स, फोर्स पुशेस, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉल्स, नेटवर्क कॉल्स एका क्लिकवरील सही-मंजुरीमागे गेट करा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल-टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशननुसार खर्च ब्रेकडाउन
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाईल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोश्चर आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट कॅप्स, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email कडे वेबहुक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — जोखमीचे टूल कॉल्स मॅन्युअल सही-मंजुरीमागे गेट करा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code साठी पूर्व-अंमलबजावणी ब्लॉकिंग** — एक कमांड जुळणारे टूल कॉल्स
*चालण्याआधीच* थांबवणारा आणि तुमच्या निर्णयाची वाट पाहणारा PreToolUse हुक इन्स्टॉल करते
([क्लाउड पुश नोटिफिकेशन्स](https://app.clawmetry.com/push) सक्षम असल्यास
तुमच्या फोनवरून एका टॅपने):

```bash
clawmetry hooks install     # ~/.claude/settings.json लिहिते (idempotent)
clawmetry hooks status      # काय जोडलेले आहे + किती पॉलिसी सक्रिय आहेत
clawmetry hooks uninstall   # फक्त ClawMetry च्या नोंदी काढून टाकते
```

एक नकार फक्त त्या एका टूल कॉलला ब्लॉक करतो — एजंट आपले सेशन कायम ठेवतो आणि
दुसरा मार्ग वापरून पाहू शकतो. तुमच्या फोनवर मंजुरी दिल्याने Claude Code चा स्वतःचा
परवानगी प्रॉम्प्ट वगळला जातो (तुम्ही आधीच उत्तर दिलेले असते). न जुळणाऱ्या टूल्ससाठी
~४०ms खर्च येतो आणि ते Claude Code च्या नेहमीच्या परवानगी फ्लोकडे जातात.
Claude Code स्वतः तुमची वाट पाहत असतानाही तुम्हाला फोन पुश मिळतो
(`permission_prompt` / `idle_prompt` नोटिफिकेशन्स).

## इन्स्टॉल

**वन-लायनर (शिफारस केलेले):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**स्त्रोतापासून:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 फ्रंटएंड डेव्हलपमेंट

v2 React अ‍ॅप `frontend/` मध्ये आहे आणि v2 सक्षम करून Flask सर्व्हर सुरू केल्यावर
`/v2` वर सर्व्ह होतो.

डेव्हलप करताना दोन टर्मिनल वापरा:

```bash
# टर्मिनल १: :8900 वर Flask API/सर्व्हर
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# टर्मिनल २: :5173 वर Vite डेव्ह सर्व्हर
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

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नाही तर अनेक AI-एजंट रनटाइम्स ऑब्झर्व्ह करते. प्रत्येक OpenClaw-नसलेला रनटाइम एक समर्पित रीडर अ‍ॅडाप्टर शिप करतो जो त्या रनटाइमच्या मूळ सेशन फॉरमॅटचे ClawMetry च्या एकसंध शेप्समध्ये भाषांतर करतो; डीमन त्यांना त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये रनटाइम टॅगसह इनजेस्ट करतो, आणि एकापेक्षा जास्त रनटाइम्स उपस्थित असताना सेशन रीप्ले टॅब एक **रनटाइम स्विचर** दाखवतो. पूर्ण मॅट्रिक्स + रनटाइम्स जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) पहा, आणि OpenClaw-फॅमिली प्रायमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

| रनटाइम / एजंट | स्थिती | टिपा |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप ओळखले जाते |
| **PicoClaw** | बीटा अ‍ॅडाप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अ‍ॅडाप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + मेसेज काउंट्स. |
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
| **n8n** | बीटा अ‍ॅडाप्टर | SQLite `~/.n8n/database.sqlite`. वर्कफ्लो एक्झिक्युशन्स, नोड रन्स, AI Agent प्रॉम्प्ट्स, n8n नोंदवत असल्यास मॉडेल + टोकन्स. |

"बीटा अ‍ॅडाप्टर" म्हणजे ClawMetry त्या रनटाइमच्या वास्तविक ऑन-डिस्क फॉरमॅटसाठी रीडर शिप करते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलविरुद्ध तयार + पडताळलेला (पहा `tests/fixtures/runtimes/<rt>/`). अ‍ॅडाप्टर्स रीड-ओन्ली आहेत; प्रत्येक त्याचा रनटाइम प्रत्यक्षात डिस्कवर काय साठवतो याबाबत प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor डिस्कवर टोकन खर्च लिहीत नाहीत). एका नोडवर अनेक रनटाइम्स चालत असताना, रनटाइम स्विचर सेशन्स व्ह्यूला एकावर स्कोप करतो स्वच्छ डीप-डाइव्हसाठी.

## कोणताही SDK एजंट ट्रॅक करा — आउट-लूप खर्च गुणविशेषण

वरील सर्व रनटाइम्स सेशन्स डिस्कवर लिहितात. तुम्ही स्वतः तयार केलेला **प्रोडक्शन एजंट** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा साधा `httpx` लूपवर बांधलेला — तसे करत नाही. ClawMetry चा शून्य-कॉन्फिग इंटरसेप्टर तरीही `httpx`/`requests` मंकी-पॅच करून त्याचे LLM कॉल्स (खर्च, टोकन्स, लेटन्सी, एरर्स) कॅप्चर करतो:

```python
import clawmetry.track            # इंटरसेप्टर सक्रिय करा
clawmetry.track.set_source("support-agent")   # या उत्पादनाचे नाव द्या

# ...तुमचा एजंट नेहमीप्रमाणे चालतो; प्रत्येक LLM कॉल आता ट्रॅक + गुणविशेषित होतो.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` env व्हेरिएबल) प्रत्येक कॉलला एका **नामांकित स्त्रोताने** टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक उत्पादन डॅशबोर्डच्या Overview वरील **🔌 आउट-लूप स्त्रोत** कार्डमध्ये स्वतःची फर्स्ट-क्लास, खर्च-गुणविशेषनीय ओळ म्हणून दिसते — प्रति एजंट कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. स्त्रोत सेट केला नाही? कॉल्स तरीही ट्रॅक होतात; कार्ड फक्त लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

हा तोच डेटा लेयर आहे जो रनटाइम अ‍ॅडाप्टर्स फीड करतात (DuckDB → क्लाउड स्नॅपशॉट), त्यामुळे आउट-लूप स्त्रोत बाकी सर्वकाही प्रमाणेच क्लाउड डॅशबोर्डशी सिंक होतात, एंड-टू-एंड एन्क्रिप्टेड.

## OpenTelemetry — वेंडर-न्यूट्रल, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry दोन्ही दिशांना **OpenTelemetry** बोलतो, **GenAI सिमॅंटिक कन्व्हेन्शन्स** वापरून, त्यामुळे तुमचे एजंट ट्रेसेस कधीच एका टूलमध्ये लॉक-इन होत नाहीत.

प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च — कोणत्याही कलेक्टरकडे (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्सपोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# समतुल्य:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल हे पर्यायी env व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # अतिरिक्त HTTP हेडर्स
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # सेकंद (डीफॉल्ट ६०)
```

**इनजेस्ट** — अंगभूत OTLP रिसीव्हर `/v1/traces` आणि `/v1/metrics` वर इतर कोणत्याही स्त्रोताकडून ट्रेसेस आणि मेट्रिक्स स्वीकारतो (protobuf इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला शून्य-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा डेटा तुमची टीम आधीच वापरत असलेल्या कोणत्याही बॅकएंडमध्ये मिळतो — कोणतेही लॉक-इन नाही, दुसरा एजंट इन्स्टॉल करण्याची गरज नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणत्याही कॉन्फिगची गरज नसते. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स, आणि क्रॉन्स आपोआप ओळखते.

जर तुम्हाला कस्टमाइझ करायचे असेल:

```bash
clawmetry --port 9000              # कस्टम पोर्ट (डीफॉल्ट: 8900)
clawmetry --host 127.0.0.1         # फक्त लोकलहोस्टशी बाइंड करा
clawmetry --workspace ~/mybot      # कस्टम वर्कस्पेस पथ
clawmetry --name "Alice"           # Flow व्हिज्युअलायझेशनमध्ये तुमचे नाव
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी ClawMetry लाइव्ह अ‍ॅक्टिव्हिटी दाखवते. फक्त तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेटअप केलेले चॅनेल्सच Flow डायग्राममध्ये दिसतात — सेटअप न केलेले आपोआप लपवले जातात.

Flow मध्ये कोणत्याही चॅनेल नोडवर क्लिक करून इनकमिंग/आउटगोइंग मेसेज काउंट्ससह लाइव्ह चॅट बबल व्ह्यू पहा.

| चॅनेल | स्थिती | लाइव्ह पॉपअप | टिपा |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मेसेजेस, आकडेवारी, १०s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | थेट `~/Library/Messages/chat.db` वाचते |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) द्वारे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli द्वारे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | गिल्ड + चॅनेल ओळख |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस + चॅनेल ओळख |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | अंगभूत वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-शैलीचे बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API द्वारे iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक्सद्वारे |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइनद्वारे |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | सेल्फ-होस्टेड टीम चॅट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE मेसेजिंग API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **आपोआप ओळख:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचतो आणि फक्त तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल्सच रेंडर करतो. मॅन्युअल सेटअपची गरज नाही.

## Docker डिप्लॉयमेंट

कंटेनरमध्ये ClawMetry चालवायचे आहे? काही अडचण नाही! 🐳

**Docker सह क्विक स्टार्ट:**

```bash
# इमेज बिल्ड करा
docker build -t clawmetry .

# डीफॉल्ट सेटिंग्जसह चालवा
docker run -p 8900:8900 clawmetry

# किंवा तुमच्या एजंटची डेटा डिरेक्टरी माउंट करा (दाखवलेली: OpenClaw ची ~/.openclaw)
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

> **टीप:** Docker मध्ये चालवताना, तुमच्या एजंटच्या डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमचे सेटअप आपोआप ओळखू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, किंवा n8n (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) आपोआप ओळखते — NVIDIA चे एंटरप्राइज सुरक्षा रॅपर जे OpenClaw एजंट्सना सँडबॉक्स्ड OpenShell कंटेनर्समध्ये चालवते.

बहुतेक प्रकरणांमध्ये अतिरिक्त कॉन्फिगरेशनची गरज नाही. सिंक डीमन सेशन फाइल्स आपोआप शोधतो, त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरच्या आत.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे ओळखते:

1. **बायनरी ओळख** — `nemoclaw` CLI तपासते आणि सँडबॉक्स माहितीसाठी `nemoclaw status` चालवते
2. **कंटेनर ओळख** — `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी चालू असलेले Docker कंटेनर्स स्कॅन करते, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचते

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्सना क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केले जाते, त्यामुळे तुम्ही त्यांना एका नजरेत मानक OpenClaw सेशन्सपासून वेगळे ओळखू शकता.

### शिफारस केलेला सेटअप: HOST वर सिंक डीमन

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डीमन **होस्ट मशीनवर** चालवा (सँडबॉक्सच्या आत नाही). यामुळे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळले जातात.

```bash
# होस्टवर (सँडबॉक्सच्या बाहेर)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डीमन कोणत्याही चालू असलेल्या OpenShell कंटेनरमधील सेशन्स आपोआप शोधेल.

### पर्यायी: स्पष्ट सँडबॉक्स नाव

जर आपोआप ओळख काम करत नसेल, तर ClawMetryला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

जर तुम्हाला सिंक डीमन **सँडबॉक्सच्या आत** चालवायचा असेल, तर ते ClawMetry इनजेस्ट API पर्यंत पोहोचू शकेल यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा एग्रेस नियम जोडा:

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
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डीमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (लोकल डॅशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन शोधासाठी |

सिंक डीमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. कोणतेही इनबाउंड पोर्ट्स आवश्यक नाहीत.

---

## क्लाउड डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## टेस्टिंग

हा प्रोजेक्ट BrowserStack सह टेस्ट केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry `https://app.clawmetry.com/api/install` कडे निनावी
इन्स्टॉल-लाइफसायकल पिंग्ज पाठवते: नवीन मशीनवर तुम्ही पहिल्यांदा `clawmetry`
CLI चालवता तेव्हा एक `install` पिंग, नवीन आवृत्तीवर अपग्रेड केल्यानंतरच्या
पहिल्या रनवर एक `update` पिंग, आणि तुम्ही डॅशबोर्डमधील ऑनबोर्डिंग निवड
पूर्ण करता तेव्हा एक `onboarded` पिंग. आम्ही याचा वापर वास्तविक इन्स्टॉल्सची
गणना करण्यासाठी करतो (कच्चे PyPI डाउनलोड आकडे ~९८% मिरर्स, CI, आणि
ऑटो-अपडेट पुन्हा-डाउनलोड्स असतात) आणि प्रत्यक्षात वापरात असलेले एजंट
फ्रेमवर्क्स आणि आवृत्त्या जाणून घेण्यासाठी.

**प्रत्येक आवृत्तीसाठी प्रति लाइफसायकल इव्हेंट जास्तीत जास्त एक POST**, ज्यामध्ये हे असते:

| फील्ड | उदाहरण | का |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डुप्लिकेशन टाळण्यासाठी; तुम्ही स्पष्टपणे Cloud सिंक कनेक्ट करेपर्यंत निनावी (त्यानंतर ऑथेंटिकेटेड डीमन हार्टबीट यात तो वाहून नेतो, हे इन्स्टॉल तुमच्या खात्याशी जोडून) |
| `event` | `install` / `update` / `onboarded` | नवीन इन्स्टॉल विरुद्ध विद्यमानाचे अपग्रेड |
| `version` | `0.12.167` | प्रत्यक्षात वापरात कोणत्या आवृत्त्या आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्यक्रम |
| `python` | `3.11.15` | Python आवृत्ती समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | आम्ही पुढे कोणत्या एजंट्ससोबत एकत्रीकरण करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्सना CI आवाजापासून वेगळे करणे |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर विनंतीवरून
देश कोड काढतो, नंतर IP टाकून देतो), होस्टनेम, युजरनेम, वर्कस्पेस पथ,
फाईल कंटेंट्स, तुमची api_key, तुमचा ईमेल, कोणतीही PII किंवा
वर्कस्पेस-विशिष्ट माहिती. वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
मध्ये ऑडिट करण्यायोग्य आहे.

**ऑप्ट आउट करा** (यापैकी कोणतेही एक हे कायमचे अक्षम करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # प्रति-शेल
export DO_NOT_TRACK=1                          # W3C क्रॉस-टूल मानक
touch ~/.clawmetry/notelemetry                 # कायमस्वरूपी फाईल मार्कर
```

नेटवर्क अपयश यामुळे `clawmetry` चालण्यात कधीच अडथळा येत नाही — पिंग
डीमन थ्रेडवर ३ सेकंद टाइमआउटसह फायर-अँड-फॉरगेट पद्धतीने पाठवला जातो.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> यांनी तयार केले · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
