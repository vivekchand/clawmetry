<!-- i18n-src:8252f6b1d31d -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টকে ভাবতে দেখুন।** **১৪টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজার্ভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ১০টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটিমাত্র ড্যাশবোর্ড।

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। কোনো কনফিগারেশন লাগে না। সবকিছু নিজে থেকেই সনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

এটি **http://localhost:8900** এ খোলে, ব্যস, হয়ে গেল।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ১৪টি এজেন্ট রানটাইমের সাথে কাজ করে

ClawMetry শুরু হয়েছিল OpenClaw-এর জন্য অবজার্ভেবিলিটি হিসেবে, আর এখন এটি একটি মাত্র ড্যাশবোর্ডে আপনার **পুরো এজেন্ট ফ্লিট** পরিমাপ করে, আপনার মেশিনে প্রতিটি রানটাইম স্বয়ংক্রিয়ভাবে সনাক্ত করে:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw এবং NemoClaw ওপেন-সোর্স অ্যাপে বিনামূল্যে পাওয়া যায়; বাকি রানটাইমগুলো ClawMetry Cloud অথবা সেলফ-হোস্টেড Pro লাইসেন্সের মাধ্যমে সক্রিয় হয়। হেডার থেকে রানটাইম পরিবর্তন করুন এবং প্রতিটি ট্যাব — খরচ, টোকেন, টুল, ট্রেস — সেই রানটাইমে পুনরায় স্কোপ হয়ে যাবে। সঠিক ফ্রি/পেইড বিভাজন, টায়ার ম্যাট্রিক্স, `/api/entitlement` শেপ এবং `clawmetry license` CLI-এর জন্য **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** দেখুন।

## আপনি যা পাবেন

- **Flow** — চ্যানেল, ব্রেইন, টুল এবং ফিরতি পথ দিয়ে বার্তা প্রবাহ দেখানো লাইভ অ্যানিমেটেড ডায়াগ্রাম
- **Overview** — স্বাস্থ্য পরীক্ষা, অ্যাক্টিভিটি হিটম্যাপ, সেশন সংখ্যা, মডেল তথ্য
- **Usage** — দৈনিক/সাপ্তাহিক/মাসিক বিভাজন সহ টোকেন এবং খরচ ট্র্যাকিং
- **Sessions** — মডেল, টোকেন, সর্বশেষ কার্যকলাপ সহ সক্রিয় এজেন্ট সেশন
- **Crons** — স্ট্যাটাস, পরবর্তী রান, সময়কাল সহ শিডিউল করা জব
- **Logs** — রঙ-কোডেড রিয়েল-টাইম লগ স্ট্রিমিং
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, দৈনিক নোট ব্রাউজ করুন
- **Transcripts** — সেশন হিস্ট্রি পড়ার জন্য চ্যাট-বাবল UI
- **Alerts** — বাজেট ক্যাপ, এরর-রেট ট্রিগার, এজেন্ট-অফলাইন সনাক্তকরণ; Slack, Discord, PagerDuty, Telegram, Email-এ রুট করে
- **Approvals** — ধ্বংসাত্মক ডিলিট, ফোর্স পুশ, DB মিউটেশন, sudo, প্যাকেজ ইনস্টল, নেটওয়ার্ক কলগুলো এক-ক্লিক সাইন-অফের পেছনে আটকে দিন

## স্ক্রিনশট

