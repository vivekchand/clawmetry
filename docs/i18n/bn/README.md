<!-- i18n-src:0e34918f8f2e -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টকে ভাবতে দেখুন।** **১৪টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজারভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ১০টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি মাত্র ড্যাশবোর্ড।

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। জিরো কনফিগ। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে এবং আপনার কাজ শেষ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ১৪টি এজেন্ট রানটাইমের সাথে কাজ করে

ClawMetry শুরু হয়েছিল OpenClaw-এর জন্য অবজারভেবিলিটি হিসেবে, এখন এটি একটি মাত্র ড্যাশবোর্ডে আপনার **পুরো এজেন্ট ফ্লিট** পরিমাপ করে, আপনার মেশিনে প্রতিটি রানটাইম স্বয়ংক্রিয়ভাবে শনাক্ত করে:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw এবং NemoClaw ওপেন-সোর্স অ্যাপে ফ্রি; অন্যান্য রানটাইমগুলো ClawMetry Cloud বা সেল্ফ-হোস্টেড Pro লাইসেন্সের মাধ্যমে সক্রিয় হয়। হেডার থেকে রানটাইম পরিবর্তন করুন এবং প্রতিটি ট্যাব—কস্ট, টোকেন, টুলস, ট্রেসেস—সেই রানটাইমের জন্য পুনরায় স্কোপ হয়ে যায়। সঠিক ফ্রি/পেইড বিভাজন, টিয়ার ম্যাট্রিক্স, `/api/entitlement` শেপ, এবং `clawmetry license` CLI-র জন্য **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** দেখুন।

## আপনি যা পাবেন

- **Flow** — চ্যানেল, ব্রেইন, টুলস এবং ফিরতি পথ দিয়ে বার্তা প্রবাহিত হওয়ার লাইভ অ্যানিমেটেড ডায়াগ্রাম
- **Overview** — হেলথ চেক, অ্যাক্টিভিটি হিটম্যাপ, সেশন কাউন্ট, মডেল তথ্য
- **Usage** — দৈনিক/সাপ্তাহিক/মাসিক ব্রেকডাউনসহ টোকেন এবং কস্ট ট্র্যাকিং
- **Sessions** — মডেল, টোকেন, শেষ অ্যাক্টিভিটিসহ সক্রিয় এজেন্ট সেশন
- **Crons** — স্ট্যাটাস, পরবর্তী রান, সময়কালসহ শিডিউলড জব
- **Logs** — কালার-কোডেড রিয়েল-টাইম লগ স্ট্রিমিং
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, দৈনিক নোট ব্রাউজ করুন
- **Transcripts** — সেশন হিস্ট্রি পড়ার জন্য চ্যাট-বাবল UI
- **Alerts** — বাজেট ক্যাপ, এরর-রেট ট্রিগার, এজেন্ট-অফলাইন শনাক্তকরণ; Slack, Discord, PagerDuty, Telegram, Email-এ রুট করে
- **Approvals** — ডেসট্রাক্টিভ ডিলিট, ফোর্স পুশ, DB মিউটেশন, sudo, প্যাকেজ ইনস্টল, নেটওয়ার্ক কল এক-ক্লিক সাইন-অফের পেছনে গেট করুন

## স্ক্রিনশট

