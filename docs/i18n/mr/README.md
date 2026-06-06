<!-- i18n-src:48548997be76 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट विचार करताना पाहा.** **१२ AI एजंट रनटाइम्ससाठी** रिअल-टाइम निरीक्षण: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि इतर ८. तुमच्या संपूर्ण एजंट ताफ्यासाठी एक डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. कोणतीही कॉन्फिगरेशन नाही. सर्व काही आपोआप शोधते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते आणि काम पूर्ण.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## १२ एजंट रनटाइम्ससह काम करते

ClawMetry OpenClaw साठी निरीक्षण म्हणून सुरू झाले, आणि आता एका डॅशबोर्डमध्ये तुमच्या **संपूर्ण एजंट ताफ्याचे** मापन करते, तुमच्या मशीनवर प्रत्येक रनटाइम आपोआप शोधते:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw आणि NemoClaw ओपन-सोर्स ॲपमध्ये विनामूल्य आहेत; इतर रनटाइम्स ClawMetry Cloud किंवा स्वत: होस्ट केलेल्या Pro परवान्यासह सक्रिय होतात. हेडरमधून रनटाइम बदला आणि प्रत्येक टॅब — खर्च, टोकन्स, टूल्स, ट्रेसेस — त्या रनटाइमनुसार बदलतो.

## तुम्हाला काय मिळते

- **Flow** — चॅनेल्स, ब्रेन, टूल्समधून संदेश वाहताना दाखवणारा लाइव्ह अॅनिमेटेड आकृती
- **Overview** — हेल्थ चेक्स, क्रियाकलाप हीटमॅप, सेशन संख्या, मॉडेल माहिती
- **Usage** — दैनिक/साप्ताहिक/मासिक विश्लेषणासह टोकन आणि खर्च ट्रॅकिंग
- **Sessions** — मॉडेल, टोकन्स, शेवटची क्रियाकलापासह सक्रिय एजंट सेशन्स
- **Crons** — स्थिती, पुढील रन, कालावधीसह शेड्यूल केलेल्या जॉब्स
- **Logs** — रंग-कोड केलेले रिअल-टाइम लॉग स्ट्रीमिंग
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, दैनिक नोट्स ब्राउझ करा
- **Transcripts** — सेशन इतिहास वाचण्यासाठी चॅट-बबल UI
- **Alerts** — बजेट मर्यादा, एरर-रेट ट्रिगर्स, एजंट-ऑफलाइन शोध; Slack, Discord, PagerDuty, Telegram, Email वर पाठवते
- **Approvals** — विनाशकारी हटवणे, फोर्स पुश, DB बदल, sudo, पॅकेज इन्स्टॉल, नेटवर्क कॉल एका क्लिकच्या मंजुरीमागे ठेवा

## स्क्रीनशॉट्स

### 🧠 Brain — लाइव्ह एजंट इव्हेंट स्ट्रीम
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — टोकन वापर आणि सेशन सारांश
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — रिअल-टाइम टूल कॉल फीड
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — मॉडेल आणि सेशनद्वारे खर्चाचे विश्लेषण
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — वर्कस्पेस फाइल ब्राउझर
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — पोश्चर आणि ऑडिट लॉग
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — बजेट मर्यादा, एरर-रेट ट्रिगर्स, Slack / Discord / PagerDuty / Email वर वेबहुक्स
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — धोकादायक टूल कॉल्स मॅन्युअल मंजुरीमागे ठेवा; धोरण-समर्थित संरक्षण नियम
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## इन्स्टॉल करा

**एक-लायनर (शिफारस केलेले):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**सोर्सवरून:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 फ्रंटएंड विकास

v2 React ॲप `frontend/` मध्ये आहे आणि Flask सर्व्हर v2 सक्षम करून सुरू केल्यावर `/v2` वर सर्व्ह केली जाते.

विकास करताना दोन टर्मिनल वापरा:

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

`http://localhost:5173/v2/` उघडा. Vite `/api` विनंत्या `http://localhost:8900` वर प्रॉक्सी करतो, त्यामुळे React ॲप अतिरिक्त CORS सेटअपशिवाय स्थानिक Flask सर्व्हरशी बोलू शकतो.

Python पॅकेजसोबत पाठवला जाणारा बंडल तयार करण्यासाठी:

```bash
cd frontend
npm run build
```

