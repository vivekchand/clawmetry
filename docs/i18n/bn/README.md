<!-- i18n-src:c422fb7dd0da -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টকে ভাবতে দেখুন।** **২০টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজার্ভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ১৬টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এই ভাষায় পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। কোনো কনফিগারেশন লাগে না। সবকিছু নিজে থেকেই শনাক্ত করে নেয়।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ঠিকানায় খুলে যায় এবং কাজ শেষ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ২০টি এজেন্ট রানটাইমের সাথে কাজ করে

ClawMetry শুরু হয়েছিল OpenClaw-এর জন্য অবজার্ভেবিলিটি হিসেবে, আর এখন এটি আপনার **পুরো এজেন্ট ফ্লিটকে** একটি ড্যাশবোর্ডেই পরিমাপ করে, আপনার মেশিনে থাকা প্রতিটি রানটাইম স্বয়ংক্রিয়ভাবে শনাক্ত করে:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw এবং NemoClaw ওপেন-সোর্স অ্যাপে বিনামূল্যে; বাকি রানটাইমগুলো চালু হয় ClawMetry Cloud বা সেলফ-হোস্টেড Pro লাইসেন্সের মাধ্যমে। হেডার থেকে রানটাইম পাল্টান, আর প্রতিটি ট্যাব — খরচ, টোকেন, টুল, ট্রেস — সেই রানটাইমের সাথে সামঞ্জস্য রেখে নতুন করে দেখাবে। সঠিক ফ্রি/পেইড বিভাজন, টিয়ার ম্যাট্রিক্স, `/api/entitlement` শেপ এবং `clawmetry license` CLI-এর জন্য দেখুন **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**।

## আপনি যা পাবেন

- **Flow** — চ্যানেল, ব্রেইন, টুল এবং ফিরতি পথ দিয়ে মেসেজ কীভাবে প্রবাহিত হচ্ছে তা দেখানো লাইভ অ্যানিমেটেড ডায়াগ্রাম
- **Overview** — হেলথ চেক, অ্যাক্টিভিটি হিটম্যাপ, সেশন সংখ্যা, মডেল তথ্য
- **Usage** — দৈনিক/সাপ্তাহিক/মাসিক বিভাজনসহ টোকেন এবং খরচ ট্র্যাকিং
- **Sessions** — মডেল, টোকেন, শেষ কার্যকলাপসহ সক্রিয় এজেন্ট সেশন
- **Crons** — স্ট্যাটাস, পরবর্তী রান, সময়কালসহ শিডিউল করা জব
- **Logs** — কালার-কোডেড রিয়েল-টাইম লগ স্ট্রিমিং
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, দৈনিক নোট ব্রাউজ করুন
- **Transcripts** — সেশন হিস্ট্রি পড়ার জন্য চ্যাট-বাবল UI
- **Alerts** — বাজেট ক্যাপ, এরর-রেট ট্রিগার, এজেন্ট-অফলাইন শনাক্তকরণ; Slack, Discord, PagerDuty, Telegram, Email-এ পাঠানো হয়
- **Approvals** — ধ্বংসাত্মক ডিলিট, ফোর্স পুশ, DB মিউটেশন, sudo, প্যাকেজ ইনস্টল, নেটওয়ার্ক কল এক-ক্লিক অনুমোদনের পেছনে আটকে রাখুন

## স্ক্রিনশট

