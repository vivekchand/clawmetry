<!-- i18n-src:8f42d460a973 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट कसा विचार करतो ते पहा.** **14 AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी 10. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एकच कमांड. शून्य कॉन्फिगरेशन. सर्वकाही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि झाले.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 एजंट रनटाइम्ससह कार्य करते

ClawMetry ची सुरुवात OpenClaw साठी ऑब्झर्व्हेबिलिटी म्हणून झाली, आणि आता ते तुमच्या **संपूर्ण एजंट फ्लीट**चे मापन एकाच डॅशबोर्डमध्ये करते, तुमच्या मशीनवरील प्रत्येक रनटाइम आपोआप शोधून:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw आणि NemoClaw ओपन-सोर्स अ‍ॅपमध्ये मोफत आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा सेल्फ-होस्टेड Pro लायसन्ससह सक्रिय होतात. हेडरमधून रनटाइम्स बदला आणि प्रत्येक टॅब — कॉस्ट, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमनुसार पुन्हा-स्कोप होतो. नेमका फ्री/पेड विभाग, टियर मॅट्रिक्स, `/api/entitlement` शेप, आणि `clawmetry license` CLI साठी **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** पहा.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, ब्रेन, टूल्स आणि परत यामधून जाणाऱ्या मेसेजेस दाखवणारा लाइव्ह अ‍ॅनिमेटेड डायग्राम
- **Overview** — हेल्थ चेक्स, अ‍ॅक्टिव्हिटी हीटमॅप, सेशन काउंट्स, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक ब्रेकडाउनसह टोकन आणि कॉस्ट ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची अ‍ॅक्टिव्हिटीसह सक्रिय एजंट सेशन्स
- **Crons** — स्टेटस, पुढील रन, कालावधीसह शेड्युल्ड जॉब्स
- **Logs** — रंग-कोडेड रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनंदिन नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट कॅप्स, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन डिटेक्शन; Slack, Discord, PagerDuty, Telegram, Email कडे रूट करते
- **Approvals** — विनाशकारी डिलीट्स, फोर्स पुश, DB म्युटेशन्स, sudo, पॅकेज इन्स्टॉल्स, नेटवर्क कॉल्स एका क्लिकच्या सही-मंजुरीमागे गेट करा

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

### ✋ Approvals — जोखमीच्या टूल कॉल्सना मॅन्युअल सही-मंजुरीमागे गेट करा; पॉलिसी-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

**स्त्रोतापासून:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 फ्रंटएंड डेव्हलपमेंट

v2 React अ‍ॅप `frontend/` मध्ये आहे आणि Flask सर्व्हर v2 सक्षम करून सुरू केल्यावर
`/v2` वर सर्व्ह केला जातो.

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
`http://localhost:8900` कडे प्रॉक्सी करतो, त्यामुळे React अ‍ॅप कोणत्याही
अतिरिक्त CORS सेटअपशिवाय स्थानिक Flask सर्व्हरशी बोलू शकतो.

Python पॅकेजसोबत शिप होणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रॉडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry फक्त OpenClaw नाही तर अनेक AI-एजंट रनटाइम्सचे निरीक्षण करते. प्रत्येक OpenClaw-नसलेला रनटाइम एक समर्पित रीडर अ‍ॅडॅप्टर शिप करतो जो त्याच्या मूळ सेशन फॉरमॅटचे ClawMetry च्या एकसंध शेप्समध्ये भाषांतर करतो; डिमन ते त्याच DuckDB स्टोअर + क्लाउड स्नॅपशॉटमध्ये इनजेस्ट करतो, रनटाइमनुसार टॅग करून, आणि एकापेक्षा जास्त उपस्थित असल्यास Session replay टॅब एक **रनटाइम स्विचर** दाखवतो. पूर्ण मॅट्रिक्स + रनटाइम्स जोडण्याच्या मार्गदर्शकासाठी [`docs/compatibility.md`](docs/compatibility.md) पहा, आणि OpenClaw-फॅमिली प्राइमरसाठी [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) पहा.

| रनटाइम / एजंट | स्टेटस | नोंदी |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप शोधले जाते |
| **PicoClaw** | बीटा अ‍ॅडॅप्टर | फ्लॅट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अ‍ॅडॅप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स + मेसेज काउंट्स. |
| **Hermes** | बीटा अ‍ॅडॅप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/कॉस्ट. |
| **Claude Code** | बीटा अ‍ॅडॅप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स + थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अ‍ॅडॅप्टर | Rollout JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अ‍ॅडॅप्टर | SQLite `state.vscdb`. चॅट/कंपोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अ‍ॅडॅप्टर | प्रति-प्रोजेक्ट `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन काउंट्स. |
| **Goose** | बीटा अ‍ॅडॅप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन एकूण. |
| **opencode** | बीटा अ‍ॅडॅप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + कॉस्ट. |
| **Qwen Code** | बीटा अ‍ॅडॅप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Pi** | बीटा अ‍ॅडॅप्टर | JSONL `~/.pi/agent/sessions`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + कॉस्ट. |
| **Deep Agents** | बीटा अ‍ॅडॅप्टर | SQLite `~/.deepagents/.state/sessions.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स + कॉस्ट. |

