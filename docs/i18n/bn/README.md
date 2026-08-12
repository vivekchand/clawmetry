<!-- i18n-src:7cfb63716507 -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টকে চিন্তা করতে দেখুন।** **১৪টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম পর্যবেক্ষণ ব্যবস্থা: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ১০টি। আপনার পুরো এজেন্ট বহরের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। শূন্য কনফিগারেশন। সবকিছু স্বয়ংক্রিয়ভাবে সনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে এবং আপনার কাজ শেষ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ১৪টি এজেন্ট রানটাইমের সাথে কাজ করে

ClawMetry শুরু হয়েছিল OpenClaw-এর জন্য পর্যবেক্ষণ ব্যবস্থা হিসেবে, এবং এখন এটি আপনার **পুরো এজেন্ট বহরের** পরিমাপ করে একটিমাত্র ড্যাশবোর্ডে, আপনার মেশিনে প্রতিটি রানটাইম স্বয়ংক্রিয়ভাবে সনাক্ত করে:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw এবং NemoClaw ওপেন-সোর্স অ্যাপে বিনামূল্যে; বাকি রানটাইমগুলো ClawMetry Cloud বা সেলফ-হোস্টেড Pro লাইসেন্সের মাধ্যমে সক্রিয় হয়। হেডার থেকে রানটাইম পরিবর্তন করুন এবং প্রতিটি ট্যাব — খরচ, টোকেন, টুলস, ট্রেস — সেই রানটাইমের জন্য নতুন করে সাজানো হয়। সঠিক বিনামূল্যে/পেইড বিভাজন, টিয়ার ম্যাট্রিক্স, `/api/entitlement` শেপ এবং `clawmetry license` CLI-এর জন্য দেখুন **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**।

## আপনি যা পাবেন

- **Flow** — চ্যানেল, ব্রেইন, টুলস এবং ফিরতি পথ দিয়ে বার্তা প্রবাহ দেখানো লাইভ অ্যানিমেটেড ডায়াগ্রাম
- **Overview** — স্বাস্থ্য পরীক্ষা, অ্যাক্টিভিটি হিটম্যাপ, সেশন সংখ্যা, মডেল তথ্য
- **Usage** — দৈনিক/সাপ্তাহিক/মাসিক ভাঙন সহ টোকেন এবং খরচ ট্র্যাকিং
- **Sessions** — মডেল, টোকেন, সর্বশেষ কার্যকলাপ সহ সক্রিয় এজেন্ট সেশন
- **Crons** — স্ট্যাটাস, পরবর্তী রান, সময়কাল সহ শিডিউল করা জব
- **Logs** — রঙ-কোডেড রিয়েল-টাইম লগ স্ট্রিমিং
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, দৈনিক নোট ব্রাউজ করুন
- **Transcripts** — সেশন ইতিহাস পড়ার জন্য চ্যাট-বাবল UI
- **Alerts** — বাজেট সীমা, ত্রুটি-হার ট্রিগার, এজেন্ট-অফলাইন শনাক্তকরণ; Slack, Discord, PagerDuty, Telegram, Email-এ রুট করে
- **Approvals** — ধ্বংসাত্মক ডিলিট, ফোর্স পুশ, DB মিউটেশন, sudo, প্যাকেজ ইনস্টল, নেটওয়ার্ক কল এক-ক্লিকে সাইন-অফের পেছনে আটকে রাখুন

## স্ক্রিনশট