प्रोडक्शन बंडल `clawmetry/static/v2/dist/` मध्ये लिहिला जातो.

## रनटाइम / एजंट सुसंगतता

ClawMetry अनेक AI-एजंट रनटाइम्सचे निरीक्षण करते, केवळ OpenClaw नाही. प्रत्येक OpenClaw-नसलेल्या रनटाइमसाठी एक समर्पित रीडर अडॅप्टर येतो जो त्याच्या नेटिव्ह सेशन स्वरूपाचे ClawMetry च्या एकत्रित आकारांमध्ये रूपांतर करतो; डेमन त्यांना रनटाइमसह टॅग करून त्याच DuckDB स्टोर आणि क्लाउड स्नॅपशॉटमध्ये घेतो, आणि Session रिप्ले टॅब एकापेक्षा जास्त रनटाइम असताना **रनटाइम स्विचर** दाखवतो. पूर्ण मॅट्रिक्स आणि रनटाइम जोडण्याचे मार्गदर्शन [`docs/compatibility.md`](docs/compatibility.md) मध्ये, आणि OpenClaw-कुटुंब प्राइमर [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) मध्ये पाहा.

| रनटाइम / एजंट | स्थिती | नोट्स |
|---|---|---|
| **OpenClaw** | नेटिव्ह | संदर्भ रनटाइम, आपोआप शोधले जाते |
| **PicoClaw** | बीटा अडॅप्टर | सपाट `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स. |
| **NanoClaw** | बीटा अडॅप्टर | प्रति-सेशन SQLite (`data/v2-sessions`). ट्रान्सक्रिप्ट्स आणि संदेश संख्या. |
| **Hermes** | बीटा अडॅप्टर | SQLite `~/.hermes/state.db`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन्स/खर्च. |
| **Claude Code** | बीटा अडॅप्टर | JSONL `~/.claude/projects/.../<id>.jsonl`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स आणि थिंकिंग, टोकन वापर. |
| **Codex** | बीटा अडॅप्टर | Rollout JSONL `~/.codex/sessions/...`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |
| **Cursor** | बीटा अडॅप्टर | SQLite `state.vscdb`. चॅट/कम्पोझर ट्रान्सक्रिप्ट्स, मॉडेल. |
| **Aider** | बीटा अडॅप्टर | प्रति प्रकल्प `.aider.chat.history.md`. ट्रान्सक्रिप्ट्स, मॉडेल, टोकन संख्या. |
| **Goose** | बीटा अडॅप्टर | SQLite `~/.local/share/goose`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, एकूण टोकन्स. |
| **opencode** | बीटा अडॅप्टर | SQLite `~/.local/share/opencode`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन्स आणि खर्च. |
| **Qwen Code** | बीटा अडॅप्टर | JSONL `~/.qwen/projects/.../chats`. ट्रान्सक्रिप्ट्स, मॉडेल, टूल कॉल्स, टोकन वापर. |

"बीटा अडॅप्टर" म्हणजे ClawMetry त्या रनटाइमच्या खऱ्या ऑन-डिस्क स्वरूपासाठी रीडर पाठवतो, प्रत्येक खऱ्या मशीनवर खऱ्या इन्स्टॉलविरुद्ध तयार आणि सत्यापित केला जातो (पाहा `tests/fixtures/runtimes/<rt>/`). अडॅप्टर्स केवळ-वाचन आहेत; प्रत्येक त्याच्या रनटाइम प्रत्यक्षात काय साठवतो याबद्दल प्रामाणिक आहे (उदा. PicoClaw/NanoClaw/Cursor डिस्कवर टोकन खर्च लिहित नाहीत). जेव्हा एका नोडवर अनेक रनटाइम चालतात, तेव्हा रनटाइम स्विचर स्वच्छ सखोल-शोधासाठी सेशन्स दृश्य एकावर स्कोप करतो.

## कोणत्याही SDK एजंटचे ट्रॅकिंग करा — आउट-लूप खर्च अट्रिब्युशन

वरील रनटाइम्स सर्व डिस्कवर सेशन्स लिहितात. तुमचा स्वतःचा **प्रोडक्शन एजंट** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B किंवा साध्या `httpx` लूपवर बनवलेला — तसे करत नाही. ClawMetry चा झीरो-कॉन्फिग इंटरसेप्टर तरीही `httpx`/`requests` मंकी-पॅचिंग करून त्याचे LLM कॉल्स (खर्च, टोकन्स, विलंब, एरर्स) कॅप्चर करतो:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (किंवा `CLAWMETRY_SOURCE=support-agent` env var) प्रत्येक कॉलला **नावाच्या स्रोत**सह टॅग करतो, त्यामुळे तुम्ही चालवत असलेले प्रत्येक उत्पादन Overview वरील डॅशबोर्डच्या **🔌 Out-loop sources** कार्डमध्ये स्वतःची प्रथम-श्रेणी, खर्च-अट्रिब्युटेबल ओळ म्हणून दिसते — प्रति एजंट कॉल्स, प्रोव्हायडर्स, विलंब, एरर दर. स्रोत सेट नाही? कॉल्स तरीही ट्रॅक केले जातात; कार्ड फक्त लपलेले राहते.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

हा तोच डेटा लेयर आहे जो रनटाइम अडॅप्टर्स फीड करतात (DuckDB → क्लाउड स्नॅपशॉट), त्यामुळे आउट-लूप स्रोत इतर सर्व गोष्टींप्रमाणेच क्लाउड डॅशबोर्डवर सिंक होतात, E2E-एन्क्रिप्टेड.

## OpenTelemetry — व्हेंडर-तटस्थ, तुमचे ट्रेसेस कुठेही पाठवा

ClawMetry **GenAI सिमँटिक कन्व्हेन्शन्स** वापरून दोन्ही दिशांमध्ये **OpenTelemetry** बोलतो, त्यामुळे तुमचे एजंट ट्रेसेस कधीही एका टूलमध्ये अडकत नाहीत.

प्रत्येक सेशन — LLM कॉल्स, टूल्स, सब-एजंट्स, टोकन्स, खर्च — OTLP/HTTP GenAI spans म्हणून कोणत्याही कलेक्टरला (Datadog, Grafana, Honeycomb, किंवा तुमचा स्वतःचा OTel Collector) **निर्यात** करा:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ऑथ हेडर्स आणि पोल इंटरव्हल पर्यायी env vars आहेत:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**इनजेस्ट** — अंगभूत OTLP रिसीव्हर `/v1/traces` आणि `/v1/metrics` वर इतर कुठल्याहीकडून ट्रेसेस आणि मेट्रिक्स स्वीकारतो (protobuf इनजेस्टसाठी `pip install clawmetry[otel]`).

तुम्हाला झीरो-कॉन्फिग, लोकल-फर्स्ट ClawMetry डॅशबोर्ड **आणि** तुमच्या टीमने आधीपासून चालवत असलेल्या कोणत्याही बॅकएंडमध्ये तुमचा डेटा मिळतो — कोणताही लॉक-इन नाही, इन्स्टॉल करण्यासाठी दुसरा एजंट नाही.

## कॉन्फिगरेशन

बहुतेक लोकांना कोणतीही कॉन्फिगरेशन लागत नाही. ClawMetry तुमचे वर्कस्पेस, लॉग्स, सेशन्स आणि crons आपोआप शोधते.

तुम्हाला सानुकूलित करायचे असल्यास:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

सर्व पर्याय: `clawmetry --help`

## समर्थित चॅनेल्स

ClawMetry तुम्ही कॉन्फिगर केलेल्या प्रत्येक OpenClaw चॅनेलसाठी लाइव्ह क्रियाकलाप दाखवतो. केवळ तुमच्या `openclaw.json` मध्ये प्रत्यक्षात सेट केलेले चॅनेल Flow आकृतीत दिसतात — कॉन्फिगर न केलेले आपोआप लपवले जातात.

लाइव्ह चॅट बबल दृश्य येणाऱ्या/जाणाऱ्या संदेश संख्येसह पाहण्यासाठी Flow मधील कोणताही चॅनेल नोड क्लिक करा.

| चॅनेल | स्थिती | लाइव्ह पॉपअप | नोट्स |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ पूर्ण | ✅ | संदेश, आकडेवारी, १०s रिफ्रेश |
| 💬 **iMessage** | ✅ पूर्ण | ✅ | `~/Library/Messages/chat.db` थेट वाचते |
| 💚 **WhatsApp** | ✅ पूर्ण | ✅ | WhatsApp Web (Baileys) द्वारे |
| 🔵 **Signal** | ✅ पूर्ण | ✅ | signal-cli द्वारे |
| 🟣 **Discord** | ✅ पूर्ण | ✅ | Guild आणि चॅनेल शोध |
| 🟪 **Slack** | ✅ पूर्ण | ✅ | वर्कस्पेस आणि चॅनेल शोध |
| 🌐 **Webchat** | ✅ पूर्ण | ✅ | अंगभूत वेब UI सेशन्स |
| 📡 **IRC** | ✅ पूर्ण | ✅ | टर्मिनल-स्टाइल बबल UI |
| 🍏 **BlueBubbles** | ✅ पूर्ण | ✅ | BlueBubbles REST API द्वारे iMessage |
| 🔵 **Google Chat** | ✅ पूर्ण | ✅ | Chat API वेबहुक्स द्वारे |
| 🟣 **MS Teams** | ✅ पूर्ण | ✅ | Teams बॉट प्लगइन द्वारे |
| 🔷 **Mattermost** | ✅ पूर्ण | ✅ | स्वत: होस्ट केलेले टीम चॅट |
| 🟩 **Matrix** | ✅ पूर्ण | ✅ | विकेंद्रित, E2EE समर्थन |
| 🟢 **LINE** | ✅ पूर्ण | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ पूर्ण | ✅ | विकेंद्रित NIP-04 DMs |
| 🟣 **Twitch** | ✅ पूर्ण | ✅ | IRC कनेक्शनद्वारे चॅट |
| 🔷 **Feishu/Lark** | ✅ पूर्ण | ✅ | WebSocket इव्हेंट सदस्यता |
| 🔵 **Zalo** | ✅ पूर्ण | ✅ | Zalo Bot API |

> **आपोआप शोध:** ClawMetry तुमचे `~/.openclaw/openclaw.json` वाचतो आणि केवळ तुम्ही प्रत्यक्षात कॉन्फिगर केलेले चॅनेल दाखवतो. कोणत्याही मॅन्युअल सेटअपची आवश्यकता नाही.

## Docker तैनाती

ClawMetry कंटेनरमध्ये चालवायचे आहे? कोणतीही अडचण नाही! 🐳

**Docker सह त्वरित सुरुवात:**

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

> **टीप:** Docker मध्ये चालवताना, तुमच्या एजंटचे डेटा आणि लॉग डिरेक्टरी (उदा. `~/.openclaw`, `~/.claude`, `~/.codex`) माउंट करा जेणेकरून ClawMetry तुमची सेटअप आपोआप शोधू शकेल.

## आवश्यकता

- Python 3.8+
- Flask (pip द्वारे आपोआप इन्स्टॉल होते)
- त्याच मशीनवर एक AI एजंट रनटाइम: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, किंवा PicoClaw (किंवा Docker साठी माउंट केलेले व्हॉल्युम्स)
- Linux किंवा macOS

## NemoClaw / OpenShell समर्थन

ClawMetry आपोआप [NemoClaw](https://github.com/NVIDIA/NemoClaw) शोधतो — NVIDIA चा OpenClaw साठी एंटरप्राइझ सिक्युरिटी रॅपर जो एजंट्स सँडबॉक्स्ड OpenShell कंटेनर्समध्ये चालवतो.

बहुतांश प्रकरणांमध्ये कोणत्याही अतिरिक्त कॉन्फिगरेशनची आवश्यकता नाही. सिंक डेमन सेशन फाइल्स आपोआप शोधतो, मग त्या होस्टवरील `~/.openclaw/` मध्ये असोत किंवा OpenShell कंटेनरमध्ये.

### हे कसे काम करते

ClawMetry NemoClaw दोन प्रकारे शोधतो:

1. **बायनरी शोध** — `nemoclaw` CLI साठी तपासतो आणि सँडबॉक्स माहिती मिळवण्यासाठी `nemoclaw status` चालवतो
2. **कंटेनर शोध** — `openshell`, `nemoclaw`, किंवा `ghcr.io/nvidia/` इमेजेससाठी चालणाऱ्या Docker कंटेनर्स स्कॅन करतो, नंतर व्हॉल्युम माउंट्स किंवा `docker cp` द्वारे सेशन्स वाचतो

NemoClaw कंटेनर्समधून सिंक केलेल्या सेशन फाइल्स क्लाउड डॅशबोर्डमध्ये `runtime=nemoclaw` आणि `container_id` मेटाडेटासह टॅग केल्या जातात, त्यामुळे तुम्ही त्या एका दृष्टीक्षेपात मानक OpenClaw सेशन्सपासून वेगळ्या ओळखू शकता.

### शिफारस केलेली सेटअप: HOST वर सिंक डेमन

सर्वोत्तम अनुभवासाठी, ClawMetry चा सिंक डेमन **होस्ट मशीनवर** (सँडबॉक्सच्या आत नाही) चालवा. हे NemoClaw नेटवर्क पॉलिसी निर्बंध टाळते.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

सिंक डेमन आपोआप कोणत्याही चालणाऱ्या OpenShell कंटेनर्समधील सेशन्स शोधेल.

### पर्यायी: स्पष्ट सँडबॉक्स नाव

आपोआप शोध काम न केल्यास, ClawMetry ला योग्य सँडबॉक्सकडे निर्देशित करा:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सँडबॉक्सच्या आत चालवणे (प्रगत)

जर तुम्हाला सिंक डेमन OpenShell सँडबॉक्सच्या **आत** चालवायचा असेल, तर ClawMetry ingest API पर्यंत पोहोचण्यासाठी तुमच्या NemoClaw नेटवर्क पॉलिसीमध्ये हा egress नियम जोडा:

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
| `ingest.clawmetry.com` | 443 | HTTPS | होय (सिंक डेमन → क्लाउड) |
| `localhost:8900` | 8900 | HTTP | होय (स्थानिक डॅशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | कंटेनर सेशन शोधासाठी |

सिंक डेमन केवळ `ingest.clawmetry.com` वर आउटबाउंड HTTPS कॉल्स करतो. कोणत्याही इनबाउंड पोर्ट्सची आवश्यकता नाही.

---

## क्लाउड तैनाती

SSH टनेल्स, रिव्हर्स प्रॉक्सी, आणि Docker साठी **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** पाहा.

## चाचणी

हा प्रकल्प BrowserStack सह चाचणी केला जातो.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलिमेट्री

ClawMetry नवीन मशीनवर `clawmetry` CLI पहिल्यांदा चालवल्यावर `https://app.clawmetry.com/api/install` वर एकच अनामिक "पहिला रन" पिंग पाठवतो. आम्ही हे इन्स्टॉल मोजण्यासाठी (OSS प्रकल्पासाठी आमच्याकडे असलेला एकमात्र मार्केटिंग मेट्रिक) आणि आमचे वापरकर्ते कोणते एजंट फ्रेमवर्क इन्स्टॉल केलेले आहेत हे जाणून घेण्यासाठी वापरतो.