### 🧠 Brain — লাইভ এজেন্ট ইভেন্ট স্ট্রিম
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — টোকেন ব্যবহার ও সেশন সারাংশ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — রিয়েল-টাইম টুল কল ফিড
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — মডেল ও সেশন অনুযায়ী খরচের বিভাজন
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ওয়ার্কস্পেস ফাইল ব্রাউজার
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — অবস্থান ও অডিট লগ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — বাজেট ক্যাপ, এরর-রেট ট্রিগার, Slack / Discord / PagerDuty / Email-এ ওয়েবহুক
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ঝুঁকিপূর্ণ টুল কল ম্যানুয়াল সাইন-অফের পেছনে আটকে রাখুন; পলিসি-সমর্থিত সুরক্ষা নিয়ম
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-এর জন্য প্রি-এক্সিকিউশন ব্লকিং** — একটি কমান্ড দিয়েই একটি
PreToolUse হুক ইনস্টল হয়ে যায় যা মিলে যাওয়া টুল কলগুলোকে চালানোর *আগেই*
থামিয়ে দেয় এবং আপনার সিদ্ধান্তের জন্য অপেক্ষা করে (ফোন থেকে এক ট্যাপেই,
[ক্লাউড পুশ নোটিফিকেশন](https://app.clawmetry.com/push) চালু থাকলে):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

একটি ডিনাই শুধু সেই একটি টুল কলকেই ব্লক করে — এজেন্ট তার সেশন ধরে রাখতে পারে
এবং অন্য উপায় চেষ্টা করতে পারে। আপনার ফোনে অ্যাপ্রুভ করলে Claude Code-এর নিজস্ব
পারমিশন প্রম্পট এড়িয়ে যায় (আপনি ইতিমধ্যেই উত্তর দিয়েছেন)। মিলে যায়নি এমন টুল
প্রায় ৪০ms খরচ করে এবং Claude Code-এর স্বাভাবিক পারমিশন ফ্লোতে চলে যায়।
Claude Code নিজেই যখন আপনার জন্য অপেক্ষা করে তখনও আপনি ফোনে পুশ পান
(`permission_prompt` / `idle_prompt` নোটিফিকেশন)।

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

v2 React অ্যাপটি `frontend/`-এ থাকে এবং v2 চালু করে ফ্লাস্ক
সার্ভার শুরু করলে `/v2`-এ সার্ভ করা হয়।

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
`http://localhost:8900`-এ প্রক্সি করে দেয়, তাই React অ্যাপ অতিরিক্ত CORS
সেটআপ ছাড়াই লোকাল Flask সার্ভারের সাথে যোগাযোগ করতে পারে।

Python প্যাকেজের সাথে যে বান্ডেলটি শিপ হয় তা বিল্ড করতে:

```bash
cd frontend
npm run build
```

প্রোডাকশন বান্ডেলটি `clawmetry/static/v2/dist/`-এ লেখা হয়।

## রানটাইম / এজেন্ট সামঞ্জস্যতা

ClawMetry শুধু OpenClaw নয়, আরও অনেক AI-এজেন্ট রানটাইম পর্যবেক্ষণ করে। প্রতিটি OpenClaw-ব্যতীত রানটাইম একটি ডেডিকেটেড রিডার অ্যাডাপ্টার নিয়ে আসে যা তার নিজস্ব সেশন ফরম্যাটকে ClawMetry-এর ইউনিফায়েড শেপে রূপান্তর করে; ডেমন সেগুলোকে একই DuckDB স্টোর + ক্লাউড স্ন্যাপশটে ইনজেস্ট করে, রানটাইম দিয়ে ট্যাগ করে, আর Session replay ট্যাবে একাধিক রানটাইম থাকলে একটি **রানটাইম সুইচার** দেখায়। সম্পূর্ণ ম্যাট্রিক্স + রানটাইম যোগ করার গাইডের জন্য দেখুন [`docs/compatibility.md`](docs/compatibility.md), এবং OpenClaw-পরিবার প্রাইমারের জন্য [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)।

[Perplexity-এর numbat](https://github.com/perplexityai/numbat) এজেন্ট-সিকিউরিটি টুল চালাচ্ছেন? ClawMetry এর ফলাফল ও এনফোর্সমেন্ট সিদ্ধান্তগুলো বাক্সের বাইরেই ইনজেস্ট করে নেয় — দেখুন [`docs/NUMBAT.md`](docs/NUMBAT.md)।

| রানটাইম / এজেন্ট | স্ট্যাটাস | নোট |
|---|---|---|
| **OpenClaw** | Native | রেফারেন্স রানটাইম, স্বয়ংক্রিয়ভাবে শনাক্ত হয় |
| **PicoClaw** | Beta adapter | ফ্ল্যাট `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ট্রান্সক্রিপ্ট, মডেল, টুল কল। |
| **NanoClaw** | Beta adapter | প্রতি-সেশন SQLite (`data/v2-sessions`)। ট্রান্সক্রিপ্ট + মেসেজ সংখ্যা। |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`। ট্রান্সক্রিপ্ট, মডেল, টোকেন/খরচ। |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`। ট্রান্সক্রিপ্ট, মডেল, টুল কল + থিংকিং, টোকেন ব্যবহার। |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Cursor** | Beta adapter | SQLite `state.vscdb`। চ্যাট/কম্পোজার ট্রান্সক্রিপ্ট, মডেল। |
| **Aider** | Beta adapter | প্রতি প্রজেক্টে `.aider.chat.history.md`। ট্রান্সক্রিপ্ট, মডেল, টোকেন গণনা। |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, মোট টোকেন। |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`। ওয়ার্কফ্লো এক্সিকিউশন, নোড রান, AI Agent প্রম্পট, n8n যেখানে রেকর্ড করে সেখানে মডেল + টোকেন। |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/`-এর অধীনে Brain JSONL। কথোপকথন, টুল স্টেপ, থিংকিং, প্রতি-জেনারেশন Gemini টোকেন বিভাজন + খরচ, ব্যাকগ্রাউন্ড-জেনারেশন খরচ। |
| **GitHub Copilot** | Beta adapter | `~/.copilot/session-state/`-এর অধীনে Copilot CLI `events.jsonl` + প্রতি-কল ব্যবহারের `session-store.db` লেজার। কথোপকথন, টুল কল, মডেল রাউটিং, ক্যাশ-সচেতন টোকেন বিভাজন, ভেন্ডর-বিলড AI-ক্রেডিট খরচ। |
| **Grok** | Beta adapter | xAI Grok Build CLI (`~/.grok/bin/grok`-এর অধীনে Rust বাইনারি): গ্লোবাল ইভেন্ট লগ `~/.grok/logs/unified.jsonl` + প্রতি-সেশন `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`। কথোপকথন, প্রতি-টার্ন টোকেন বিভাজন, মডেল রাউটিং, এবং CLI-এর বাইরে যাওয়া রিপো পেলোড `~/.grok/upload_queue/`-এ স্টেজড, যাতে আপনার মেশিন থেকে কী বেরিয়ে গেছে তা দেখতে পারেন। |

"Beta adapter" মানে ClawMetry সেই রানটাইমের প্রকৃত অন-ডিস্ক ফরম্যাটের জন্য একটি রিডার শিপ করে, প্রতিটি বাস্তব মেশিনে বাস্তব ইনস্টলের বিপরীতে তৈরি + যাচাই করা (`tests/fixtures/runtimes/<rt>/` দেখুন)। অ্যাডাপ্টারগুলো রিড-অনলি; প্রতিটি তার রানটাইম আসলে কী সংরক্ষণ করে সে বিষয়ে সৎ (যেমন, PicoClaw/NanoClaw/Cursor ডিস্কে টোকেন খরচ লেখে না)। একই নোডে একাধিক রানটাইম চললে, রানটাইম সুইচার পরিষ্কার ডিপ-ডাইভের জন্য সেশন ভিউকে একটিতে সীমাবদ্ধ করে দেয়।

## যেকোনো SDK এজেন্ট ট্র্যাক করুন — আউট-লুপ খরচ অ্যাট্রিবিউশন

উপরের রানটাইমগুলো সবই ডিস্কে সেশন লেখে। আপনার নিজের **প্রোডাকশন এজেন্ট** — যেটা আপনি OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, বা একটি সাধারণ `httpx` লুপের ওপর তৈরি করেছেন — সেটা তা করে না। ClawMetry-এর জিরো-কনফিগ ইন্টারসেপ্টর `httpx`/`requests`-কে মাংকি-প্যাচ করে তার LLM কলগুলো (খরচ, টোকেন, লেটেন্সি, এরর) ঠিকই ধরে ফেলে:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (অথবা `CLAWMETRY_SOURCE=support-agent` এনভায়রনমেন্ট ভেরিয়েবল) প্রতিটি কলকে একটি **নামযুক্ত সোর্স** দিয়ে ট্যাগ করে, তাই আপনি যে প্রতিটি প্রোডাক্ট চালান তা ড্যাশবোর্ডের **🔌 Out-loop sources** কার্ডে Overview-তে নিজস্ব প্রথম-শ্রেণির, খরচ-অ্যাট্রিবিউটেবল লাইন হিসেবে দেখা যায় — প্রতি এজেন্টের জন্য কল, প্রোভাইডার, লেটেন্সি, এরর রেট। সোর্স সেট করা হয়নি? কলগুলো তখনও ট্র্যাক হয়; কার্ডটি শুধু লুকানো থাকে।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

এটি একই ডেটা লেয়ার যা রানটাইম অ্যাডাপ্টারগুলো খাওয়ায় (DuckDB → ক্লাউড স্ন্যাপশট), তাই আউট-লুপ সোর্সগুলো বাকি সবকিছুর মতোই, E2E-এনক্রিপ্টেড অবস্থায় ক্লাউড ড্যাশবোর্ডে সিঙ্ক হয়।

## OpenTelemetry — ভেন্ডর-নিরপেক্ষ, আপনার ট্রেস যেকোনো জায়গায় পাঠান

ClawMetry উভয় দিকে **OpenTelemetry** বলতে পারে, **GenAI সিমান্টিক কনভেনশন** ব্যবহার করে, তাই আপনার এজেন্ট ট্রেস কখনও একটি টুলে আটকে থাকে না।

প্রতিটি সেশন — LLM কল, টুল, সাব-এজেন্ট, টোকেন, খরচ — যেকোনো কালেক্টরে (Datadog, Grafana, Honeycomb, বা আপনার নিজের OTel Collector) OTLP/HTTP GenAI স্প্যান হিসেবে **এক্সপোর্ট** করুন:

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

**ইনজেস্ট** — বিল্ট-ইন OTLP রিসিভার `/v1/traces`, `/v1/logs`, এবং `/v1/metrics`-এ যেকোনো জায়গা থেকে ট্রেস, লগ এবং মেট্রিক্স গ্রহণ করে। যেকোনো OpenTelemetry-ইনস্ট্রুমেন্টেড অ্যাপকে এটির দিকে পয়েন্ট করুন:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON ট্রেস ও লগ সাধারণ `pip install clawmetry`-তেই কাজ করে, কোনো এক্সট্রা লাগে না। Protobuf ইনজেস্ট (এবং OTLP/JSON মেট্রিক্স) এর জন্য দরকার `pip install clawmetry[otel]`। যে অ্যাপ নিজের `service.name` সেট করে সেটি রানটাইম সুইচারে তার নিজস্ব এজেন্ট হিসেবে দেখা যায়, তার নিজস্ব খরচ ও টোকেনসহ।

আপনি পাবেন জিরো-কনফিগ, লোকাল-ফার্স্ট ClawMetry ড্যাশবোর্ড **এবং** আপনার দল ইতিমধ্যেই যা চালায় সেই ব্যাকএন্ডে আপনার ডেটা — কোনো লক-ইন নেই, দ্বিতীয় কোনো এজেন্ট ইনস্টল করতে হবে না।

## কনফিগারেশন

বেশিরভাগ মানুষের কোনো কনফিগারেশনই লাগে না। ClawMetry আপনার ওয়ার্কস্পেস, লগ, সেশন, এবং ক্রন স্বয়ংক্রিয়ভাবে শনাক্ত করে নেয়।

কাস্টমাইজ করার দরকার হলে:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

সব অপশন: `clawmetry --help`

## সমর্থিত চ্যানেল

আপনি কনফিগার করা প্রতিটি OpenClaw চ্যানেলের জন্য ClawMetry লাইভ অ্যাক্টিভিটি দেখায়। আপনার `openclaw.json`-এ যেসব চ্যানেল আসলে সেটআপ করা আছে শুধু সেগুলোই Flow ডায়াগ্রামে দেখা যায় — কনফিগার না করাগুলো স্বয়ংক্রিয়ভাবে লুকানো থাকে।

Flow-তে যেকোনো চ্যানেল নোডে ক্লিক করে ইনকামিং/আউটগোয়িং মেসেজ গণনাসহ একটি লাইভ চ্যাট বাবল ভিউ দেখুন।

| চ্যানেল | স্ট্যাটাস | লাইভ পপআপ | নোট |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | মেসেজ, পরিসংখ্যান, ১০সে রিফ্রেশ |
| 💬 **iMessage** | ✅ Full | ✅ | সরাসরি `~/Library/Messages/chat.db` পড়ে |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) এর মাধ্যমে |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli এর মাধ্যমে |
| 🟣 **Discord** | ✅ Full | ✅ | গিল্ড + চ্যানেল শনাক্তকরণ |
| 🟪 **Slack** | ✅ Full | ✅ | ওয়ার্কস্পেস + চ্যানেল শনাক্তকরণ |
| 🌐 **Webchat** | ✅ Full | ✅ | বিল্ট-ইন ওয়েব UI সেশন |
| 📡 **IRC** | ✅ Full | ✅ | টার্মিনাল-স্টাইল বাবল UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API এর মাধ্যমে iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API ওয়েবহুকের মাধ্যমে |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams বট প্লাগইনের মাধ্যমে |
| 🔷 **Mattermost** | ✅ Full | ✅ | সেলফ-হোস্টেড টিম চ্যাট |
| 🟩 **Matrix** | ✅ Full | ✅ | বিকেন্দ্রীভূত, E2EE সমর্থন |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | বিকেন্দ্রীভূত NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC সংযোগের মাধ্যমে চ্যাট |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | ওয়েবসকেট ইভেন্ট সাবস্ক্রিপশন |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **স্বয়ংক্রিয় শনাক্তকরণ:** ClawMetry আপনার `~/.openclaw/openclaw.json` পড়ে এবং শুধু আপনার আসলেই কনফিগার করা চ্যানেলগুলোই রেন্ডার করে। ম্যানুয়াল সেটআপের দরকার নেই।

## Docker ডিপ্লয়মেন্ট

কনটেইনারে ClawMetry চালাতে চান? কোনো সমস্যা নেই! 🐳

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

> **নোট:** Docker-এ চালানোর সময়, আপনার এজেন্টের ডেটা + লগ ডিরেক্টরি মাউন্ট করুন (যেমন `~/.openclaw`, `~/.claude`, `~/.codex`) যাতে ClawMetry আপনার সেটআপ স্বয়ংক্রিয়ভাবে শনাক্ত করতে পারে।

## প্রয়োজনীয়তা

- Python 3.8+
- Flask (pip এর মাধ্যমে স্বয়ংক্রিয়ভাবে ইনস্টল হয়)
- একই মেশিনে একটি AI এজেন্ট রানটাইম: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, বা QM (অথবা Docker এর জন্য মাউন্ট করা ভলিউম)
- Linux বা macOS

## NemoClaw / OpenShell সমর্থন

ClawMetry স্বয়ংক্রিয়ভাবে [NemoClaw](https://github.com/NVIDIA/NemoClaw) শনাক্ত করে — NVIDIA-এর এন্টারপ্রাইজ সিকিউরিটি র‍্যাপার যা OpenClaw এজেন্টদের স্যান্ডবক্সড OpenShell কনটেইনারের ভেতরে চালায়।

বেশিরভাগ ক্ষেত্রে কোনো অতিরিক্ত কনফিগারেশনের দরকার নেই। সিঙ্ক ডেমন সেশন ফাইলগুলো স্বয়ংক্রিয়ভাবে খুঁজে বের করে, সেগুলো হোস্টে `~/.openclaw/`-এ থাকুক বা OpenShell কনটেইনারের ভেতরেই থাকুক।

### কীভাবে কাজ করে

ClawMetry দুইভাবে NemoClaw শনাক্ত করে:

1. **বাইনারি শনাক্তকরণ** — `nemoclaw` CLI আছে কিনা তা চেক করে এবং স্যান্ডবক্স তথ্য পেতে `nemoclaw status` চালায়
2. **কনটেইনার শনাক্তকরণ** — চলমান Docker কনটেইনারগুলোতে `openshell`, `nemoclaw`, বা `ghcr.io/nvidia/` ইমেজ স্ক্যান করে, তারপর ভলিউম মাউন্ট বা `docker cp` এর মাধ্যমে সেশন পড়ে

NemoClaw কনটেইনার থেকে সিঙ্ক করা সেশন ফাইলগুলো ক্লাউড ড্যাশবোর্ডে `runtime=nemoclaw` এবং `container_id` মেটাডেটা দিয়ে ট্যাগ করা হয়, তাই আপনি এক নজরে সেগুলোকে স্ট্যান্ডার্ড OpenClaw সেশন থেকে আলাদা করতে পারবেন।

### প্রস্তাবিত সেটআপ: HOST-এ সিঙ্ক ডেমন

সেরা অভিজ্ঞতার জন্য, ClawMetry-এর সিঙ্ক ডেমনটি **হোস্ট মেশিনে** চালান (স্যান্ডবক্সের ভেতরে নয়)। এটি NemoClaw নেটওয়ার্ক পলিসি বিধিনিষেধ এড়িয়ে যায়।

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে যেকোনো চলমান OpenShell কনটেইনারের ভেতরে সেশন খুঁজে বের করবে।

### ঐচ্ছিক: স্পষ্ট স্যান্ডবক্স নাম

স্বয়ংক্রিয় শনাক্তকরণ কাজ না করলে, ClawMetry-কে সঠিক স্যান্ডবক্সের দিকে নির্দেশ করুন:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### স্যান্ডবক্সের ভেতরে চালানো (অ্যাডভান্সড)

যদি আপনাকে সিঙ্ক ডেমনটি **স্যান্ডবক্সের ভেতরে** OpenShell-এ চালাতেই হয়, তাহলে আপনার NemoClaw নেটওয়ার্ক পলিসিতে এই egress নিয়মটি যোগ করুন যাতে এটি ClawMetry ইনজেস্ট API-এ পৌঁছাতে পারে:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

প্রয়োগ করুন এভাবে:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### পোর্ট এবং এন্ডপয়েন্ট

| এন্ডপয়েন্ট | পোর্ট | প্রোটোকল | প্রয়োজনীয় |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | হ্যাঁ (সিঙ্ক ডেমন → ক্লাউড) |
| `localhost:8900` | 8900 | HTTP | হ্যাঁ (লোকাল ড্যাশবোর্ড UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | কনটেইনার সেশন আবিষ্কারের জন্য |

সিঙ্ক ডেমন শুধুমাত্র `ingest.clawmetry.com`-এ আউটবাউন্ড HTTPS কল করে। কোনো ইনবাউন্ড পোর্টের দরকার নেই।

---

## ক্লাউড ডিপ্লয়মেন্ট

SSH টানেল, রিভার্স প্রক্সি, এবং Docker-এর জন্য দেখুন **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**।

## টেস্টিং

এই প্রজেক্টটি BrowserStack দিয়ে টেস্ট করা হয়।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## টেলিমেট্রি

ClawMetry বেনামী ইনস্টল-লাইফসাইকেল পিং পাঠায়
`https://app.clawmetry.com/api/install`-এ: নতুন মেশিনে প্রথমবার
`clawmetry` CLI চালানোর সময় একটি `install` পিং, নতুন ভার্সনে
আপগ্রেড করার পর প্রথম রানে একটি `update` পিং, এবং ইন-ড্যাশবোর্ড
অনবোর্ডিং পছন্দ সম্পূর্ণ করলে একটি `onboarded` পিং। আমরা এটি ব্যবহার
করি প্রকৃত ইনস্টল গণনা করতে (কাঁচা PyPI ডাউনলোড সংখ্যার ~৯৮% মিরর, CI,
এবং অটো-আপডেট রি-ডাউনলোড) এবং কোন এজেন্ট ফ্রেমওয়ার্ক ও ভার্সন আসলে
ব্যবহৃত হচ্ছে তা জানতে।

**প্রতি লাইফসাইকেল ইভেন্ট প্রতি ভার্সনে সর্বোচ্চ একটি POST**, যাতে থাকে:

| ফিল্ড | উদাহরণ | কেন |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-এ সংরক্ষিত র‍্যান্ডম UUID | ডুপ্লিকেট এড়াতে; আপনি স্পষ্টভাবে Cloud sync সংযুক্ত না করা পর্যন্ত বেনামী (তারপর অথেন্টিকেটেড ডেমন হার্টবিট এটি বহন করে, এই ইনস্টলটিকে আপনার অ্যাকাউন্টের সাথে যুক্ত করে) |
| `event` | `install` / `update` / `onboarded` | নতুন ইনস্টল নাকি বিদ্যমান একটির আপগ্রেড |
| `version` | `0.12.167` | কোন ভার্সনগুলো ব্যবহৃত হচ্ছে |
| `os` / `os_version` | `Darwin` / `25.3.0` | প্ল্যাটফর্ম সমর্থনের অগ্রাধিকার |
| `python` | `3.11.15` | Python ভার্সন সমর্থন ম্যাট্রিক্স |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | পরবর্তীতে আমাদের কোন এজেন্টের সাথে ইন্টিগ্রেট করা উচিত |
| `is_ci` / `ci_provider` | `true` / `github_actions` | মানুষের ইনস্টল থেকে CI নয়েজ আলাদা করতে |

**আমরা যা পাঠাই না**: IP (ক্লাউড সার্ভার-সাইডে রিকোয়েস্ট থেকে
কান্ট্রি কোড বের করে নেয়, তারপর IP ফেলে দেয়), হোস্টনেম, ইউজারনেম,
ওয়ার্কস্পেস পাথ, ফাইলের কন্টেন্ট, আপনার api_key, আপনার ইমেইল, বা
কোনো PII বা ওয়ার্কস্পেস-নির্দিষ্ট কিছু। ওয়্যার পেলোডটি
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-এ অডিটযোগ্য।

**অপ্ট আউট করুন** (এর যেকোনো একটি স্থায়ীভাবে এটি নিষ্ক্রিয় করে দেয়):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

নেটওয়ার্ক ব্যর্থতা কখনও `clawmetry`-কে চালানো থেকে ব্লক করে না — পিংটি
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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> দ্বারা নির্মিত · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ইকোসিস্টেমের একটি অংশ</sub>
</p>
