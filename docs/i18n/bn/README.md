<!-- i18n-src:48548997be76 -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টকে চিন্তা করতে দেখুন।** **১২টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজার্ভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ৮টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। কোনো কনফিগ নেই। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে এবং কাজ শেষ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ১২টি এজেন্ট রানটাইমের সাথে কাজ করে

ClawMetry শুরু হয়েছিল OpenClaw-এর অবজার্ভেবিলিটি হিসেবে, এবং এখন একটি ড্যাশবোর্ডে আপনার **পুরো এজেন্ট ফ্লিট** পরিমাপ করে, আপনার মেশিনে প্রতিটি রানটাইম স্বয়ংক্রিয়ভাবে শনাক্ত করে:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw এবং NemoClaw ওপেন-সোর্স অ্যাপে বিনামূল্যে পাওয়া যায়; অন্য রানটাইমগুলো ClawMetry Cloud বা একটি সেলফ-হোস্টেড Pro লাইসেন্সের সাথে সক্রিয় হয়। হেডার থেকে রানটাইম পরিবর্তন করুন এবং প্রতিটি ট্যাব — খরচ, টোকেন, টুল, ট্রেস — সেই রানটাইমে পুনরায় স্কোপ হয়।

## আপনি যা পাবেন

- **Flow** — লাইভ অ্যানিমেটেড ডায়াগ্রাম যা চ্যানেল, ব্রেইন, টুল এবং ফিরে বার্তা প্রবাহিত হতে দেখায়
- **Overview** — হেলথ চেক, অ্যাক্টিভিটি হিটম্যাপ, সেশন সংখ্যা, মডেল তথ্য
- **Usage** — দৈনিক/সাপ্তাহিক/মাসিক বিশ্লেষণসহ টোকেন এবং খরচ ট্র্যাকিং
- **Sessions** — মডেল, টোকেন, সর্বশেষ কার্যকলাপসহ সক্রিয় এজেন্ট সেশন
- **Crons** — স্ট্যাটাস, পরবর্তী রান, সময়কালসহ নির্ধারিত কাজ
- **Logs** — রঙ-কোডযুক্ত রিয়েল-টাইম লগ স্ট্রিমিং
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, দৈনিক নোট ব্রাউজ করুন
- **Transcripts** — সেশন ইতিহাস পড়ার জন্য চ্যাট-বাবল UI
- **Alerts** — বাজেট সীমা, এরর-রেট ট্রিগার, এজেন্ট-অফলাইন শনাক্তকরণ; Slack, Discord, PagerDuty, Telegram, Email-এ রাউট করে
- **Approvals** — ধ্বংসাত্মক ডিলিট, ফোর্স পুশ, DB মিউটেশন, sudo, প্যাকেজ ইনস্টল, নেটওয়ার্ক কল এক-ক্লিক অনুমোদনের পেছনে রাখুন

## স্ক্রিনশট

### 🧠 Brain — লাইভ এজেন্ট ইভেন্ট স্ট্রিম
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — টোকেন ব্যবহার ও সেশন সারসংক্ষেপ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — রিয়েল-টাইম টুল কল ফিড
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — মডেল ও সেশন অনুযায়ী খরচের বিশ্লেষণ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ওয়ার্কস্পেস ফাইল ব্রাউজার
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — পসচার ও অডিট লগ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — বাজেট সীমা, এরর-রেট ট্রিগার, Slack / Discord / PagerDuty / Email-এ ওয়েবহুক
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ঝুঁকিপূর্ণ টুল কল ম্যানুয়াল অনুমোদনের পেছনে রাখুন; পলিসি-সমর্থিত সুরক্ষা নিয়ম
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ইনস্টল করুন

**ওয়ান-লাইনার (প্রস্তাবিত):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**সোর্স থেকে:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ফ্রন্টএন্ড ডেভেলপমেন্ট

v2 React অ্যাপটি `frontend/`-এ থাকে এবং Flask সার্ভার v2 সক্রিয় করে চালু হলে `/v2`-এ পরিবেশিত হয়।

ডেভেলপ করার সময় দুটি টার্মিনাল ব্যবহার করুন:

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