**प्रति इन्स्टॉल फक्त एक POST**, ज्यात आहे:

| फील्ड | उदाहरण | का |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` वर साठवलेला यादृच्छिक UUID | डिडप; तुमच्या ईमेल किंवा api_key शी जोडलेला नाही |
| `version` | `0.12.167` | कोणत्या आवृत्त्या वापरात आहेत |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लॅटफॉर्म समर्थन प्राधान्यक्रम |
| `python` | `3.11.15` | Python आवृत्ती समर्थन मॅट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | कोणत्या एजंट्ससह आम्ही पुढे एकत्रीकरण करावे |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानवी इन्स्टॉल्स CI नॉइजपासून वेगळे करणे |

**आम्ही काय पाठवत नाही**: IP (क्लाउड विनंतीमधून सर्व्हर-साइड देश कोड काढतो, नंतर IP टाकून देतो), होस्टनेम, वापरकर्तानाव, वर्कस्पेस पाथ, फाइल सामग्री, तुमचा api_key, तुमचा ईमेल, कोणतीही PII किंवा वर्कस्पेस-विशिष्ट माहिती. वायर पेलोड [`clawmetry/telemetry.py`](clawmetry/telemetry.py) मध्ये ऑडिट करता येतो.

**ऑप्ट आउट** (यापैकी कोणतेही एक कायमस्वरूपी अक्षम करते):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

येथे नेटवर्क अयशस्वी झाल्यास `clawmetry` चालणे कधीही थांबत नाही — पिंग ३ सेकंदाच्या टाइमआउटसह डेमन थ्रेडवर fire-and-forget आहे.

## स्टार इतिहास

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
  <strong>🦞 तुमचा एजंट विचार करताना पाहा</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> द्वारे बनवलेले · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> परिसंस्थेचा भाग</sub>
</p>