"बीटा अ‍ॅडॅप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या ऑन-डिस्क फॉरमॅटसाठी एक रीडर शिप करते, प्रत्येक खऱ्या मशीनवरील खऱ्या इन्स्टॉलविरुद्ध तयार + पडताळलेला (`tests/fixtures/runtimes/<rt>/` पहा). अ‍ॅडॅप्टर्स फक्त-वाचनीय आहेत; प्रत्येक त्याच्या रनटाइमने प्रत्यक्षात डिस्कवर काय साठवले आहे याबद्दल प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor टोकन कॉस्ट डिस्कवर लिहीत नाहीत). एका नोडवर अनेक रनटाइम्स चालत असताना, रनटाइम स्विचर एका स्वच्छ डीप-डाइव्हसाठी सेशन्स व्ह्यूला एकाच रनटाइमपुरते स्कोप करतो.

## कोणताही SDK एजंट ट्रॅक करा — आउट-लूप कॉस्ट अ‍ॅट्रिब्युशन

वरील सर्व रनटाइम्स सेशन्स डिस्कवर लिहितात. तुमचा स्वतःचा **प्रॉडक्शन एजंट** — जो तुम्ही OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, किंवा एक साधा `httpx` लूप वापरून बनवला आहे — तसे करत नाही. ClawMetry चा शून्य-कॉन्फिग इंटरसेप्टर तरीही `httpx`/`requests` मंकी-पॅच करून त्याचे LLM कॉल्स (कॉस्ट, टोकन्स, लेटन्सी, एरर्स) कॅप्चर करतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` एन्व्ह व्हेरिएबल) प्रत्येक कॉलला एका **नामांकित स्त्रोतासोबत** टॅग करते, त्यामुळे तुम्ही चालवत असलेले प्रत्येक प्रॉडक्ट डॅशबोर्डच्या Overview वरील **🔌 Out-loop sources** कार्डमध्ये स्वतःची पहिल्या-दर्जाची, कॉस्ट-अ‍ॅट्रिब्युटेबल ओळ म्हणून दिसते — प्रत्येक एजंटसाठी कॉल्स, प्रोव्हायडर्स, लेटन्सी, एरर रेट. स्त्रोत सेट केला नाही? कॉल्स तरीही ट्रॅक होतात; कार्ड फक्त लपून राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ही तीच डेटा लेयर आहे जी रनटाइम अ‍ॅडॅप्टर्स फीड करतात (DuckDB → क्लाउड स्नॅपशॉट), त्यामुळे आउट-लूप स्त्रोत बाकी सर्वकाहीसारखेच क्लाउड डॅशबोर्डशी, E2E-एन्क्रिप्टेड सिंक होतात.

## OpenTelemetry — व्हेंडर-न्यूट्रल, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry दोन्ही दिशांनी **OpenTelemetry** बोलतो, **GenAI सिमॅंटिक कन्व्हेन्शन्स** वापरून, त्यामुळे तुमचे एजंट ट्रेसेस कधीही एका टूलमध्ये लॉक-इन होत नाहीत.

प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, कॉस्ट — कोणत्याही कलेक्टरला (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) OTLP/HTTP GenAI स्पॅन्स म्हणून **एक्सपोर्ट** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल पर्यायी एन्व्ह व्हेरिएबल्स आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — बिल्ट-इन OTLP रिसीव्हर इतर कशाहीकडून `/v1/traces` आणि `/v1/metrics` वर ट्रेसेस आणि मेट्रिक्स स्वीकारतो (प्रोटोबफ इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला शून्य-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमचा डेटा तुमची टीम आधीच वापरत असलेल्या कोणत्याही बॅकएंडमध्ये मिळतो — कोणतेही लॉक-इन नाही, इन्स्टॉल करण्यासाठी दुसरा एजंट नाही.

## कॉन्फिगरेशन

बहुतांश लोकांना कोणत्याही कॉन्फिगची गरज नसते. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स आणि क्रॉन्स आपोआप शोधतो.

तुम्हाला कस्टमाइझ करायचे असल्यास:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

ClawMetry तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी लाइव्ह अ‍ॅक्टिव्हिटी दाखवतो. फक्त तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेटअप केलेले चॅनेल्स Flow डायग्राममध्ये दिसतात — कॉन्फिगर न केलेले आपोआप लपवले जातात.

Flow मधील कोणत्याही चॅनेल नोडवर क्लिक करून येणाऱ्या/जाणाऱ्या मेसेज काउंट्ससह लाइव्ह चॅट बबल व्ह्यू पहा.

| चॅनेल | स्टेटस | लाइव्ह पॉपअप | नोंदी |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | मेसेजेस, स्टॅट्स, 10s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचतो |
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
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE सपोर्ट |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सबस्क्रिप्शन |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **ऑटो-डिटेक्शन:** ClawMetry तुमचा `~/.openclaw/openclaw.json` वाचतो आणि तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल्सच रेंडर करतो. कोणतेही मॅन्युअल सेटअप आवश्यक नाही.

## Docker डिप्लॉयमेंट

ClawMetry ला कंटेनरमध्ये चालवायचे आहे? काही हरकत नाही! 🐳

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

> **नोंद:** Docker मध्ये चालवताना, तुमच्या एजंटच्या डेटा + लॉग डिरेक्टरीज (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमचे सेटअप आपोआप शोधू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, किंवा Deep Agents (किंवा Docker साठी माउंट केलेले व्हॉल्यूम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry आपोआप [NemoClaw](https://github.com/NVIDIA/NemoClaw) शोधतो — NVIDIA चा एंटरप्राइझ सिक्युरिटी रॅपर जो OpenClaw साठी असून सँडबॉक्स्ड OpenShell कंटेनर्समध्ये एजंट्स चालवतो.

बहुतांश प्रकरणांमध्ये कोणत्याही अतिरिक्त कॉन्फिगरेशनची गरज नाही. सिंक डिमन सेशन फाइल्स आपोआप शोधतो, मग त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरच्या आत.

### हे कसे कार्य करते

ClawMetry दोन प्रकारे NemoClaw शोधतो:

1. **बायनरी डिटेक्शन** — `nemoclaw` CLI ची तपासणी करते आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवते
2. **कंटेनर डिटेक्शन** — चालू असलेल्या Docker कंटेनर्समध्ये `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी स्कॅन करते, नंतर व्हॉल्यूम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचते

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्स क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केल्या जातात, त्यामुळे तुम्ही त्यांना एका दृष्टिक्षेपात मानक OpenClaw सेशन्सपासून वेगळे ओळखू शकता.