`http://localhost:5173/v2/` খুলুন। Vite `/api` রিকোয়েস্টগুলো `http://localhost:8900`-এ প্রক্সি করে, তাই React অ্যাপটি অতিরিক্ত CORS সেটআপ ছাড়াই লোকাল Flask সার্ভারের সাথে কথা বলতে পারে।

Python প্যাকেজের সাথে শিপ করা বান্ডেল তৈরি করতে:

```bash
cd frontend
npm run build
```

প্রোডাকশন বান্ডেল `clawmetry/static/v2/dist/`-এ লেখা হয়।

## রানটাইম / এজেন্ট সামঞ্জস্যতা

ClawMetry শুধু OpenClaw নয়, অনেক AI এজেন্ট রানটাইম পর্যবেক্ষণ করে। প্রতিটি নন-OpenClaw রানটাইম একটি ডেডিকেটেড রিডার অ্যাডাপ্টার দিয়ে আসে যা তার নেটিভ সেশন ফরম্যাটকে ClawMetry-র একীভূত আকারে রূপান্তরিত করে; ড্যামন সেগুলো একই DuckDB স্টোর ও ক্লাউড স্ন্যাপশটে ইনজেস্ট করে, রানটাইম দিয়ে ট্যাগ করে, এবং Session রিপ্লে ট্যাব একাধিক রানটাইম থাকলে একটি **রানটাইম সুইচার** দেখায়। সম্পূর্ণ ম্যাট্রিক্স ও রানটাইম যোগ করার গাইডের জন্য [`docs/compatibility.md`](docs/compatibility.md) দেখুন, এবং OpenClaw-ফ্যামিলি প্রাইমারের জন্য [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) দেখুন।