### 🧠 Brain — লাইভ এজেন্ট ইভেন্ট স্ট্রিম
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — টোকেন ব্যবহার ও সেশন সারাংশ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — রিয়েল-টাইম টুল কল ফিড
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — মডেল ও সেশন অনুযায়ী খরচ বিভাজন
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ওয়ার্কস্পেস ফাইল ব্রাউজার
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — অবস্থান ও অডিট লগ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — বাজেট ক্যাপ, এরর-রেট ট্রিগার, Slack / Discord / PagerDuty / Email-এ ওয়েবহুক
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ম্যানুয়াল সাইন-অফের পেছনে ঝুঁকিপূর্ণ টুল কল আটকে দিন; পলিসি-সমর্থিত সুরক্ষা নিয়ম
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-এর জন্য প্রি-এক্সিকিউশন ব্লকিং** — একটি কমান্ড একটি
PreToolUse হুক ইনস্টল করে যা মিল খাওয়া টুল কলগুলো রান হওয়ার *আগেই* থামিয়ে দেয় এবং
আপনার সিদ্ধান্তের জন্য অপেক্ষা করে ([ক্লাউড পুশ নোটিফিকেশন](https://app.clawmetry.com/push)
সক্রিয় থাকলে আপনার ফোন থেকে এক ট্যাপেই):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

একটি ডিনাই শুধু সেই একটি টুল কলকেই ব্লক করে — এজেন্ট তার সেশন বজায় রাখে এবং
অন্য একটি পন্থা চেষ্টা করতে পারে। আপনার ফোনে অনুমোদন দিলে তা Claude Code-এর নিজস্ব
পারমিশন প্রম্পট এড়িয়ে যায় (আপনি ইতিমধ্যে উত্তর দিয়েছেন)। মিল না খাওয়া টুলগুলোর
খরচ হয় ~৪০ms এবং সেগুলো Claude Code-এর স্বাভাবিক পারমিশন ফ্লো-তে চলে যায়।
Claude Code নিজে আপনার জন্য অপেক্ষা করলেও (`permission_prompt` /
`idle_prompt` নোটিফিকেশন) আপনি ফোনে পুশ পাবেন।

## ইনস্টল

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

v2 React অ্যাপটি `frontend/`-এ থাকে এবং v2 সক্রিয় করে Flask
সার্ভার চালু করা হলে এটি `/v2`-এ সার্ভ করা হয়।

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

`http://localhost:5173/v2/` খুলুন। Vite `/api` রিকোয়েস্টগুলো
`http://localhost:8900`-এ প্রক্সি করে, তাই React অ্যাপটি অতিরিক্ত CORS
সেটআপ ছাড়াই লোকাল Flask সার্ভারের সাথে কথা বলতে পারে।

Python প্যাকেজের সাথে শিপ হওয়া বান্ডেল বিল্ড করতে:

```bash
cd frontend
npm run build
```

প্রোডাকশন বান্ডেলটি `clawmetry/static/v2/dist/`-এ লেখা হয়।

## রানটাইম / এজেন্ট সামঞ্জস্যতা

ClawMetry শুধু OpenClaw নয়, আরও অনেক AI-এজেন্ট রানটাইম পর্যবেক্ষণ করে। প্রতিটি নন-OpenClaw রানটাইমে একটি ডেডিকেটেড রিডার অ্যাডাপ্টার থাকে যা তার নেটিভ সেশন ফরম্যাটকে ClawMetry-এর ইউনিফাইড শেপে রূপান্তরিত করে; ডেমন সেগুলোকে রানটাইম দিয়ে ট্যাগ করে একই DuckDB স্টোর + ক্লাউড স্ন্যাপশটে ইনজেস্ট করে, এবং একাধিক রানটাইম উপস্থিত থাকলে Session replay ট্যাব একটি **রানটাইম সুইচার** দেখায়। সম্পূর্ণ ম্যাট্রিক্স + রানটাইম যোগ করার গাইডের জন্য [`docs/compatibility.md`](docs/compatibility.md) এবং OpenClaw-ফ্যামিলি প্রাইমারের জন্য [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) দেখুন।

| রানটাইম / এজেন্ট | স্ট্যাটাস | নোট |
|---|---|---|
| **OpenClaw** | নেটিভ | রেফারেন্স রানটাইম, স্বয়ংক্রিয়ভাবে সনাক্ত করা হয় |
| **PicoClaw** | বেটা অ্যাডাপ্টার | ফ্ল্যাট `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ট্রান্সক্রিপ্ট, মডেল, টুল কল। |
| **NanoClaw** | বেটা অ্যাডাপ্টার | প্রতি-সেশন SQLite (`data/v2-sessions`)। ট্রান্সক্রিপ্ট + বার্তা সংখ্যা। |
| **Hermes** | বেটা অ্যাডাপ্টার | SQLite `~/.hermes/state.db`। ট্রান্সক্রিপ্ট, মডেল, টোকেন/খরচ। |
| **Claude Code** | বেটা অ্যাডাপ্টার | JSONL `~/.claude/projects/.../<id>.jsonl`। ট্রান্সক্রিপ্ট, মডেল, টুল কল + থিংকিং, টোকেন ব্যবহার। |
| **Codex** | বেটা অ্যাডাপ্টার | Rollout JSONL `~/.codex/sessions/...`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Cursor** | বেটা অ্যাডাপ্টার | SQLite `state.vscdb`। চ্যাট/কম্পোজার ট্রান্সক্রিপ্ট, মডেল। |
| **Aider** | বেটা অ্যাডাপ্টার | প্রতি প্রজেক্টে `.aider.chat.history.md`। ট্রান্সক্রিপ্ট, মডেল, টোকেন গণনা। |
| **Goose** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/goose`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন টোটাল। |
| **opencode** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/opencode`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Qwen Code** | বেটা অ্যাডাপ্টার | JSONL `~/.qwen/projects/.../chats`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Pi** | বেটা অ্যাডাপ্টার | JSONL `~/.pi/agent/sessions`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Deep Agents** | বেটা অ্যাডাপ্টার | SQLite `~/.deepagents/.state/sessions.db`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **n8n** | বেটা অ্যাডাপ্টার | SQLite `~/.n8n/database.sqlite`। ওয়ার্কফ্লো এক্সিকিউশন, নোড রান, AI Agent প্রম্পট, n8n যেখানে রেকর্ড করে সেখানে মডেল + টোকেন। |

"বেটা অ্যাডাপ্টার" মানে ClawMetry সেই রানটাইমের প্রকৃত অন-ডিস্ক ফরম্যাটের জন্য একটি রিডার শিপ করে, প্রতিটি একটি প্রকৃত মেশিনে প্রকৃত ইনস্টলের বিপরীতে তৈরি + যাচাই করা হয়েছে (দেখুন `tests/fixtures/runtimes/<rt>/`)। অ্যাডাপ্টারগুলো রিড-ওনলি; প্রতিটি তার রানটাইম প্রকৃতপক্ষে যা সংরক্ষণ করে সে সম্পর্কে সৎ (যেমন PicoClaw/NanoClaw/Cursor ডিস্কে টোকেন খরচ লেখে না)। একই নোডে একাধিক রানটাইম চললে, রানটাইম সুইচার সেশন ভিউকে একটি পরিষ্কার ডিপ-ডাইভের জন্য একটিতে স্কোপ করে।

## যেকোনো SDK এজেন্ট ট্র্যাক করুন — আউট-লুপ খরচ অ্যাট্রিবিউশন

উপরের রানটাইমগুলো সবই সেশন ডিস্কে লেখে। আপনার নিজের **প্রোডাকশন এজেন্ট** — যেটি আপনি OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, অথবা একটি সাধারণ `httpx` লুপের ওপর বানিয়েছেন — তা করে না। ClawMetry-এর জিরো-কনফিগ ইন্টারসেপ্টর তবুও `httpx`/`requests`-কে মাংকি-প্যাচ করে তার LLM কলগুলো (খরচ, টোকেন, লেটেন্সি, এরর) ক্যাপচার করে:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (অথবা `CLAWMETRY_SOURCE=support-agent` এনভায়রনমেন্ট ভেরিয়েবল) প্রতিটি কলকে একটি **নামযুক্ত সোর্স** দিয়ে ট্যাগ করে, ফলে আপনার চালানো প্রতিটি প্রোডাক্ট ড্যাশবোর্ডের Overview-এর **🔌 আউট-লুপ সোর্স** কার্ডে নিজস্ব প্রথম-শ্রেণীর, খরচ-অ্যাট্রিবিউটযোগ্য লাইন হিসেবে দেখা যায় — প্রতি এজেন্টে কল, প্রোভাইডার, লেটেন্সি, এরর রেট। কোনো সোর্স সেট করা নেই? কলগুলো তবুও ট্র্যাক হয়; কার্ডটি শুধু লুকানো থাকে।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

এটি সেই একই ডেটা লেয়ার যা রানটাইম অ্যাডাপ্টারগুলো ফিড করে (DuckDB → ক্লাউড স্ন্যাপশট), তাই আউট-লুপ সোর্সগুলো বাকি সবকিছুর মতোই ক্লাউড ড্যাশবোর্ডে সিঙ্ক হয়, E2E-এনক্রিপ্টেড অবস্থায়।

## OpenTelemetry — ভেন্ডর-নিরপেক্ষ, আপনার ট্রেস যেকোনো জায়গায় পাঠান

ClawMetry উভয় দিকেই **OpenTelemetry** বলে, **GenAI সিমান্টিক কনভেনশন** ব্যবহার করে, তাই আপনার এজেন্ট ট্রেসগুলো কখনো একটি টুলে আটকে থাকে না।

প্রতিটি সেশন — LLM কল, টুল, সাব-এজেন্ট, টোকেন, খরচ — যেকোনো কালেক্টরে (Datadog, Grafana, Honeycomb, অথবা আপনার নিজস্ব OTel Collector) OTLP/HTTP GenAI স্প্যান হিসেবে **এক্সপোর্ট** করুন:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

অথ হেডার এবং পোল ইন্টারভাল ঐচ্ছিক এনভায়রনমেন্ট ভেরিয়েবল:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ইনজেস্ট** — বিল্ট-ইন OTLP রিসিভার অন্য যেকোনো কিছু থেকে `/v1/traces` এবং `/v1/metrics`-এ ট্রেস এবং মেট্রিক্স গ্রহণ করে (প্রোটোবাফ ইনজেস্টের জন্য `pip install clawmetry[otel]`)।

আপনি জিরো-কনফিগ, লোকাল-ফার্স্ট ClawMetry ড্যাশবোর্ড **এবং** আপনার টিম ইতিমধ্যে যে ব্যাকএন্ড চালায় তাতে আপনার ডেটা দুটোই পাবেন — কোনো লক-ইন নেই, দ্বিতীয় কোনো এজেন্ট ইনস্টল করার দরকার নেই।

## কনফিগারেশন

বেশিরভাগ মানুষের কোনো কনফিগারেশনের দরকার হয় না। ClawMetry আপনার ওয়ার্কস্পেস, লগ, সেশন এবং ক্রন স্বয়ংক্রিয়ভাবে সনাক্ত করে।

কাস্টমাইজ করার দরকার হলে:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

সব অপশন: `clawmetry --help`

## সমর্থিত চ্যানেল

আপনার কনফিগার করা প্রতিটি OpenClaw চ্যানেলের জন্য ClawMetry লাইভ কার্যকলাপ দেখায়। শুধুমাত্র আপনার `openclaw.json`-এ প্রকৃতপক্ষে সেটআপ করা চ্যানেলগুলোই Flow ডায়াগ্রামে দেখা যায় — কনফিগার না করা চ্যানেলগুলো স্বয়ংক্রিয়ভাবে লুকানো থাকে।

Flow-তে যেকোনো চ্যানেল নোড ক্লিক করলে ইনকামিং/আউটগোয়িং বার্তা গণনা সহ একটি লাইভ চ্যাট বাবল ভিউ দেখা যায়।

| চ্যানেল | স্ট্যাটাস | লাইভ পপআপ | নোট |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ সম্পূর্ণ | ✅ | বার্তা, পরিসংখ্যান, ১০সে রিফ্রেশ |
| 💬 **iMessage** | ✅ সম্পূর্ণ | ✅ | সরাসরি `~/Library/Messages/chat.db` পড়ে |
| 💚 **WhatsApp** | ✅ সম্পূর্ণ | ✅ | WhatsApp Web (Baileys) এর মাধ্যমে |
| 🔵 **Signal** | ✅ সম্পূর্ণ | ✅ | signal-cli এর মাধ্যমে |
| 🟣 **Discord** | ✅ সম্পূর্ণ | ✅ | গিল্ড + চ্যানেল সনাক্তকরণ |
| 🟪 **Slack** | ✅ সম্পূর্ণ | ✅ | ওয়ার্কস্পেস + চ্যানেল সনাক্তকরণ |
| 🌐 **Webchat** | ✅ সম্পূর্ণ | ✅ | বিল্ট-ইন ওয়েব UI সেশন |
| 📡 **IRC** | ✅ সম্পূর্ণ | ✅ | টার্মিনাল-স্টাইল বাবল UI |
| 🍏 **BlueBubbles** | ✅ সম্পূর্ণ | ✅ | BlueBubbles REST API এর মাধ্যমে iMessage |
| 🔵 **Google Chat** | ✅ সম্পূর্ণ | ✅ | Chat API ওয়েবহুকের মাধ্যমে |
| 🟣 **MS Teams** | ✅ সম্পূর্ণ | ✅ | Teams বট প্লাগইনের মাধ্যমে |
| 🔷 **Mattermost** | ✅ সম্পূর্ণ | ✅ | সেলফ-হোস্টেড টিম চ্যাট |
| 🟩 **Matrix** | ✅ সম্পূর্ণ | ✅ | বিকেন্দ্রীভূত, E2EE সমর্থন |
| 🟢 **LINE** | ✅ সম্পূর্ণ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ সম্পূর্ণ | ✅ | বিকেন্দ্রীভূত NIP-04 DM |
| 🟣 **Twitch** | ✅ সম্পূর্ণ | ✅ | IRC সংযোগের মাধ্যমে চ্যাট |
| 🔷 **Feishu/Lark** | ✅ সম্পূর্ণ | ✅ | WebSocket ইভেন্ট সাবস্ক্রিপশন |
| 🔵 **Zalo** | ✅ সম্পূর্ণ | ✅ | Zalo Bot API |

> **স্বয়ংক্রিয় সনাক্তকরণ:** ClawMetry আপনার `~/.openclaw/openclaw.json` পড়ে এবং শুধুমাত্র আপনি প্রকৃতপক্ষে কনফিগার করা চ্যানেলগুলো রেন্ডার করে। কোনো ম্যানুয়াল সেটআপের দরকার নেই।

## Docker ডিপ্লয়মেন্ট

কন্টেইনারে ClawMetry চালাতে চান? কোনো সমস্যা নেই! 🐳

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

> **নোট:** Docker-এ চালানোর সময়, আপনার এজেন্টের ডেটা + লগ ডিরেক্টরি (যেমন `~/.openclaw`, `~/.claude`, `~/.codex`) মাউন্ট করুন যাতে ClawMetry আপনার সেটআপ স্বয়ংক্রিয়ভাবে সনাক্ত করতে পারে।

## প্রয়োজনীয়তা

- Python 3.8+
- Flask (pip এর মাধ্যমে স্বয়ংক্রিয়ভাবে ইনস্টল হয়)
- একই মেশিনে একটি AI এজেন্ট রানটাইম: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, অথবা n8n (অথবা Docker-এর জন্য মাউন্ট করা ভলিউম)
- Linux অথবা macOS

## NemoClaw / OpenShell সমর্থন

ClawMetry স্বয়ংক্রিয়ভাবে [NemoClaw](https://github.com/NVIDIA/NemoClaw) সনাক্ত করে — NVIDIA-এর এন্টারপ্রাইজ সিকিউরিটি র‍্যাপার যা স্যান্ডবক্সড OpenShell কন্টেইনারের ভেতরে এজেন্ট চালায় OpenClaw-এর জন্য।

বেশিরভাগ ক্ষেত্রে অতিরিক্ত কোনো কনফিগারেশনের দরকার নেই। সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে সেশন ফাইল আবিষ্কার করে সেগুলো হোস্টের `~/.openclaw/`-এ থাকুক অথবা একটি OpenShell কন্টেইনারের ভেতরে থাকুক।

### কীভাবে এটি কাজ করে

ClawMetry দুটি উপায়ে NemoClaw সনাক্ত করে:

1. **বাইনারি সনাক্তকরণ** — `nemoclaw` CLI চেক করে এবং স্যান্ডবক্স তথ্য পেতে `nemoclaw status` চালায়
2. **কন্টেইনার সনাক্তকরণ** — `openshell`, `nemoclaw`, অথবা `ghcr.io/nvidia/` ইমেজের জন্য চলমান Docker কন্টেইনার স্ক্যান করে, তারপর ভলিউম মাউন্ট অথবা `docker cp` এর মাধ্যমে সেশন পড়ে

NemoClaw কন্টেইনার থেকে সিঙ্ক করা সেশন ফাইলগুলো ক্লাউড ড্যাশবোর্ডে `runtime=nemoclaw` এবং `container_id` মেটাডেটা দিয়ে ট্যাগ করা হয়, যাতে আপনি এক নজরে সেগুলোকে স্ট্যান্ডার্ড OpenClaw সেশন থেকে আলাদা করতে পারেন।

### প্রস্তাবিত সেটআপ: HOST-এ সিঙ্ক ডেমন

সেরা অভিজ্ঞতার জন্য, ClawMetry-এর সিঙ্ক ডেমন **হোস্ট মেশিনে** চালান (স্যান্ডবক্সের ভেতরে নয়)। এটি NemoClaw নেটওয়ার্ক পলিসি সীমাবদ্ধতা এড়ায়।

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

আপনাকে যদি সিঙ্ক ডেমন OpenShell স্যান্ডবক্সের **ভেতরে** চালাতেই হয়, তাহলে ClawMetry ingest API-তে পৌঁছাতে পারার জন্য আপনার NemoClaw নেটওয়ার্ক পলিসিতে এই এগ্রেস নিয়মটি যোগ করুন:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

দিয়ে প্রয়োগ করুন:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### পোর্ট এবং এন্ডপয়েন্ট

| এন্ডপয়েন্ট | পোর্ট | প্রোটোকল | প্রয়োজনীয় |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | হ্যাঁ (সিঙ্ক ডেমন → ক্লাউড) |
| `localhost:8900` | 8900 | HTTP | হ্যাঁ (লোকাল ড্যাশবোর্ড UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | কন্টেইনার সেশন আবিষ্কারের জন্য |

সিঙ্ক ডেমন শুধুমাত্র `ingest.clawmetry.com`-এ আউটবাউন্ড HTTPS কল করে। কোনো ইনবাউন্ড পোর্টের দরকার নেই।

---

## ক্লাউড ডিপ্লয়মেন্ট

SSH টানেল, রিভার্স প্রক্সি এবং Docker-এর জন্য **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** দেখুন।

## টেস্টিং

এই প্রজেক্টটি BrowserStack দিয়ে টেস্ট করা হয়।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## টেলিমেট্রি

ClawMetry `https://app.clawmetry.com/api/install`-এ বেনামী
ইনস্টল-লাইফসাইকেল পিং পাঠায়: একটি নতুন মেশিনে প্রথমবার `clawmetry`
CLI চালানোর সময় একটি `install` পিং, একটি নতুন ভার্সনে আপগ্রেড করার পর
প্রথম রানে একটি `update` পিং, এবং ড্যাশবোর্ডের ভেতরে অনবোর্ডিং চয়েস
সম্পন্ন করলে একটি `onboarded` পিং। আমরা এটি প্রকৃত ইনস্টল গণনা করতে ব্যবহার
করি (কাঁচা PyPI ডাউনলোড সংখ্যার ~৯৮% মিরর, CI, এবং অটো-আপডেট
পুনঃডাউনলোড) এবং জানতে যে কোন এজেন্ট ফ্রেমওয়ার্ক এবং ভার্সনগুলো
প্রকৃতপক্ষে ব্যবহৃত হচ্ছে।

**প্রতি লাইফসাইকেল ইভেন্টে প্রতি ভার্সনে সর্বাধিক একটি POST**, যাতে থাকে:

| ফিল্ড | উদাহরণ | কেন |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-এ সংরক্ষিত এলোমেলো UUID | ডিডুপ; আপনি স্পষ্টভাবে Cloud sync কানেক্ট না করা পর্যন্ত বেনামী (তখন প্রমাণীকৃত ডেমন হার্টবিট এটি বহন করে, এই ইনস্টলকে আপনার অ্যাকাউন্টের সাথে লিঙ্ক করে) |
| `event` | `install` / `update` / `onboarded` | নতুন ইনস্টল নাকি বিদ্যমান একটির আপগ্রেড |
| `version` | `0.12.167` | কোন ভার্সনগুলো ব্যবহৃত হচ্ছে |
| `os` / `os_version` | `Darwin` / `25.3.0` | প্ল্যাটফর্ম সমর্থন অগ্রাধিকার |
| `python` | `3.11.15` | Python ভার্সন সমর্থন ম্যাট্রিক্স |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | পরবর্তীতে আমাদের কোন এজেন্টের সাথে ইন্টিগ্রেট করা উচিত |
| `is_ci` / `ci_provider` | `true` / `github_actions` | মানুষের ইনস্টলকে CI নয়েজ থেকে আলাদা করা |

**আমরা যা পাঠাই না**: IP (ক্লাউড সার্ভার-সাইডে রিকোয়েস্ট থেকে
দেশের কোড বের করে, তারপর IP বাতিল করে দেয়), হোস্টনেম, ইউজারনেম,
ওয়ার্কস্পেস পাথ, ফাইল কন্টেন্ট, আপনার api_key, আপনার ইমেইল, PII অথবা
ওয়ার্কস্পেস-নির্দিষ্ট কিছুই না। ওয়্যার পেলোডটি
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-এ যাচাইযোগ্য।

**অপ্ট আউট করুন** (এর যেকোনো একটি এটি স্থায়ীভাবে নিষ্ক্রিয় করে দেয়):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

নেটওয়ার্ক ব্যর্থতা এখানে কখনো `clawmetry`-কে চলা থেকে ব্লক করে না — পিংটি
একটি ডেমন থ্রেডে ৩ সেকেন্ড টাইমআউট সহ ফায়ার-অ্যান্ড-ফরগেট।

## স্টার হিস্ট্রি

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
  <strong>🦞 আপনার এজেন্টকে ভাবতে দেখুন</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> দ্বারা নির্মিত · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ইকোসিস্টেমের অংশ</sub>
</p>