### शिफारसीय सेटअप: सिंक डिमन HOST वर

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डिमन **होस्ट मशीन**वर चालवा (सँडबॉक्सच्या आत नाही). हे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळते.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डिमन आपोआप चालू असलेल्या कोणत्याही OpenShell कंटेनर्समधील सेशन्स शोधेल.

### पर्यायी: स्पष्ट सँडबॉक्स नाव

ऑटो-डिटेक्शन काम करत नसल्यास, ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

सिंक डिमन OpenShell सँडबॉक्सच्या **आत** चालवणे आवश्यक असल्यास, तो ClawMetry इनजेस्ट API पर्यंत पोहोचू शकेल यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा एग्रेस नियम जोडा:

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
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डिमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (लोकल डॅशबोर्ड UI) |
| Docker सॉकेट (`/var/run/docker.sock`) | — | Unix सॉकेट | कंटेनर सेशन डिस्कव्हरीसाठी |

सिंक डिमन फक्त `ingest.clawmetry.com` कडे आउटबाउंड HTTPS कॉल्स करतो. कोणतेही इनबाउंड पोर्ट्स आवश्यक नाहीत.

---

## क्लाउड डिप्लॉयमेंट

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पहा.

## टेस्टिंग

हा प्रोजेक्ट BrowserStack सोबत टेस्ट केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry नवीन मशीनवर पहिल्यांदा `clawmetry` CLI चालवल्यावर
`https://app.clawmetry.com/api/install` कडे एकच अनामिक "फर्स्ट रन" पिंग पाठवतो. आम्ही
याचा वापर इन्स्टॉल्स मोजण्यासाठी (एका OSS प्रोजेक्टसाठी आमच्याकडे असलेले
एकमेव मार्केटिंग मेट्रिक) आणि आमच्या युजर्सनी कोणते एजंट फ्रेमवर्क्स इन्स्टॉल
केले आहेत हे जाणून घेण्यासाठी करतो.

**प्रति इन्स्टॉल फक्त एक POST**, ज्यामध्ये हे असते:

| फील्ड | उदाहरण | का |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला रँडम UUID | डिडुप; तुमच्या ईमेल किंवा api_key शी लिंक केलेले नाही |
| `version` | `0.12.167` | कोणत्या व्हर्जन्स प्रत्यक्षात वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म सपोर्ट प्राधान्यक्रम |
| `python` | `3.11.15` | Python व्हर्जन सपोर्ट मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | पुढे आम्ही कोणत्या एजंट्ससोबत इंटिग्रेट करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्सना CI आवाजापासून वेगळे करते |

**आम्ही काय पाठवत नाही**: IP (क्लाउड सर्व्हर-साइडवर रिक्वेस्टवरून
देश कोड मिळवतो, नंतर IP टाकून देतो), होस्टनेम, युजरनेम, वर्कस्पेस
पाथ, फाइल कंटेंट्स, तुमची api_key, तुमचा ईमेल, कोणतीही PII किंवा
वर्कस्पेस-विशिष्ट माहिती. वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
मध्ये ऑडिट करण्यायोग्य आहे.

**ऑप्ट आउट** (यापैकी कोणतीही एक कायमची अक्षम करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

नेटवर्क अपयश इथे `clawmetry` चालण्यास कधीही अडथळा आणत नाही — पिंग
डिमन थ्रेडवर 3 सेकंद टाइमआउटसह फायर-अँड-फर्गेट आहे.

## स्टार हिस्ट्री

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
  <sub>निर्माता <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> इकोसिस्टमचा भाग</sub>
</p>