| রানটাইম / এজেন্ট | স্ট্যাটাস | মন্তব্য |
|---|---|---|
| **OpenClaw** | নেটিভ | রেফারেন্স রানটাইম, স্বয়ংক্রিয়ভাবে শনাক্ত হয় |
| **PicoClaw** | বেটা অ্যাডাপ্টার | ফ্ল্যাট `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ট্রান্সক্রিপ্ট, মডেল, টুল কল। |
| **NanoClaw** | বেটা অ্যাডাপ্টার | প্রতি-সেশন SQLite (`data/v2-sessions`)। ট্রান্সক্রিপ্ট ও বার্তা সংখ্যা। |
| **Hermes** | বেটা অ্যাডাপ্টার | SQLite `~/.hermes/state.db`। ট্রান্সক্রিপ্ট, মডেল, টোকেন/খরচ। |
| **Claude Code** | বেটা অ্যাডাপ্টার | JSONL `~/.claude/projects/.../<id>.jsonl`। ট্রান্সক্রিপ্ট, মডেল, টুল কল ও থিংকিং, টোকেন ব্যবহার। |
| **Codex** | বেটা অ্যাডাপ্টার | রোলআউট JSONL `~/.codex/sessions/...`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Cursor** | বেটা অ্যাডাপ্টার | SQLite `state.vscdb`। চ্যাট/কম্পোজার ট্রান্সক্রিপ্ট, মডেল। |
| **Aider** | বেটা অ্যাডাপ্টার | প্রতি প্রজেক্টে `.aider.chat.history.md`। ট্রান্সক্রিপ্ট, মডেল, টোকেন সংখ্যা। |
| **Goose** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/goose`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন মোট। |
| **opencode** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/opencode`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ও খরচ। |
| **Qwen Code** | বেটা অ্যাডাপ্টার | JSONL `~/.qwen/projects/.../chats`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |

"বেটা অ্যাডাপ্টার" মানে ClawMetry সেই রানটাইমের আসল অন-ডিস্ক ফরম্যাটের জন্য একটি রিডার সরবরাহ করে, প্রতিটি একটি আসল মেশিনে আসল ইনস্টলের বিপরীতে তৈরি ও যাচাই করা হয়েছে (`tests/fixtures/runtimes/<rt>/` দেখুন)। অ্যাডাপ্টারগুলো রিড-অনলি; প্রতিটি তার রানটাইম আসলে কী সঞ্চয় করে সে সম্পর্কে সৎ (যেমন PicoClaw/NanoClaw/Cursor ডিস্কে টোকেন খরচ লেখে না)। যখন একটি নোডে একাধিক রানটাইম চলে, রানটাইম সুইচার পরিষ্কার গভীর-ডাইভের জন্য সেশন ভিউকে একটিতে স্কোপ করে।

## যেকোনো SDK এজেন্ট ট্র্যাক করুন — আউট-লুপ খরচ অ্যাট্রিবিউশন

উপরের রানটাইমগুলো সবই ডিস্কে সেশন লেখে। আপনার নিজের **প্রোডাকশন এজেন্ট** যেটি আপনি OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, বা একটি সাধারণ `httpx` লুপে তৈরি করেছেন সেটি লেখে না। ClawMetry-র জিরো-কনফিগ ইন্টারসেপ্টর তবুও `httpx`/`requests` মাংকি-প্যাচিং করে এর LLM কল (খরচ, টোকেন, লেটেন্সি, ত্রুটি) ক্যাপচার করে:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (বা `CLAWMETRY_SOURCE=support-agent` এনভ ভার) প্রতিটি কলকে একটি **নামযুক্ত সোর্স** দিয়ে ট্যাগ করে, তাই আপনি যে প্রতিটি পণ্য চালান তা ড্যাশবোর্ডের Overview-এ **🔌 Out-loop sources** কার্ডে নিজস্ব প্রথম-শ্রেণীর, খরচ-অ্যাট্রিবিউটযোগ্য লাইন হিসেবে দেখায় — প্রতি এজেন্টে কল, প্রোভাইডার, লেটেন্সি, এরর রেট। সোর্স সেট না থাকলে? কলগুলো তখনও ট্র্যাক হয়; কার্ডটি শুধু লুকানো থাকে।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

এটি একই ডেটা লেয়ার যা রানটাইম অ্যাডাপ্টারগুলো ফিড করে (DuckDB থেকে ক্লাউড স্ন্যাপশট), তাই আউট-লুপ সোর্সগুলো অন্য সবকিছুর মতো একইভাবে ক্লাউড ড্যাশবোর্ডে সিঙ্ক হয়, E2E-এনক্রিপ্টেড।

## OpenTelemetry — ভেন্ডর-নিরপেক্ষ, আপনার ট্রেস যেকোনো জায়গায় পাঠান

ClawMetry **GenAI সিমান্টিক কনভেনশন** ব্যবহার করে উভয় দিকে **OpenTelemetry** কথা বলে, তাই আপনার এজেন্ট ট্রেস কখনো একটি টুলে আটকে থাকে না।

যেকোনো কালেক্টরে (Datadog, Grafana, Honeycomb, বা আপনার নিজস্ব OTel Collector) OTLP/HTTP GenAI স্প্যান হিসেবে প্রতিটি সেশন এক্সপোর্ট করুন — LLM কল, টুল, সাব-এজেন্ট, টোকেন, খরচ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

অথ হেডার এবং পোল ইন্টারভাল ঐচ্ছিক এনভ ভার:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ইনজেস্ট** — বিল্ট-ইন OTLP রিসিভার `/v1/traces` এবং `/v1/metrics`-এ যেকোনো কিছু থেকে ট্রেস এবং মেট্রিক্স গ্রহণ করে (প্রোটোবাফ ইনজেস্টের জন্য `pip install clawmetry[otel]`)।

আপনি জিরো-কনফিগ, লোকাল-ফার্স্ট ClawMetry ড্যাশবোর্ড **এবং** আপনার দল যে ব্যাকএন্ড ইতিমধ্যে চালায় সেখানে আপনার ডেটা পাবেন — কোনো লক-ইন নেই, ইনস্টল করতে দ্বিতীয় এজেন্ট নেই।

## কনফিগারেশন

বেশিরভাগ মানুষের কোনো কনফিগের প্রয়োজন নেই। ClawMetry আপনার ওয়ার্কস্পেস, লগ, সেশন এবং cron স্বয়ংক্রিয়ভাবে শনাক্ত করে।

কাস্টমাইজ করার প্রয়োজন হলে:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

সমস্ত অপশন: `clawmetry --help`

## সমর্থিত চ্যানেল

ClawMetry আপনার কনফিগার করা প্রতিটি OpenClaw চ্যানেলের জন্য লাইভ কার্যকলাপ দেখায়। শুধুমাত্র আপনার `openclaw.json`-এ আসলে সেটআপ করা চ্যানেলগুলো Flow ডায়াগ্রামে দেখা যায় — কনফিগার না করা চ্যানেলগুলো স্বয়ংক্রিয়ভাবে লুকানো হয়।

লাইভ আসা/যাওয়া বার্তা সংখ্যাসহ একটি লাইভ চ্যাট বাবল ভিউ দেখতে Flow-এর যেকোনো চ্যানেল নোডে ক্লিক করুন।

| চ্যানেল | স্ট্যাটাস | লাইভ পপআপ | মন্তব্য |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ সম্পূর্ণ | ✅ | বার্তা, স্ট্যাটিস্টিক্স, ১০ সেকেন্ড রিফ্রেশ |
| 💬 **iMessage** | ✅ সম্পূর্ণ | ✅ | সরাসরি `~/Library/Messages/chat.db` পড়ে |
| 💚 **WhatsApp** | ✅ সম্পূর্ণ | ✅ | WhatsApp Web (Baileys) এর মাধ্যমে |
| 🔵 **Signal** | ✅ সম্পূর্ণ | ✅ | signal-cli এর মাধ্যমে |
| 🟣 **Discord** | ✅ সম্পূর্ণ | ✅ | Guild ও চ্যানেল শনাক্তকরণ |
| 🟪 **Slack** | ✅ সম্পূর্ণ | ✅ | ওয়ার্কস্পেস ও চ্যানেল শনাক্তকরণ |
| 🌐 **Webchat** | ✅ সম্পূর্ণ | ✅ | বিল্ট-ইন ওয়েব UI সেশন |
| 📡 **IRC** | ✅ সম্পূর্ণ | ✅ | টার্মিনাল-স্টাইল বাবল UI |
| 🍏 **BlueBubbles** | ✅ সম্পূর্ণ | ✅ | BlueBubbles REST API এর মাধ্যমে iMessage |
| 🔵 **Google Chat** | ✅ সম্পূর্ণ | ✅ | Chat API ওয়েবহুকের মাধ্যমে |
| 🟣 **MS Teams** | ✅ সম্পূর্ণ | ✅ | Teams bot প্লাগইনের মাধ্যমে |
| 🔷 **Mattermost** | ✅ সম্পূর্ণ | ✅ | সেলফ-হোস্টেড টিম চ্যাট |
| 🟩 **Matrix** | ✅ সম্পূর্ণ | ✅ | বিকেন্দ্রীভূত, E2EE সমর্থন |
| 🟢 **LINE** | ✅ সম্পূর্ণ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ সম্পূর্ণ | ✅ | বিকেন্দ্রীভূত NIP-04 DMs |
| 🟣 **Twitch** | ✅ সম্পূর্ণ | ✅ | IRC কানেকশনের মাধ্যমে চ্যাট |
| 🔷 **Feishu/Lark** | ✅ সম্পূর্ণ | ✅ | WebSocket ইভেন্ট সাবস্ক্রিপশন |
| 🔵 **Zalo** | ✅ সম্পূর্ণ | ✅ | Zalo Bot API |

> **স্বয়ংক্রিয় শনাক্তকরণ:** ClawMetry আপনার `~/.openclaw/openclaw.json` পড়ে এবং শুধুমাত্র আপনি আসলে কনফিগার করেছেন এমন চ্যানেল রেন্ডার করে। কোনো ম্যানুয়াল সেটআপ প্রয়োজন নেই।

## Docker ডিপ্লয়মেন্ট

ClawMetry একটি কন্টেইনারে চালাতে চান? কোনো সমস্যা নেই! 🐳

**Docker দিয়ে দ্রুত শুরু:**

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

**Docker Compose উদাহরণ:**

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

> **দ্রষ্টব্য:** Docker-এ চালানোর সময়, আপনার এজেন্টের ডেটা ও লগ ডিরেক্টরি (যেমন `~/.openclaw`, `~/.claude`, `~/.codex`) মাউন্ট করুন যাতে ClawMetry আপনার সেটআপ স্বয়ংক্রিয়ভাবে শনাক্ত করতে পারে।

## প্রয়োজনীয়তা

- Python 3.8+
- Flask (pip এর মাধ্যমে স্বয়ংক্রিয়ভাবে ইনস্টল হয়)
- একই মেশিনে একটি AI এজেন্ট রানটাইম: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, বা PicoClaw (বা Docker-এর জন্য মাউন্ট করা ভলিউম)
- Linux বা macOS

## NemoClaw / OpenShell সমর্থন

ClawMetry স্বয়ংক্রিয়ভাবে [NemoClaw](https://github.com/NVIDIA/NemoClaw) শনাক্ত করে — OpenClaw-এর জন্য NVIDIA-র এন্টারপ্রাইজ সিকিউরিটি র‍্যাপার যা স্যান্ডবক্সড OpenShell কন্টেইনারের ভেতরে এজেন্ট চালায়।

বেশিরভাগ ক্ষেত্রে কোনো অতিরিক্ত কনফিগারেশন প্রয়োজন নেই। সিঙ্ক ড্যামন স্বয়ংক্রিয়ভাবে সেশন ফাইল আবিষ্কার করে সেগুলো হোস্টে `~/.openclaw/`-এ থাকুক বা OpenShell কন্টেইনারের ভেতরে থাকুক।

### এটি কীভাবে কাজ করে

ClawMetry দুটি উপায়ে NemoClaw শনাক্ত করে:

1. **বাইনারি শনাক্তকরণ** — `nemoclaw` CLI খোঁজে এবং স্যান্ডবক্স তথ্য পেতে `nemoclaw status` চালায়
2. **কন্টেইনার শনাক্তকরণ** — `openshell`, `nemoclaw`, বা `ghcr.io/nvidia/` ইমেজের জন্য চলমান Docker কন্টেইনার স্ক্যান করে, তারপর ভলিউম মাউন্ট বা `docker cp` এর মাধ্যমে সেশন পড়ে

NemoClaw কন্টেইনার থেকে সিঙ্ক করা সেশন ফাইলগুলো ক্লাউড ড্যাশবোর্ডে `runtime=nemoclaw` এবং `container_id` মেটাডেটা দিয়ে ট্যাগ করা হয়, তাই আপনি এক নজরে সেগুলোকে স্ট্যান্ডার্ড OpenClaw সেশন থেকে আলাদা করতে পারবেন।

### প্রস্তাবিত সেটআপ: HOST-এ সিঙ্ক ড্যামন

সেরা অভিজ্ঞতার জন্য, **হোস্ট মেশিনে** (স্যান্ডবক্সের ভেতরে নয়) ClawMetry-র সিঙ্ক ড্যামন চালান। এটি NemoClaw নেটওয়ার্ক পলিসি বিধিনিষেধ এড়িয়ে চলে।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

সিঙ্ক ড্যামন স্বয়ংক্রিয়ভাবে যেকোনো চলমান OpenShell কন্টেইনারের ভেতরে সেশন খুঁজে পাবে।

### ঐচ্ছিক: স্পষ্ট স্যান্ডবক্স নাম

স্বয়ংক্রিয় শনাক্তকরণ কাজ না করলে, ClawMetry-কে সঠিক স্যান্ডবক্সে নির্দেশ করুন:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### স্যান্ডবক্সের ভেতরে চালানো (অ্যাডভান্সড)

যদি আপনাকে অবশ্যই OpenShell স্যান্ডবক্সের **ভেতরে** সিঙ্ক ড্যামন চালাতে হয়, তাহলে আপনার NemoClaw নেটওয়ার্ক পলিসিতে এই ইগ্রেস নিয়ম যোগ করুন যাতে এটি ClawMetry ইনজেস্ট API-তে পৌঁছাতে পারে:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

প্রয়োগ করুন:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### পোর্ট এবং এন্ডপয়েন্ট

| এন্ডপয়েন্ট | পোর্ট | প্রোটোকল | প্রয়োজনীয় |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | হ্যাঁ (সিঙ্ক ড্যামন থেকে ক্লাউড) |
| `localhost:8900` | 8900 | HTTP | হ্যাঁ (লোকাল ড্যাশবোর্ড UI) |
| Docker সকেট (`/var/run/docker.sock`) | — | Unix সকেট | কন্টেইনার সেশন আবিষ্কারের জন্য |

সিঙ্ক ড্যামন শুধুমাত্র `ingest.clawmetry.com`-এ আউটবাউন্ড HTTPS কল করে। কোনো ইনবাউন্ড পোর্ট প্রয়োজন নেই।

---

## ক্লাউড ডিপ্লয়মেন্ট

SSH টানেল, রিভার্স প্রক্সি এবং Docker-এর জন্য **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** দেখুন।

## পরীক্ষা-নিরীক্ষা

এই প্রজেক্টটি BrowserStack দিয়ে পরীক্ষিত।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## টেলিমেট্রি

ClawMetry প্রথমবার একটি নতুন মেশিনে `clawmetry` CLI চালানোর সময়
`https://app.clawmetry.com/api/install`-এ একটি একক বেনামী "প্রথম রান" পিং পাঠায়। আমরা এটি ইনস্টল গণনা করতে (একটি OSS প্রজেক্টের জন্য আমাদের একমাত্র মার্কেটিং মেট্রিক) এবং আমাদের ব্যবহারকারীরা কোন এজেন্ট ফ্রেমওয়ার্ক ইনস্টল করেছে তা জানতে ব্যবহার করি।