### 🧠 Brain — লাইভ এজেন্ট ইভেন্ট স্ট্রিম
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — টোকেন ব্যবহার ও সেশন সারাংশ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — রিয়েল-টাইম টুল কল ফিড
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — মডেল ও সেশন অনুযায়ী খরচের ভাঙন
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ওয়ার্কস্পেস ফাইল ব্রাউজার
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — অবস্থান ও অডিট লগ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — বাজেট সীমা, ত্রুটি-হার ট্রিগার, Slack / Discord / PagerDuty / Email-এ ওয়েবহুক
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ম্যানুয়াল সাইন-অফের পেছনে ঝুঁকিপূর্ণ টুল কল আটকে রাখুন; নীতি-সমর্থিত সুরক্ষা নিয়ম
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-এর জন্য এক্সিকিউশনের আগে ব্লকিং** — একটি কমান্ড একটি
PreToolUse হুক ইনস্টল করে যা মিলে যাওয়া টুল কলগুলোকে চালু হওয়ার *আগে* থামিয়ে
দেয় এবং আপনার সিদ্ধান্তের জন্য অপেক্ষা করে (আপনার ফোন থেকে এক-ট্যাপে,
[cloud push notifications](https://app.clawmetry.com/push) সক্রিয় থাকলে):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

একটি ডিনাই শুধু সেই একটি টুল কলকেই ব্লক করে — এজেন্ট তার সেশন ধরে রাখে এবং
অন্য পদ্ধতি চেষ্টা করতে পারে। আপনার ফোনে অনুমোদন করলে Claude Code-এর নিজস্ব
পারমিশন প্রম্পট এড়িয়ে যায় (আপনি ইতিমধ্যে উত্তর দিয়েছেন)। অমিলযুক্ত টুলগুলোর
খরচ ~৪০ms এবং সেগুলো Claude Code-এর স্বাভাবিক পারমিশন ফ্লোতে পড়ে যায়। এছাড়াও
Claude Code নিজে যখন আপনার জন্য অপেক্ষা করছে তখনও আপনি একটি ফোন পুশ পাবেন
(`permission_prompt` / `idle_prompt` নোটিফিকেশন)।

## ইনস্টল

**এক-লাইনার (প্রস্তাবিত):**
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

v2 React অ্যাপটি `frontend/`-এ থাকে এবং যখন Flask সার্ভার v2 সক্রিয় করে চালু
করা হয় তখন `/v2`-এ পরিবেশন করা হয়।

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

`http://localhost:5173/v2/` খুলুন। Vite `/api` অনুরোধগুলো
`http://localhost:8900`-এ প্রক্সি করে, যাতে React অ্যাপ অতিরিক্ত CORS
সেটআপ ছাড়াই স্থানীয় Flask সার্ভারের সাথে কথা বলতে পারে।

Python প্যাকেজের সাথে পাঠানো বান্ডেল তৈরি করতে:

```bash
cd frontend
npm run build
```

প্রোডাকশন বান্ডেলটি `clawmetry/static/v2/dist/`-এ লেখা হয়।

## রানটাইম / এজেন্ট সামঞ্জস্যতা

ClawMetry শুধু OpenClaw নয়, আরও অনেক AI-এজেন্ট রানটাইম পর্যবেক্ষণ করে। প্রতিটি নন-OpenClaw রানটাইমে একটি নিবেদিত রিডার অ্যাডাপ্টার থাকে যা তার নেটিভ সেশন ফরম্যাটকে ClawMetry-এর ইউনিফাইড শেপে রূপান্তর করে; ডেমন সেগুলোকে একই DuckDB স্টোর + ক্লাউড স্ন্যাপশটে ইনজেস্ট করে, রানটাইম দিয়ে ট্যাগ করে, এবং Session replay ট্যাব একের বেশি রানটাইম থাকলে একটি **রানটাইম সুইচার** দেখায়। সম্পূর্ণ ম্যাট্রিক্স + নতুন রানটাইম যোগ করার গাইডের জন্য দেখুন [`docs/compatibility.md`](docs/compatibility.md), এবং OpenClaw-family প্রাইমারের জন্য [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)।

[Perplexity-এর numbat](https://github.com/perplexityai/numbat) এজেন্ট-সিকিউরিটি টুল চালাচ্ছেন? ClawMetry এটির ফলাফল এবং এনফোর্সমেন্ট সিদ্ধান্ত সরাসরি ইনজেস্ট করে — দেখুন [`docs/NUMBAT.md`](docs/NUMBAT.md)।

| রানটাইম / এজেন্ট | স্ট্যাটাস | নোট |
|---|---|---|
| **OpenClaw** | নেটিভ | রেফারেন্স রানটাইম, স্বয়ংক্রিয়ভাবে সনাক্ত হয় |
| **PicoClaw** | বিটা অ্যাডাপ্টার | ফ্ল্যাট `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ট্রান্সক্রিপ্ট, মডেল, টুল কল। |
| **NanoClaw** | বিটা অ্যাডাপ্টার | প্রতি-সেশন SQLite (`data/v2-sessions`)। ট্রান্সক্রিপ্ট + বার্তা সংখ্যা। |
| **Hermes** | বিটা অ্যাডাপ্টার | SQLite `~/.hermes/state.db`। ট্রান্সক্রিপ্ট, মডেল, টোকেন/খরচ। |
| **Claude Code** | বিটা অ্যাডাপ্টার | JSONL `~/.claude/projects/.../<id>.jsonl`। ট্রান্সক্রিপ্ট, মডেল, টুল কল + থিংকিং, টোকেন ব্যবহার। |
| **Codex** | বিটা অ্যাডাপ্টার | Rollout JSONL `~/.codex/sessions/...`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Cursor** | বিটা অ্যাডাপ্টার | SQLite `state.vscdb`। চ্যাট/কম্পোজার ট্রান্সক্রিপ্ট, মডেল। |
| **Aider** | বিটা অ্যাডাপ্টার | প্রতি প্রজেক্টে `.aider.chat.history.md`। ট্রান্সক্রিপ্ট, মডেল, টোকেন গণনা। |
| **Goose** | বিটা অ্যাডাপ্টার | SQLite `~/.local/share/goose`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন মোট। |
| **opencode** | বিটা অ্যাডাপ্টার | SQLite `~/.local/share/opencode`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Qwen Code** | বিটা অ্যাডাপ্টার | JSONL `~/.qwen/projects/.../chats`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Pi** | বিটা অ্যাডাপ্টার | JSONL `~/.pi/agent/sessions`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Deep Agents** | বিটা অ্যাডাপ্টার | SQLite `~/.deepagents/.state/sessions.db`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **n8n** | বিটা অ্যাডাপ্টার | SQLite `~/.n8n/database.sqlite`। ওয়ার্কফ্লো এক্সিকিউশন, নোড রান, AI Agent প্রম্পট, মডেল + টোকেন যেখানে n8n তা রেকর্ড করে। |
| **Antigravity** | বিটা অ্যাডাপ্টার | `~/.gemini/<flavor>/brain/`-এর অধীনে ব্রেইন JSONL। কথোপকথন, টুল স্টেপ, থিংকিং, প্রতি-জেনারেশন Gemini টোকেন বিভাজন + খরচ, ব্যাকগ্রাউন্ড-জেনারেশন বার্ন। |
| **GitHub Copilot** | বিটা অ্যাডাপ্টার | Copilot CLI `events.jsonl` `~/.copilot/session-state/`-এর অধীনে + প্রতি-কল ব্যবহারের লেজার `session-store.db`। কথোপকথন, টুল কল, মডেল রাউটিং, ক্যাশ-সচেতন টোকেন বিভাজন, ভেন্ডর-বিলড AI-ক্রেডিট খরচ। |
| **Grok** | বিটা অ্যাডাপ্টার | xAI Grok Build CLI (`~/.grok/bin/grok`-এর অধীনে Rust বাইনারি): গ্লোবাল ইভেন্ট লগ `~/.grok/logs/unified.jsonl` + প্রতি-সেশন `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`। কথোপকথন, প্রতি-টার্ন টোকেন বিভাজন, মডেল রাউটিং, এবং CLI-এর আউটবাউন্ড রিপো পেলোড `~/.grok/upload_queue/`-এ স্টেজ করা থাকে যাতে আপনার মেশিন থেকে কী বেরিয়ে গেছে তা দেখতে পারেন। |

"বিটা অ্যাডাপ্টার" মানে ClawMetry সেই রানটাইমের প্রকৃত অন-ডিস্ক ফরম্যাটের জন্য একটি রিডার সরবরাহ করে, প্রতিটি একটি বাস্তব মেশিনে বাস্তব ইনস্টলের বিরুদ্ধে তৈরি + যাচাই করা হয়েছে (দেখুন `tests/fixtures/runtimes/<rt>/`)। অ্যাডাপ্টারগুলো রিড-অনলি; প্রতিটি সৎ যে তার রানটাইম প্রকৃতপক্ষে কী সংরক্ষণ করে (যেমন, PicoClaw/NanoClaw/Cursor ডিস্কে টোকেন খরচ লেখে না)। যখন একটি নোডে একাধিক রানটাইম চলে, তখন রানটাইম সুইচার সেশন ভিউকে পরিষ্কার গভীর-বিশ্লেষণের জন্য একটিতে সীমাবদ্ধ করে।

## যেকোনো SDK এজেন্ট ট্র্যাক করুন — আউট-লুপ খরচ অ্যাট্রিবিউশন

উপরের রানটাইমগুলো সবাই ডিস্কে সেশন লেখে। আপনার নিজের **প্রোডাকশন এজেন্ট** — যেটি আপনি OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, বা একটি সাধারণ `httpx` লুপের উপর তৈরি করেছেন — তা করে না। ClawMetry-এর শূন্য-কনফিগ ইন্টারসেপ্টর তবুও `httpx`/`requests` মাংকি-প্যাচ করে এর LLM কল (খরচ, টোকেন, লেটেন্সি, ত্রুটি) ক্যাপচার করে:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (অথবা `CLAWMETRY_SOURCE=support-agent` env ভেরিয়েবল) প্রতিটি কলকে একটি **নামযুক্ত সোর্স** দিয়ে ট্যাগ করে, যাতে আপনার চালানো প্রতিটি প্রোডাক্ট ড্যাশবোর্ডের Overview-এর **🔌 Out-loop sources** কার্ডে একটি স্বতন্ত্র, খরচ-অ্যাট্রিবিউট করা যায় এমন লাইন হিসেবে দেখা যায় — প্রতি এজেন্টে কল, প্রোভাইডার, লেটেন্সি, ত্রুটির হার। কোনো সোর্স সেট করা না থাকলে? কলগুলো তবুও ট্র্যাক করা হয়; কার্ডটি শুধু লুকানো থাকে।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

এটি একই ডেটা লেয়ার যা রানটাইম অ্যাডাপ্টারগুলো খাওয়ায় (DuckDB → ক্লাউড স্ন্যাপশট), তাই আউট-লুপ সোর্সগুলো বাকি সবকিছুর মতোই ক্লাউড ড্যাশবোর্ডে সিঙ্ক হয়, এন্ড-টু-এন্ড এনক্রিপ্টেড।

## OpenTelemetry — ভেন্ডর-নিরপেক্ষ, আপনার ট্রেস যেখানে ইচ্ছা পাঠান

ClawMetry উভয় দিকে **OpenTelemetry** বলে, **GenAI সিমান্টিক কনভেনশন** ব্যবহার করে, তাই আপনার এজেন্ট ট্রেসগুলো কখনো একটি টুলে আটকে থাকে না।

প্রতিটি সেশন — LLM কল, টুলস, সাব-এজেন্ট, টোকেন, খরচ — **এক্সপোর্ট** করুন OTLP/HTTP GenAI স্প্যান হিসেবে যেকোনো কালেক্টরে (Datadog, Grafana, Honeycomb, বা আপনার নিজের OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth হেডার এবং পোল ইন্টারভাল ঐচ্ছিক env ভেরিয়েবল:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ইনজেস্ট** — বিল্ট-ইন OTLP রিসিভার `/v1/traces` এবং `/v1/metrics`-এ অন্য যেকোনো জায়গা থেকে ট্রেস এবং মেট্রিক্স গ্রহণ করে (প্রোটোবাফ ইনজেস্টের জন্য `pip install clawmetry[otel]`)।

আপনি শূন্য-কনফিগ, স্থানীয়-প্রথম ClawMetry ড্যাশবোর্ড **এবং** আপনার দল ইতিমধ্যে চালাচ্ছে এমন যেকোনো ব্যাকএন্ডে আপনার ডেটা পাবেন — কোনো লক-ইন নেই, দ্বিতীয় কোনো এজেন্ট ইনস্টল করতে হবে না।

## কনফিগারেশন

বেশিরভাগ মানুষের কোনো কনফিগারেশন লাগে না। ClawMetry স্বয়ংক্রিয়ভাবে আপনার ওয়ার্কস্পেস, লগ, সেশন এবং ক্রন সনাক্ত করে।

কাস্টমাইজ করার প্রয়োজন হলে:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

সব অপশন: `clawmetry --help`

## সমর্থিত চ্যানেল

আপনি কনফিগার করা প্রতিটি OpenClaw চ্যানেলের জন্য ClawMetry লাইভ কার্যকলাপ দেখায়। শুধুমাত্র সেই চ্যানেলগুলো যেগুলো আপনার `openclaw.json`-এ প্রকৃতপক্ষে সেটআপ করা আছে সেগুলোই Flow ডায়াগ্রামে দেখা যায় — কনফিগার না করাগুলো স্বয়ংক্রিয়ভাবে লুকানো থাকে।

Flow-এ যেকোনো চ্যানেল নোডে ক্লিক করে ইনকামিং/আউটগোয়িং বার্তা সংখ্যা সহ একটি লাইভ চ্যাট বাবল ভিউ দেখুন।

| চ্যানেল | স্ট্যাটাস | লাইভ পপআপ | নোট |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ পূর্ণ | ✅ | বার্তা, পরিসংখ্যান, ১০সে রিফ্রেশ |
| 💬 **iMessage** | ✅ পূর্ণ | ✅ | সরাসরি `~/Library/Messages/chat.db` পড়ে |
| 💚 **WhatsApp** | ✅ পূর্ণ | ✅ | WhatsApp Web (Baileys) এর মাধ্যমে |
| 🔵 **Signal** | ✅ পূর্ণ | ✅ | signal-cli এর মাধ্যমে |
| 🟣 **Discord** | ✅ পূর্ণ | ✅ | গিল্ড + চ্যানেল সনাক্তকরণ |
| 🟪 **Slack** | ✅ পূর্ণ | ✅ | ওয়ার্কস্পেস + চ্যানেল সনাক্তকরণ |
| 🌐 **Webchat** | ✅ পূর্ণ | ✅ | বিল্ট-ইন ওয়েব UI সেশন |
| 📡 **IRC** | ✅ পূর্ণ | ✅ | টার্মিনাল-স্টাইল বাবল UI |
| 🍏 **BlueBubbles** | ✅ পূর্ণ | ✅ | BlueBubbles REST API এর মাধ্যমে iMessage |
| 🔵 **Google Chat** | ✅ পূর্ণ | ✅ | Chat API ওয়েবহুকের মাধ্যমে |
| 🟣 **MS Teams** | ✅ পূর্ণ | ✅ | Teams বট প্লাগইনের মাধ্যমে |
| 🔷 **Mattermost** | ✅ পূর্ণ | ✅ | সেলফ-হোস্টেড টিম চ্যাট |
| 🟩 **Matrix** | ✅ পূর্ণ | ✅ | বিকেন্দ্রীভূত, E2EE সমর্থন |
| 🟢 **LINE** | ✅ পূর্ণ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ পূর্ণ | ✅ | বিকেন্দ্রীভূত NIP-04 DM |
| 🟣 **Twitch** | ✅ পূর্ণ | ✅ | IRC সংযোগের মাধ্যমে চ্যাট |
| 🔷 **Feishu/Lark** | ✅ পূর্ণ | ✅ | WebSocket ইভেন্ট সাবস্ক্রিপশন |
| 🔵 **Zalo** | ✅ পূর্ণ | ✅ | Zalo Bot API |

> **স্বয়ংক্রিয় সনাক্তকরণ:** ClawMetry আপনার `~/.openclaw/openclaw.json` পড়ে এবং শুধুমাত্র আপনি প্রকৃতপক্ষে কনফিগার করা চ্যানেলগুলো রেন্ডার করে। ম্যানুয়াল সেটআপের প্রয়োজন নেই।

## Docker ডিপ্লয়মেন্ট

একটি কন্টেইনারে ClawMetry চালাতে চান? কোনো সমস্যা নেই! 🐳

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

> **নোট:** Docker-এ চালানোর সময়, আপনার এজেন্টের ডেটা + লগ ডিরেক্টরিগুলো মাউন্ট করুন (যেমন, `~/.openclaw`, `~/.claude`, `~/.codex`) যাতে ClawMetry আপনার সেটআপ স্বয়ংক্রিয়ভাবে সনাক্ত করতে পারে।

## প্রয়োজনীয়তা

- Python 3.8+
- Flask (pip এর মাধ্যমে স্বয়ংক্রিয়ভাবে ইনস্টল হয়)
- একই মেশিনে একটি AI এজেন্ট রানটাইম: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, অথবা QM (অথবা Docker-এর জন্য মাউন্ট করা ভলিউম)
- Linux অথবা macOS

## NemoClaw / OpenShell সমর্থন

ClawMetry স্বয়ংক্রিয়ভাবে [NemoClaw](https://github.com/NVIDIA/NemoClaw) সনাক্ত করে — NVIDIA-এর এন্টারপ্রাইজ সিকিউরিটি র‍্যাপার যা OpenClaw-এর জন্য স্যান্ডবক্সড OpenShell কন্টেইনারের ভেতরে এজেন্ট চালায়।

বেশিরভাগ ক্ষেত্রে কোনো অতিরিক্ত কনফিগারেশনের প্রয়োজন নেই। সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে সেশন ফাইল খুঁজে বের করে সেগুলো হোস্টে `~/.openclaw/`-এ থাকুক বা একটি OpenShell কন্টেইনারের ভেতরে থাকুক।

### এটি কীভাবে কাজ করে

ClawMetry দুইভাবে NemoClaw সনাক্ত করে:

1. **বাইনারি সনাক্তকরণ** — `nemoclaw` CLI-এর জন্য চেক করে এবং স্যান্ডবক্স তথ্য পেতে `nemoclaw status` চালায়
2. **কন্টেইনার সনাক্তকরণ** — `openshell`, `nemoclaw`, বা `ghcr.io/nvidia/` ইমেজের জন্য চলমান Docker কন্টেইনার স্ক্যান করে, তারপর ভলিউম মাউন্ট বা `docker cp`-এর মাধ্যমে সেশন পড়ে

NemoClaw কন্টেইনার থেকে সিঙ্ক করা সেশন ফাইলগুলো ক্লাউড ড্যাশবোর্ডে `runtime=nemoclaw` এবং `container_id` মেটাডেটা দিয়ে ট্যাগ করা হয়, যাতে আপনি এক নজরে স্ট্যান্ডার্ড OpenClaw সেশন থেকে সেগুলো আলাদা করতে পারেন।

### প্রস্তাবিত সেটআপ: হোস্টে সিঙ্ক ডেমন

সেরা অভিজ্ঞতার জন্য, ClawMetry-এর সিঙ্ক ডেমন **হোস্ট মেশিনে** (স্যান্ডবক্সের ভেতরে নয়) চালান। এটি NemoClaw নেটওয়ার্ক নীতি বিধিনিষেধ এড়িয়ে যায়।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে যেকোনো চলমান OpenShell কন্টেইনারের ভেতরে সেশন খুঁজে পাবে।

### ঐচ্ছিক: স্পষ্ট স্যান্ডবক্স নাম

স্বয়ংক্রিয় সনাক্তকরণ কাজ না করলে, ClawMetry-কে সঠিক স্যান্ডবক্সের দিকে নির্দেশ করুন:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### স্যান্ডবক্সের ভেতরে চালানো (উন্নত)

আপনাকে যদি স্যান্ডবক্সের **ভেতরে** OpenShell সিঙ্ক ডেমন চালাতে হয়, তবে আপনার NemoClaw নেটওয়ার্ক নীতিতে এই এগ্রেস নিয়মটি যোগ করুন যাতে এটি ClawMetry ইনজেস্ট API পৌঁছাতে পারে:

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
| `ingest.clawmetry.com` | 443 | HTTPS | হ্যাঁ (সিঙ্ক ডেমন → ক্লাউড) |
| `localhost:8900` | 8900 | HTTP | হ্যাঁ (স্থানীয় ড্যাশবোর্ড UI) |
| Docker সকেট (`/var/run/docker.sock`) | — | Unix সকেট | কন্টেইনার সেশন আবিষ্কারের জন্য |

সিঙ্ক ডেমন শুধুমাত্র `ingest.clawmetry.com`-এ আউটবাউন্ড HTTPS কল করে। কোনো ইনবাউন্ড পোর্টের প্রয়োজন নেই।

---

## ক্লাউড ডিপ্লয়মেন্ট

SSH টানেল, রিভার্স প্রক্সি এবং Docker-এর জন্য দেখুন **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**।

## টেস্টিং

এই প্রজেক্টটি BrowserStack দিয়ে টেস্ট করা হয়েছে।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## টেলিমেট্রি

ClawMetry `https://app.clawmetry.com/api/install`-এ বেনামী
ইনস্টল-লাইফসাইকেল পিং পাঠায়: একটি নতুন মেশিনে প্রথমবার `clawmetry`
CLI চালানোর সময় একটি `install` পিং, একটি নতুন সংস্করণে আপগ্রেড করার
পর প্রথম রানে একটি `update` পিং, এবং ড্যাশবোর্ডের মধ্যে অনবোর্ডিং
পছন্দ সম্পূর্ণ করার সময় একটি `onboarded` পিং। আমরা এটি প্রকৃত ইনস্টল
গণনা করতে ব্যবহার করি (কাঁচা PyPI ডাউনলোড সংখ্যা প্রায় ৯৮% মিরর, CI,
এবং স্বয়ংক্রিয়-আপডেট পুনরায়-ডাউনলোড) এবং কোন এজেন্ট ফ্রেমওয়ার্ক এবং
সংস্করণ প্রকৃতপক্ষে ব্যবহার হচ্ছে তা জানতে।

**প্রতি লাইফসাইকেল ইভেন্ট প্রতি সংস্করণে সর্বোচ্চ একটি POST**, যাতে থাকে:

| ফিল্ড | উদাহরণ | কারণ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-এ সংরক্ষিত এলোমেলো UUID | ডিডুপ; আপনি স্পষ্টভাবে Cloud sync সংযুক্ত না করা পর্যন্ত বেনামী (তারপর প্রমাণীকৃত ডেমন হার্টবিট এটি বহন করে, এই ইনস্টলটিকে আপনার অ্যাকাউন্টের সাথে লিঙ্ক করে) |
| `event` | `install` / `update` / `onboarded` | নতুন ইনস্টল বনাম বিদ্যমান একটির আপগ্রেড |
| `version` | `0.12.167` | কোন সংস্করণগুলো ব্যবহার হচ্ছে |
| `os` / `os_version` | `Darwin` / `25.3.0` | প্ল্যাটফর্ম সমর্থনের অগ্রাধিকার |
| `python` | `3.11.15` | Python সংস্করণ সমর্থন ম্যাট্রিক্স |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | আমাদের পরবর্তীতে কোন এজেন্টের সাথে ইন্টিগ্রেট করা উচিত |
| `is_ci` / `ci_provider` | `true` / `github_actions` | মানব ইনস্টল থেকে CI নয়েজ আলাদা করা |

**আমরা যা পাঠাই না**: IP (ক্লাউড সার্ভার-সাইডে অনুরোধ থেকে দেশের কোড
আহরণ করে, তারপর IP বাদ দেয়), হোস্টনেম, ইউজারনেম, ওয়ার্কস্পেস পাথ, ফাইল
বিষয়বস্তু, আপনার api_key, আপনার ইমেইল, PII বা ওয়ার্কস্পেস-নির্দিষ্ট কিছু।
ওয়্যার পেলোডটি [`clawmetry/telemetry.py`](clawmetry/telemetry.py)-এ
নিরীক্ষণযোগ্য।

**অপ্ট আউট** (এর যেকোনো একটি এটি স্থায়ীভাবে নিষ্ক্রিয় করে):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

নেটওয়ার্ক ব্যর্থতা কখনো `clawmetry`-কে চলা থেকে ব্লক করে না — পিংটি
একটি ডেমন থ্রেডে ৩ সেকেন্ড টাইমআউট সহ ফায়ার-অ্যান্ড-ফরগেট।

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
  <sub>তৈরি করেছেন <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ইকোসিস্টেমের অংশ</sub>
</p>