### 🧠 Brain — লাইভ এজেন্ট ইভেন্ট স্ট্রিম
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — টোকেন ব্যবহার ও সেশন সারাংশ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — রিয়েল-টাইম টুল কল ফিড
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — মডেল ও সেশন অনুযায়ী কস্ট ব্রেকডাউন
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ওয়ার্কস্পেস ফাইল ব্রাউজার
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — পশ্চার ও অডিট লগ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — বাজেট ক্যাপ, এরর-রেট ট্রিগার, Slack / Discord / PagerDuty / Email-এ ওয়েবহুক
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ম্যানুয়াল সাইন-অফের পেছনে ঝুঁকিপূর্ণ টুল কল গেট করুন; পলিসি-ব্যাকড প্রোটেকশন রুল
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-এর জন্য প্রি-এক্সিকিউশন ব্লকিং** — একটি কমান্ড একটি
PreToolUse হুক ইনস্টল করে যা ম্যাচিং টুল কলগুলোকে সেগুলো চালানোর *আগে* থামিয়ে দেয় এবং আপনার সিদ্ধান্তের জন্য অপেক্ষা করে
([ক্লাউড পুশ নোটিফিকেশন](https://app.clawmetry.com/push) সক্রিয় থাকলে আপনার ফোন থেকে এক ট্যাপে):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

একটি ডিনাই শুধু সেই একটি টুল কলকেই ব্লক করে — এজেন্ট তার সেশন ধরে রাখে এবং
অন্য উপায় চেষ্টা করতে পারে। আপনার ফোনে অ্যাপ্রুভ করা Claude Code-এর নিজস্ব
পারমিশন প্রম্পট স্কিপ করে দেয় (আপনি ইতিমধ্যে উত্তর দিয়েছেন)। ম্যাচ না হওয়া টুলগুলোর
খরচ ~৪০ms এবং সেগুলো Claude Code-এর স্বাভাবিক পারমিশন ফ্লোতে চলে যায়। এছাড়াও
Claude Code নিজেই আপনার জন্য অপেক্ষা করলে আপনি ফোনে পুশ পাবেন (`permission_prompt` /
`idle_prompt` নোটিফিকেশন)।

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

v2 React অ্যাপটি `frontend/`-এ থাকে এবং v2 সক্রিয় থাকলে Flask
সার্ভার শুরু হওয়ার সময় `/v2`-এ সার্ভ করা হয়।

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
`http://localhost:8900`-এ প্রক্সি করে, তাই React অ্যাপ অতিরিক্ত CORS সেটআপ ছাড়াই
লোকাল Flask সার্ভারের সাথে কথা বলতে পারে।

Python প্যাকেজের সাথে শিপ হওয়া বান্ডেল তৈরি করতে:

```bash
cd frontend
npm run build
```

প্রোডাকশন বান্ডেল `clawmetry/static/v2/dist/`-এ লেখা হয়।

## রানটাইম / এজেন্ট সামঞ্জস্যতা

ClawMetry শুধু OpenClaw নয়, আরও অনেক AI-এজেন্ট রানটাইম পর্যবেক্ষণ করে। প্রতিটি নন-OpenClaw রানটাইম একটি ডেডিকেটেড রিডার অ্যাডাপ্টার শিপ করে যা তার নেটিভ সেশন ফরম্যাটকে ClawMetry-এর ইউনিফাইড শেপে রূপান্তরিত করে; ডেমন সেগুলোকে একই DuckDB স্টোর + ক্লাউড স্ন্যাপশটে ইনজেস্ট করে, রানটাইম দিয়ে ট্যাগ করে, এবং Session replay ট্যাব একাধিক রানটাইম থাকলে একটি **রানটাইম সুইচার** দেখায়। সম্পূর্ণ ম্যাট্রিক্স + রানটাইম যোগ করার গাইডের জন্য [`docs/compatibility.md`](docs/compatibility.md) এবং OpenClaw-family প্রাইমারের জন্য [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) দেখুন।

[Perplexity-এর numbat](https://github.com/perplexityai/numbat) এজেন্ট-সিকিউরিটি টুল চালাচ্ছেন? ClawMetry এর ফাইন্ডিংস এবং এনফোর্সমেন্ট সিদ্ধান্তগুলো সরাসরি ইনজেস্ট করে—দেখুন [`docs/NUMBAT.md`](docs/NUMBAT.md)।

| রানটাইম / এজেন্ট | স্ট্যাটাস | নোট |
|---|---|---|
| **OpenClaw** | নেটিভ | রেফারেন্স রানটাইম, স্বয়ংক্রিয়ভাবে শনাক্ত |
| **PicoClaw** | বেটা অ্যাডাপ্টার | ফ্ল্যাট `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ট্রান্সক্রিপ্ট, মডেল, টুল কল। |
| **NanoClaw** | বেটা অ্যাডাপ্টার | প্রতি-সেশন SQLite (`data/v2-sessions`)। ট্রান্সক্রিপ্ট + মেসেজ কাউন্ট। |
| **Hermes** | বেটা অ্যাডাপ্টার | SQLite `~/.hermes/state.db`। ট্রান্সক্রিপ্ট, মডেল, টোকেন/কস্ট। |
| **Claude Code** | বেটা অ্যাডাপ্টার | JSONL `~/.claude/projects/.../<id>.jsonl`। ট্রান্সক্রিপ্ট, মডেল, টুল কল + থিংকিং, টোকেন ব্যবহার। |
| **Codex** | বেটা অ্যাডাপ্টার | রোলআউট JSONL `~/.codex/sessions/...`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Cursor** | বেটা অ্যাডাপ্টার | SQLite `state.vscdb`। চ্যাট/কম্পোজার ট্রান্সক্রিপ্ট, মডেল। |
| **Aider** | বেটা অ্যাডাপ্টার | প্রতি প্রজেক্টে `.aider.chat.history.md`। ট্রান্সক্রিপ্ট, মডেল, টোকেন কাউন্ট। |
| **Goose** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/goose`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন টোটাল। |
| **opencode** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/opencode`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + কস্ট। |
| **Qwen Code** | বেটা অ্যাডাপ্টার | JSONL `~/.qwen/projects/.../chats`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Pi** | বেটা অ্যাডাপ্টার | JSONL `~/.pi/agent/sessions`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + কস্ট। |
| **Deep Agents** | বেটা অ্যাডাপ্টার | SQLite `~/.deepagents/.state/sessions.db`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + কস্ট। |
| **n8n** | বেটা অ্যাডাপ্টার | SQLite `~/.n8n/database.sqlite`। ওয়ার্কফ্লো এক্সিকিউশন, নোড রান, AI Agent প্রম্পট, n8n যেখানে রেকর্ড করে সেখানে মডেল + টোকেন। |
| **Antigravity** | বেটা অ্যাডাপ্টার | `~/.gemini/<flavor>/brain/`-এর অধীনে ব্রেইন JSONL। কনভারসেশন, টুল স্টেপ, থিংকিং, প্রতি-জেনারেশন Gemini টোকেন বিভাজন + কস্ট, ব্যাকগ্রাউন্ড-জেনারেশন বার্ন। |
| **GitHub Copilot** | বেটা অ্যাডাপ্টার | `~/.copilot/session-state/`-এর অধীনে Copilot CLI `events.jsonl` + প্রতি-কল ব্যবহার লেজার `session-store.db`। কনভারসেশন, টুল কল, মডেল রাউটিং, ক্যাশ-অ্যাওয়্যার টোকেন বিভাজন, ভেন্ডর-বিলড AI-ক্রেডিট কস্ট। |

"বেটা অ্যাডাপ্টার" মানে ClawMetry সেই রানটাইমের প্রকৃত অন-ডিস্ক ফরম্যাটের জন্য একটি রিডার শিপ করে, প্রতিটি একটি বাস্তব মেশিনে একটি বাস্তব ইনস্টলের বিরুদ্ধে তৈরি + যাচাই করা হয়েছে (দেখুন `tests/fixtures/runtimes/<rt>/`)। অ্যাডাপ্টারগুলো রিড-অনলি; প্রতিটি সৎভাবে জানায় তার রানটাইম প্রকৃতপক্ষে কী স্টোর করে (যেমন, PicoClaw/NanoClaw/Cursor ডিস্কে টোকেন কস্ট লেখে না)। একটি নোডে একাধিক রানটাইম চললে, রানটাইম সুইচার পরিষ্কার ডিপ-ডাইভের জন্য সেশন ভিউকে একটির জন্য স্কোপ করে।

## যেকোনো SDK এজেন্ট ট্র্যাক করুন — আউট-লুপ কস্ট অ্যাট্রিবিউশন

উপরের রানটাইমগুলো সবই ডিস্কে সেশন লেখে। আপনার নিজস্ব **প্রোডাকশন এজেন্ট**—যেটি আপনি OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, বা একটি প্লেইন `httpx` লুপে তৈরি করেছেন—তা করে না। ClawMetry-এর জিরো-কনফিগ ইন্টারসেপ্টর তবুও `httpx`/`requests` মাংকি-প্যাচিং করে তার LLM কলগুলো (কস্ট, টোকেন, লেটেন্সি, এরর) ক্যাপচার করে:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (অথবা `CLAWMETRY_SOURCE=support-agent` এনভায়রনমেন্ট ভেরিয়েবল) প্রতিটি কলকে একটি **নামযুক্ত সোর্স** দিয়ে ট্যাগ করে, তাই আপনার চালানো প্রতিটি প্রোডাক্ট ড্যাশবোর্ডের Overview-এর **🔌 Out-loop sources** কার্ডে নিজস্ব ফার্স্ট-ক্লাস, কস্ট-অ্যাট্রিবিউটেবল লাইন হিসেবে দেখা যায়—প্রতি এজেন্টে কল, প্রোভাইডার, লেটেন্সি, এরর রেট। কোনো সোর্স সেট করা না থাকলে? কলগুলো তবুও ট্র্যাক হয়; কার্ডটি শুধু লুকানো থাকে।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

এটি একই ডেটা লেয়ার যা রানটাইম অ্যাডাপ্টারগুলো ফিড করে (DuckDB → ক্লাউড স্ন্যাপশট), তাই আউট-লুপ সোর্সগুলো বাকি সবকিছুর মতো একইভাবে ক্লাউড ড্যাশবোর্ডে সিঙ্ক হয়, E2E-এনক্রিপ্টেড।

## OpenTelemetry — ভেন্ডর-নিউট্রাল, আপনার ট্রেস যেকোনো জায়গায় পাঠান

ClawMetry উভয় দিকেই **OpenTelemetry** বলে, **GenAI সিমান্টিক কনভেনশন** ব্যবহার করে, তাই আপনার এজেন্ট ট্রেসগুলো কখনো একটি টুলে লক-ইন হয় না।

প্রতিটি সেশন—LLM কল, টুল, সাব-এজেন্ট, টোকেন, কস্ট—OTLP/HTTP GenAI স্প্যান হিসেবে যেকোনো কালেক্টরে (Datadog, Grafana, Honeycomb, বা আপনার নিজস্ব OTel Collector) **এক্সপোর্ট** করুন:

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

**ইনজেস্ট** — বিল্ট-ইন OTLP রিসিভার `/v1/traces` এবং `/v1/metrics`-এ অন্য যেকোনো কিছু থেকে ট্রেস এবং মেট্রিক্স গ্রহণ করে (প্রোটোবাফ ইনজেস্টের জন্য `pip install clawmetry[otel]`)।

আপনি জিরো-কনফিগ, লোকাল-ফার্স্ট ClawMetry ড্যাশবোর্ড **এবং** আপনার দল ইতিমধ্যে যে ব্যাকএন্ড চালাচ্ছে সেখানে আপনার ডেটা—কোনো লক-ইন নেই, ইনস্টল করার জন্য দ্বিতীয় এজেন্ট নেই।

## কনফিগারেশন

বেশিরভাগ মানুষের কোনো কনফিগ দরকার নেই। ClawMetry আপনার ওয়ার্কস্পেস, লগ, সেশন এবং ক্রন স্বয়ংক্রিয়ভাবে শনাক্ত করে।

কাস্টমাইজ করার প্রয়োজন হলে:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

সব অপশন: `clawmetry --help`

## সমর্থিত চ্যানেল

আপনার কনফিগার করা প্রতিটি OpenClaw চ্যানেলের জন্য ClawMetry লাইভ অ্যাক্টিভিটি দেখায়। শুধু আপনার `openclaw.json`-এ প্রকৃতপক্ষে সেট আপ করা চ্যানেলগুলো Flow ডায়াগ্রামে দেখা যায়—কনফিগার না করা চ্যানেলগুলো স্বয়ংক্রিয়ভাবে লুকানো থাকে।

Flow-এ যেকোনো চ্যানেল নোডে ক্লিক করে ইনকামিং/আউটগোয়িং মেসেজ কাউন্টসহ একটি লাইভ চ্যাট বাবল ভিউ দেখুন।

| চ্যানেল | স্ট্যাটাস | লাইভ পপআপ | নোট |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ সম্পূর্ণ | ✅ | মেসেজ, স্ট্যাটস, ১০ সেকেন্ড রিফ্রেশ |
| 💬 **iMessage** | ✅ সম্পূর্ণ | ✅ | সরাসরি `~/Library/Messages/chat.db` পড়ে |
| 💚 **WhatsApp** | ✅ সম্পূর্ণ | ✅ | WhatsApp Web (Baileys) এর মাধ্যমে |
| 🔵 **Signal** | ✅ সম্পূর্ণ | ✅ | signal-cli এর মাধ্যমে |
| 🟣 **Discord** | ✅ সম্পূর্ণ | ✅ | গিল্ড + চ্যানেল শনাক্তকরণ |
| 🟪 **Slack** | ✅ সম্পূর্ণ | ✅ | ওয়ার্কস্পেস + চ্যানেল শনাক্তকরণ |
| 🌐 **Webchat** | ✅ সম্পূর্ণ | ✅ | বিল্ট-ইন ওয়েব UI সেশন |
| 📡 **IRC** | ✅ সম্পূর্ণ | ✅ | টার্মিনাল-স্টাইল বাবল UI |
| 🍏 **BlueBubbles** | ✅ সম্পূর্ণ | ✅ | BlueBubbles REST API এর মাধ্যমে iMessage |
| 🔵 **Google Chat** | ✅ সম্পূর্ণ | ✅ | Chat API ওয়েবহুকের মাধ্যমে |
| 🟣 **MS Teams** | ✅ সম্পূর্ণ | ✅ | Teams বট প্লাগইনের মাধ্যমে |
| 🔷 **Mattermost** | ✅ সম্পূর্ণ | ✅ | সেল্ফ-হোস্টেড টিম চ্যাট |
| 🟩 **Matrix** | ✅ সম্পূর্ণ | ✅ | ডিসেন্ট্রালাইজড, E2EE সমর্থন |
| 🟢 **LINE** | ✅ সম্পূর্ণ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ সম্পূর্ণ | ✅ | ডিসেন্ট্রালাইজড NIP-04 DM |
| 🟣 **Twitch** | ✅ সম্পূর্ণ | ✅ | IRC সংযোগের মাধ্যমে চ্যাট |
| 🔷 **Feishu/Lark** | ✅ সম্পূর্ণ | ✅ | WebSocket ইভেন্ট সাবস্ক্রিপশন |
| 🔵 **Zalo** | ✅ সম্পূর্ণ | ✅ | Zalo Bot API |

> **স্বয়ংক্রিয় শনাক্তকরণ:** ClawMetry আপনার `~/.openclaw/openclaw.json` পড়ে এবং শুধু আপনি প্রকৃতপক্ষে কনফিগার করা চ্যানেলগুলো রেন্ডার করে। কোনো ম্যানুয়াল সেটআপের প্রয়োজন নেই।

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

> **নোট:** Docker-এ চালানোর সময়, আপনার এজেন্টের ডেটা + লগ ডিরেক্টরি (যেমন `~/.openclaw`, `~/.claude`, `~/.codex`) মাউন্ট করুন যাতে ClawMetry আপনার সেটআপ স্বয়ংক্রিয়ভাবে শনাক্ত করতে পারে।

## প্রয়োজনীয়তা

- Python 3.8+
- Flask (pip এর মাধ্যমে স্বয়ংক্রিয়ভাবে ইনস্টল হয়)
- একই মেশিনে একটি AI এজেন্ট রানটাইম: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, বা GitHub Copilot (বা Docker-এর জন্য মাউন্ট করা ভলিউম)
- Linux বা macOS

## NemoClaw / OpenShell সমর্থন

ClawMetry স্বয়ংক্রিয়ভাবে [NemoClaw](https://github.com/NVIDIA/NemoClaw) শনাক্ত করে — NVIDIA-এর এন্টারপ্রাইজ সিকিউরিটি র‍্যাপার যা স্যান্ডবক্সড OpenShell কন্টেইনারের ভেতরে OpenClaw এজেন্ট চালায়।

বেশিরভাগ ক্ষেত্রে অতিরিক্ত কনফিগারেশনের প্রয়োজন নেই। সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে সেশন ফাইল আবিষ্কার করে, সেগুলো হোস্টে `~/.openclaw/`-এ থাকুক বা OpenShell কন্টেইনারের ভেতরে থাকুক।

### এটি কীভাবে কাজ করে

ClawMetry দুটি উপায়ে NemoClaw শনাক্ত করে:

1. **বাইনারি শনাক্তকরণ** — `nemoclaw` CLI চেক করে এবং স্যান্ডবক্স তথ্য পেতে `nemoclaw status` চালায়
2. **কন্টেইনার শনাক্তকরণ** — চলমান Docker কন্টেইনারগুলো `openshell`, `nemoclaw`, বা `ghcr.io/nvidia/` ইমেজের জন্য স্ক্যান করে, তারপর ভলিউম মাউন্ট বা `docker cp` এর মাধ্যমে সেশন পড়ে

NemoClaw কন্টেইনার থেকে সিঙ্ক করা সেশন ফাইলগুলো ক্লাউড ড্যাশবোর্ডে `runtime=nemoclaw` এবং `container_id` মেটাডেটা দিয়ে ট্যাগ করা হয়, তাই আপনি এক নজরে সেগুলোকে স্ট্যান্ডার্ড OpenClaw সেশন থেকে আলাদা করতে পারবেন।

### প্রস্তাবিত সেটআপ: হোস্টে সিঙ্ক ডেমন

সেরা অভিজ্ঞতার জন্য, **হোস্ট মেশিনে** (স্যান্ডবক্সের ভেতরে নয়) ClawMetry-এর সিঙ্ক ডেমন চালান। এটি NemoClaw নেটওয়ার্ক পলিসি বিধিনিষেধ এড়িয়ে যায়।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে যেকোনো চলমান OpenShell কন্টেইনারের ভেতরে সেশন খুঁজে পাবে।

### ঐচ্ছিক: স্পষ্ট স্যান্ডবক্স নাম

স্বয়ংক্রিয় শনাক্তকরণ কাজ না করলে, ClawMetry-কে সঠিক স্যান্ডবক্সের দিকে নির্দেশ করুন:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### স্যান্ডবক্সের ভেতরে চালানো (উন্নত)

আপনাকে যদি অবশ্যই OpenShell স্যান্ডবক্সের **ভেতরে** সিঙ্ক ডেমন চালাতে হয়, তাহলে ClawMetry ইনজেস্ট API-তে পৌঁছাতে পারার জন্য আপনার NemoClaw নেটওয়ার্ক পলিসিতে এই এগ্রেস রুল যোগ করুন:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

এভাবে প্রয়োগ করুন:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### পোর্ট এবং এন্ডপয়েন্ট

| এন্ডপয়েন্ট | পোর্ট | প্রোটোকল | প্রয়োজনীয় |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | হ্যাঁ (সিঙ্ক ডেমন → ক্লাউড) |
| `localhost:8900` | 8900 | HTTP | হ্যাঁ (লোকাল ড্যাশবোর্ড UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | কন্টেইনার সেশন আবিষ্কারের জন্য |

সিঙ্ক ডেমন শুধু `ingest.clawmetry.com`-এ আউটবাউন্ড HTTPS কল করে। কোনো ইনবাউন্ড পোর্টের প্রয়োজন নেই।

---

## ক্লাউড ডিপ্লয়মেন্ট

SSH টানেল, রিভার্স প্রক্সি এবং Docker-এর জন্য **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** দেখুন।

## টেস্টিং

এই প্রজেক্টটি BrowserStack দিয়ে টেস্ট করা হয়েছে।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## টেলিমেট্রি

ClawMetry `https://app.clawmetry.com/api/install`-এ অজ্ঞাত ইনস্টল-লাইফসাইকেল
পিং পাঠায়: নতুন মেশিনে প্রথমবার `clawmetry` CLI চালানোর সময় একটি `install`
পিং, নতুন ভার্সনে আপগ্রেড করার পরে প্রথম রানে একটি `update` পিং, এবং
ড্যাশবোর্ডের ভেতরে অনবোর্ডিং পছন্দ সম্পূর্ণ করার সময় একটি `onboarded`
পিং। আমরা এটি প্রকৃত ইনস্টল গণনা করতে ব্যবহার করি (কাঁচা PyPI ডাউনলোড
সংখ্যা ~৯৮% মিরর, CI, এবং অটো-আপডেট পুনরায়-ডাউনলোড) এবং কোন এজেন্ট
ফ্রেমওয়ার্ক এবং ভার্সন আসলে ব্যবহারে আছে তা জানতে।

**প্রতি ভার্সনে প্রতি লাইফসাইকেল ইভেন্টে সর্বোচ্চ একটি POST**, যাতে রয়েছে:

| ফিল্ড | উদাহরণ | কেন |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-এ সংরক্ষিত র‍্যান্ডম UUID | ডিডুপ; ক্লাউড সিঙ্ক স্পষ্টভাবে কানেক্ট না করা পর্যন্ত অজ্ঞাত (এরপর অথেন্টিকেটেড ডেমন হার্টবিট এটি বহন করে, এই ইনস্টলটিকে আপনার অ্যাকাউন্টের সাথে লিঙ্ক করে) |
| `event` | `install` / `update` / `onboarded` | নতুন ইনস্টল বনাম বিদ্যমান একটির আপগ্রেড |
| `version` | `0.12.167` | কোন ভার্সন ব্যবহারে আছে |
| `os` / `os_version` | `Darwin` / `25.3.0` | প্ল্যাটফর্ম সমর্থন অগ্রাধিকার |
| `python` | `3.11.15` | Python ভার্সন সমর্থন ম্যাট্রিক্স |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | পরবর্তীতে আমাদের কোন এজেন্টের সাথে ইন্টিগ্রেট করা উচিত |
| `is_ci` / `ci_provider` | `true` / `github_actions` | মানুষের ইনস্টলকে CI নয়েজ থেকে আলাদা করা |

**আমরা যা পাঠাই না**: IP (ক্লাউড রিকোয়েস্ট থেকে সার্ভার-সাইডে
দেশের কোড বের করে, তারপর IP বাতিল করে), হোস্টনেম, ইউজারনেম, ওয়ার্কস্পেস
পাথ, ফাইল কন্টেন্ট, আপনার api_key, আপনার ইমেইল, PII বা
ওয়ার্কস্পেস-নির্দিষ্ট কিছু। ওয়্যার পেলোড
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-এ অডিট করা যায়।

**অপ্ট আউট** (এর যেকোনো একটি এটি স্থায়ীভাবে নিষ্ক্রিয় করে):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

এখানে একটি নেটওয়ার্ক ব্যর্থতা কখনো `clawmetry` চালানো ব্লক করে না — পিংটি
৩ সেকেন্ড টাইমআউটসহ একটি ডেমন থ্রেডে ফায়ার-অ্যান্ড-ফরগেট।

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
  <sub>তৈরি করেছেন <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ইকোসিস্টেমের অংশ</sub>
</p>