**ইনস্টল প্রতি মাত্র একটি POST**, যাতে রয়েছে:

| ক্ষেত্র | উদাহরণ | কারণ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-এ সংরক্ষিত র‍্যান্ডম UUID | ডিডাপ; আপনার ইমেইল বা api_key-এর সাথে যুক্ত নয় |
| `version` | `0.12.167` | মাঠে কোন সংস্করণ আছে |
| `os` / `os_version` | `Darwin` / `25.3.0` | প্ল্যাটফর্ম সমর্থনের অগ্রাধিকার |
| `python` | `3.11.15` | Python সংস্করণ সমর্থন ম্যাট্রিক্স |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | পরবর্তী কোন এজেন্টের সাথে ইন্টিগ্রেট করা উচিত |
| `is_ci` / `ci_provider` | `true` / `github_actions` | মানব ইনস্টলকে CI নয়েজ থেকে আলাদা করুন |

**আমরা যা পাঠাই না**: IP (ক্লাউড রিকোয়েস্ট থেকে সার্ভার-সাইডে দেশের কোড ডেরাইভ করে, তারপর IP বাতিল করে), হোস্টনেম, ব্যবহারকারীর নাম, ওয়ার্কস্পেস পাথ, ফাইলের বিষয়বস্তু, আপনার api_key, আপনার ইমেইল, কোনো PII বা ওয়ার্কস্পেস-নির্দিষ্ট কিছু। ওয়্যার পেলোড
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-এ অডিটযোগ্য।

**অপ্ট আউট করুন** (এর যেকোনো একটি স্থায়ীভাবে নিষ্ক্রিয় করে):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

এখানে নেটওয়ার্ক ব্যর্থতা কখনো `clawmetry` চালানো আটকায় না — পিং একটি ড্যামন থ্রেডে ৩ সেকেন্ড টাইমআউটসহ ফায়ার-অ্যান্ড-ফরগেট।

## স্টার ইতিহাস

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## লাইসেন্স

MIT

---

<p align="center">
  <strong>🦞 আপনার এজেন্টকে চিন্তা করতে দেখুন</strong><br>
  <sub>নির্মিত <a href="https://github.com/vivekchand">@vivekchand</a> দ্বারা · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ইকোসিস্টেমের অংশ</sub>
</p>
