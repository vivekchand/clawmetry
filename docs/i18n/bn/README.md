<!-- i18n-src:bab48eec552f -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টকে ভাবতে দেখুন।** **১৪টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজারভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ১০টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। জিরো কনফিগ। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900**-এ খোলে, ব্যাস কাজ শেষ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ১৪টি এজেন্ট রানটাইমের সাথে কাজ করে

ClawMetry শুরু হয়েছিল OpenClaw-এর জন্য অবজারভেবিলিটি হিসেবে, এবং এখন এটি একটি ড্যাশবোর্ডে আপনার **পুরো এজেন্ট ফ্লিট** মিটার করে, আপনার মেশিনে থাকা প্রতিটি রানটাইম স্বয়ংক্রিয়ভাবে শনাক্ত করে:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw এবং NemoClaw ওপেন-সোর্স অ্যাপে বিনামূল্যে; অন্যান্য রানটাইমগুলো ClawMetry Cloud অথবা একটি সেলফ-হোস্টেড Pro লাইসেন্সের মাধ্যমে সক্রিয় হয়। হেডার থেকে রানটাইম বদলান এবং প্রতিটি ট্যাব — খরচ, টোকেন, টুল, ট্রেস — সেই রানটাইমের জন্য পুনরায় স্কোপ হয়ে যায়। ঠিক কোনটা ফ্রি/পেইড, টায়ার ম্যাট্রিক্স, `/api/entitlement`-এর শেপ, এবং `clawmetry license` CLI দেখতে **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** দেখুন।

## আপনি যা পাবেন

- **Flow** — চ্যানেল, ব্রেইন, টুল এবং ফিরতি পথ দিয়ে বার্তা প্রবাহিত হওয়া দেখানো একটি লাইভ অ্যানিমেটেড ডায়াগ্রাম
- **Overview** — হেলথ চেক, অ্যাক্টিভিটি হিটম্যাপ, সেশন সংখ্যা, মডেল তথ্য
- **Usage** — দৈনিক/সাপ্তাহিক/মাসিক ব্রেকডাউন সহ টোকেন এবং খরচ ট্র্যাকিং
- **Sessions** — মডেল, টোকেন, শেষ অ্যাক্টিভিটি সহ সক্রিয় এজেন্ট সেশন
- **Crons** — স্ট্যাটাস, পরবর্তী রান, সময়কাল সহ শিডিউলড জব
- **Logs** — কালার-কোডেড রিয়েল-টাইম লগ স্ট্রিমিং
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, দৈনিক নোট ব্রাউজ করুন
- **Transcripts** — সেশন হিস্টরি পড়ার জন্য চ্যাট-বাবল UI
- **Alerts** — বাজেট ক্যাপ, এরর-রেট ট্রিগার, এজেন্ট-অফলাইন শনাক্তকরণ; Slack, Discord, PagerDuty, Telegram, Email-এ রুট করে
- **Approvals** — ধ্বংসাত্মক ডিলিট, ফোর্স পুশ, DB মিউটেশন, sudo, প্যাকেজ ইনস্টল, নেটওয়ার্ক কল এক-ক্লিক সাইন-অফের পেছনে গেট করে

## স্ক্রিনশট

### 🧠 Brain — লাইভ এজেন্ট ইভেন্ট স্ট্রিম
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — টোকেন ব্যবহার ও সেশন সারাংশ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — রিয়েল-টাইম টুল কল ফিড
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — মডেল ও সেশন অনুযায়ী খরচের ব্রেকডাউন
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ওয়ার্কস্পেস ফাইল ব্রাউজার
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — পসচার ও অডিট লগ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — বাজেট ক্যাপ, এরর-রেট ট্রিগার, Slack / Discord / PagerDuty / Email-এ ওয়েবহুক
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ম্যানুয়াল সাইন-অফের পেছনে ঝুঁকিপূর্ণ টুল কল গেট করুন; পলিসি-ব্যাকড প্রোটেকশন রুল
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-এর জন্য প্রি-এক্সিকিউশন ব্লকিং** — একটি কমান্ড একটি
PreToolUse হুক ইনস্টল করে যা মিলে যাওয়া টুল কলগুলোকে *রান হওয়ার আগে* থামিয়ে দেয় এবং আপনার
সিদ্ধান্তের জন্য অপেক্ষা করে ([ক্লাউড পুশ নোটিফিকেশন](https://app.clawmetry.com/push) সক্রিয় থাকলে আপনার ফোন থেকে এক ট্যাপে):

```bash
clawmetry hooks install     # ~/.claude/settings.json লেখে (idempotent)
clawmetry hooks status      # কী ওয়্যার করা আছে + কতগুলো পলিসি সক্রিয়
clawmetry hooks uninstall   # শুধু ClawMetry-এর এন্ট্রিগুলো সরায়
```

একটি deny শুধু সেই একটি টুল কল ব্লক করে — এজেন্ট তার সেশন রাখে এবং
অন্য কোনো পন্থা চেষ্টা করতে পারে। আপনার ফোনে অ্যাপ্রুভ করলে Claude Code-এর নিজস্ব
পারমিশন প্রম্পট স্কিপ হয়ে যায় (আপনি ইতিমধ্যে উত্তর দিয়েছেন)। মিলে না যাওয়া টুলগুলোর খরচ ~40ms এবং
Claude Code-এর স্বাভাবিক পারমিশন ফ্লো-তে চলে যায়। Claude Code নিজে যখন আপনার জন্য অপেক্ষা করছে
তখনও আপনি ফোনে পুশ পাবেন (`permission_prompt` / `idle_prompt` নোটিফিকেশন)।

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
সার্ভার চালু হলে `/v2`-এ সার্ভ হয়।

ডেভেলপ করার সময় দুটি টার্মিনাল ব্যবহার করুন:

```bash
# টার্মিনাল ১: :8900-এ Flask API/সার্ভার
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# টার্মিনাল ২: :5173-এ Vite dev সার্ভার
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` খুলুন। Vite `/api` রিকোয়েস্টগুলো
`http://localhost:8900`-এ প্রক্সি করে, তাই React অ্যাপটি অতিরিক্ত CORS সেটআপ ছাড়াই
লোকাল Flask সার্ভারের সাথে কথা বলতে পারে।

Python প্যাকেজের সাথে শিপ হওয়া বান্ডেল বিল্ড করতে:

```bash
cd frontend
npm run build
```

প্রোডাকশন বান্ডেলটি `clawmetry/static/v2/dist/`-এ লেখা হয়।

## রানটাইম / এজেন্ট কম্প্যাটিবিলিটি

ClawMetry শুধু OpenClaw নয়, আরও অনেক AI-এজেন্ট রানটাইম পর্যবেক্ষণ করে। OpenClaw ছাড়া প্রতিটি রানটাইমের নিজস্ব রিডার অ্যাডাপ্টার থাকে যা এর নেটিভ সেশন ফরম্যাটকে ClawMetry-এর ইউনিফায়েড শেপে রূপান্তর করে; ডেমন এগুলোকে একই DuckDB স্টোর + ক্লাউড স্ন্যাপশটে ইনজেস্ট করে, রানটাইম দিয়ে ট্যাগ করা হয়, এবং একাধিক রানটাইম উপস্থিত থাকলে সেশন রিপ্লে ট্যাব একটি **রানটাইম সুইচার** দেখায়। সম্পূর্ণ ম্যাট্রিক্স + নতুন রানটাইম যোগ করার গাইডের জন্য [`docs/compatibility.md`](docs/compatibility.md) দেখুন, এবং OpenClaw-ফ্যামিলি প্রাইমারের জন্য [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) দেখুন।

| রানটাইম / এজেন্ট | স্ট্যাটাস | নোট |
|---|---|---|
| **OpenClaw** | নেটিভ | রেফারেন্স রানটাইম, স্বয়ংক্রিয়ভাবে শনাক্ত |
| **PicoClaw** | বেটা অ্যাডাপ্টার | ফ্ল্যাট `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)। ট্রান্সক্রিপ্ট, মডেল, টুল কল। |
| **NanoClaw** | বেটা অ্যাডাপ্টার | প্রতি-সেশন SQLite (`data/v2-sessions`)। ট্রান্সক্রিপ্ট + মেসেজ সংখ্যা। |
| **Hermes** | বেটা অ্যাডাপ্টার | SQLite `~/.hermes/state.db`। ট্রান্সক্রিপ্ট, মডেল, টোকেন/খরচ। |
| **Claude Code** | বেটা অ্যাডাপ্টার | JSONL `~/.claude/projects/.../<id>.jsonl`। ট্রান্সক্রিপ্ট, মডেল, টুল কল + থিংকিং, টোকেন ব্যবহার। |
| **Codex** | বেটা অ্যাডাপ্টার | রোলআউট JSONL `~/.codex/sessions/...`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Cursor** | বেটা অ্যাডাপ্টার | SQLite `state.vscdb`। চ্যাট/কম্পোজার ট্রান্সক্রিপ্ট, মডেল। |
| **Aider** | বেটা অ্যাডাপ্টার | প্রতি প্রজেক্টে `.aider.chat.history.md`। ট্রান্সক্রিপ্ট, মডেল, টোকেন সংখ্যা। |
| **Goose** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/goose`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন মোট। |
| **opencode** | বেটা অ্যাডাপ্টার | SQLite `~/.local/share/opencode`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Qwen Code** | বেটা অ্যাডাপ্টার | JSONL `~/.qwen/projects/.../chats`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন ব্যবহার। |
| **Pi** | বেটা অ্যাডাপ্টার | JSONL `~/.pi/agent/sessions`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |
| **Deep Agents** | বেটা অ্যাডাপ্টার | SQLite `~/.deepagents/.state/sessions.db`। ট্রান্সক্রিপ্ট, মডেল, টুল কল, টোকেন + খরচ। |

"বেটা অ্যাডাপ্টার" মানে হলো ClawMetry সেই রানটাইমের প্রকৃত অন-ডিস্ক ফরম্যাটের জন্য একটি রিডার শিপ করে, প্রতিটি একটি বাস্তব মেশিনে বাস্তব ইনস্টলের বিপরীতে তৈরি + যাচাই করা (`tests/fixtures/runtimes/<rt>/` দেখুন)। অ্যাডাপ্টারগুলো রিড-অনলি; প্রতিটি তার রানটাইম প্রকৃতপক্ষে যা ডিস্কে স্টোর করে সে সম্পর্কে সৎ (যেমন, PicoClaw/NanoClaw/Cursor ডিস্কে টোকেন খরচ লেখে না)। একটি নোডে একাধিক রানটাইম চললে, রানটাইম সুইচার সেশন ভিউকে একটির জন্য স্কোপ করে একটি পরিষ্কার ডিপ-ডাইভের জন্য।

## যেকোনো SDK এজেন্ট ট্র্যাক করুন — আউট-লুপ কস্ট অ্যাট্রিবিউশন

উপরের রানটাইমগুলো সবই সেশন ডিস্কে লেখে। আপনার নিজের **প্রোডাকশন এজেন্ট** — যেটি আপনি OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, বা একটি সাধারণ `httpx` লুপের ওপর তৈরি করেছেন — তা লেখে না। ClawMetry-এর জিরো-কনফিগ ইন্টারসেপ্টর তবুও `httpx`/`requests` মাংকি-প্যাচ করে এর LLM কলগুলো (খরচ, টোকেন, লেটেন্সি, এরর) ক্যাপচার করে:

```python
import clawmetry.track            # ইন্টারসেপ্টর সক্রিয় করুন
clawmetry.track.set_source("support-agent")   # এই প্রোডাক্টের নাম দিন

# ...আপনার এজেন্ট স্বাভাবিকভাবে চলে; প্রতিটি LLM কল এখন ট্র্যাক + অ্যাট্রিবিউট করা হয়।
```

`set_source()` (অথবা `CLAWMETRY_SOURCE=support-agent` env ভেরিয়েবল) প্রতিটি কলকে একটি **নামযুক্ত সোর্স** দিয়ে ট্যাগ করে, তাই আপনার চালানো প্রতিটি প্রোডাক্ট ড্যাশবোর্ডের Overview-এর **🔌 Out-loop sources** কার্ডে নিজস্ব প্রথম-শ্রেণির, খরচ-অ্যাট্রিবিউটযোগ্য লাইন হিসেবে দেখা যায় — প্রতি এজেন্টে কল, প্রোভাইডার, লেটেন্সি, এরর রেট। কোনো সোর্স সেট করেননি? কলগুলো তবুও ট্র্যাক হয়; কার্ডটি শুধু লুকানো থাকে।

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

এটি একই ডেটা লেয়ার যা রানটাইম অ্যাডাপ্টারগুলো ফিড করে (DuckDB → ক্লাউড স্ন্যাপশট), তাই আউট-লুপ সোর্সগুলো বাকি সবকিছুর মতোই ক্লাউড ড্যাশবোর্ডে সিঙ্ক হয়, E2E-এনক্রিপ্টেড।

## OpenTelemetry — ভেন্ডর-নিউট্রাল, আপনার ট্রেস যেকোনো জায়গায় পাঠান

ClawMetry উভয় দিকেই **OpenTelemetry**-তে কথা বলে, **GenAI সিমান্টিক কনভেনশন** ব্যবহার করে, তাই আপনার এজেন্ট ট্রেসগুলো কখনও একটি টুলে লক-ইন হয় না।

প্রতিটি সেশন — LLM কল, টুল, সাব-এজেন্ট, টোকেন, খরচ — কে যেকোনো কালেক্টরে (Datadog, Grafana, Honeycomb, বা আপনার নিজস্ব OTel Collector) OTLP/HTTP GenAI স্প্যান হিসেবে **এক্সপোর্ট** করুন:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# সমতুল্যভাবে:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth হেডার এবং পোল ইন্টারভাল ঐচ্ছিক env ভেরিয়েবল:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # অতিরিক্ত HTTP হেডার
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # সেকেন্ড (ডিফল্ট 60)
```

**ইনজেস্ট** — বিল্ট-ইন OTLP রিসিভার `/v1/traces` এবং `/v1/metrics`-এ অন্য যেকোনো কিছু থেকে ট্রেস এবং মেট্রিক্স গ্রহণ করে (প্রোটোবাফ ইনজেস্টের জন্য `pip install clawmetry[otel]`)।

আপনি জিরো-কনফিগ, লোকাল-ফার্স্ট ClawMetry ড্যাশবোর্ড **এবং** আপনার দল ইতিমধ্যে যে ব্যাকএন্ড চালাচ্ছে তাতে আপনার ডেটা দুটোই পাবেন — কোনো লক-ইন নেই, দ্বিতীয় কোনো এজেন্ট ইনস্টল করার দরকার নেই।

## কনফিগারেশন

বেশিরভাগ মানুষের কোনো কনফিগের দরকার নেই। ClawMetry আপনার ওয়ার্কস্পেস, লগ, সেশন এবং ক্রন স্বয়ংক্রিয়ভাবে শনাক্ত করে।

যদি আপনার কাস্টমাইজ করতে হয়:

```bash
clawmetry --port 9000              # কাস্টম পোর্ট (ডিফল্ট: 8900)
clawmetry --host 127.0.0.1         # শুধু localhost-এ বাইন্ড করুন
clawmetry --workspace ~/mybot      # কাস্টম ওয়ার্কস্পেস পাথ
clawmetry --name "Alice"           # Flow ভিজ্যুয়ালাইজেশনে আপনার নাম
```

সব অপশন: `clawmetry --help`

## সমর্থিত চ্যানেল

আপনার কনফিগার করা প্রতিটি OpenClaw চ্যানেলের জন্য ClawMetry লাইভ অ্যাক্টিভিটি দেখায়। শুধুমাত্র আপনার `openclaw.json`-এ প্রকৃতপক্ষে সেটআপ করা চ্যানেলগুলোই Flow ডায়াগ্রামে দেখা যায় — কনফিগার না করা চ্যানেলগুলো স্বয়ংক্রিয়ভাবে লুকানো থাকে।

Flow-তে যেকোনো চ্যানেল নোডে ক্লিক করলে ইনকামিং/আউটগোয়িং মেসেজ সংখ্যা সহ একটি লাইভ চ্যাট বাবল ভিউ দেখা যায়।

| চ্যানেল | স্ট্যাটাস | লাইভ পপআপ | নোট |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ পূর্ণ | ✅ | মেসেজ, পরিসংখ্যান, 10s রিফ্রেশ |
| 💬 **iMessage** | ✅ পূর্ণ | ✅ | `~/Library/Messages/chat.db` সরাসরি পড়ে |
| 💚 **WhatsApp** | ✅ পূর্ণ | ✅ | WhatsApp Web-এর মাধ্যমে (Baileys) |
| 🔵 **Signal** | ✅ পূর্ণ | ✅ | signal-cli-র মাধ্যমে |
| 🟣 **Discord** | ✅ পূর্ণ | ✅ | গিল্ড + চ্যানেল শনাক্তকরণ |
| 🟪 **Slack** | ✅ পূর্ণ | ✅ | ওয়ার্কস্পেস + চ্যানেল শনাক্তকরণ |
| 🌐 **Webchat** | ✅ পূর্ণ | ✅ | বিল্ট-ইন ওয়েব UI সেশন |
| 📡 **IRC** | ✅ পূর্ণ | ✅ | টার্মিনাল-স্টাইল বাবল UI |
| 🍏 **BlueBubbles** | ✅ পূর্ণ | ✅ | BlueBubbles REST API-র মাধ্যমে iMessage |
| 🔵 **Google Chat** | ✅ পূর্ণ | ✅ | Chat API ওয়েবহুকের মাধ্যমে |
| 🟣 **MS Teams** | ✅ পূর্ণ | ✅ | Teams বট প্লাগইনের মাধ্যমে |
| 🔷 **Mattermost** | ✅ পূর্ণ | ✅ | সেলফ-হোস্টেড টিম চ্যাট |
| 🟩 **Matrix** | ✅ পূর্ণ | ✅ | ডিসেন্ট্রালাইজড, E2EE সমর্থন |
| 🟢 **LINE** | ✅ পূর্ণ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ পূর্ণ | ✅ | ডিসেন্ট্রালাইজড NIP-04 DM |
| 🟣 **Twitch** | ✅ পূর্ণ | ✅ | IRC কানেকশনের মাধ্যমে চ্যাট |
| 🔷 **Feishu/Lark** | ✅ পূর্ণ | ✅ | WebSocket ইভেন্ট সাবস্ক্রিপশন |
| 🔵 **Zalo** | ✅ পূর্ণ | ✅ | Zalo Bot API |

> **স্বয়ংক্রিয় শনাক্তকরণ:** ClawMetry আপনার `~/.openclaw/openclaw.json` পড়ে এবং শুধুমাত্র আপনি প্রকৃতপক্ষে কনফিগার করা চ্যানেলগুলো রেন্ডার করে। কোনো ম্যানুয়াল সেটআপের দরকার নেই।

## Docker ডেপ্লয়মেন্ট

একটি কন্টেইনারে ClawMetry চালাতে চান? কোনো সমস্যা নেই! 🐳

**Docker দিয়ে দ্রুত শুরু:**

```bash
# ইমেজ বিল্ড করুন
docker build -t clawmetry .

# ডিফল্ট সেটিংস দিয়ে চালান
docker run -p 8900:8900 clawmetry

# অথবা আপনার এজেন্টের ডেটা ডিরেক্টরি মাউন্ট করুন (দেখানো হয়েছে: OpenClaw-এর ~/.openclaw)
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
- Flask (pip-এর মাধ্যমে স্বয়ংক্রিয়ভাবে ইনস্টল হয়)
- একই মেশিনে একটি AI এজেন্ট রানটাইম: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, অথবা Deep Agents (অথবা Docker-এর জন্য মাউন্ট করা ভলিউম)
- Linux বা macOS

## NemoClaw / OpenShell সাপোর্ট

ClawMetry স্বয়ংক্রিয়ভাবে [NemoClaw](https://github.com/NVIDIA/NemoClaw) শনাক্ত করে — NVIDIA-র এন্টারপ্রাইজ সিকিউরিটি র‍্যাপার যা OpenClaw-এর জন্য যা স্যান্ডবক্সড OpenShell কন্টেইনারের ভেতরে এজেন্ট চালায়।

বেশিরভাগ ক্ষেত্রে অতিরিক্ত কোনো কনফিগারেশনের দরকার নেই। সিঙ্ক ডেমন স্বয়ংক্রিয়ভাবে সেশন ফাইল খুঁজে বের করে, সেগুলো হোস্টে `~/.openclaw/`-এ থাকুক বা একটি OpenShell কন্টেইনারের ভেতরে থাকুক।

### এটি কীভাবে কাজ করে

ClawMetry দুইভাবে NemoClaw শনাক্ত করে:

1. **বাইনারি শনাক্তকরণ** — `nemoclaw` CLI চেক করে এবং স্যান্ডবক্স তথ্য পেতে `nemoclaw status` চালায়
2. **কন্টেইনার শনাক্তকরণ** — `openshell`, `nemoclaw`, বা `ghcr.io/nvidia/` ইমেজের জন্য চলমান Docker কন্টেইনার স্ক্যান করে, তারপর ভলিউম মাউন্ট বা `docker cp`-এর মাধ্যমে সেশন পড়ে

NemoClaw কন্টেইনার থেকে সিঙ্ক করা সেশন ফাইলগুলো ক্লাউড ড্যাশবোর্ডে `runtime=nemoclaw` এবং `container_id` মেটাডেটা দিয়ে ট্যাগ করা হয়, যাতে আপনি এক নজরে স্ট্যান্ডার্ড OpenClaw সেশন থেকে সেগুলো আলাদা করতে পারেন।

### প্রস্তাবিত সেটআপ: হোস্টে সিঙ্ক ডেমন

সেরা অভিজ্ঞতার জন্য, ClawMetry-এর সিঙ্ক ডেমন **হোস্ট মেশিনে** চালান (স্যান্ডবক্সের ভেতরে নয়)। এটি NemoClaw নেটওয়ার্ক পলিসি নিষেধাজ্ঞা এড়ায়।

```bash
# হোস্টে (স্যান্ডবক্সের বাইরে)
pip install clawmetry
clawmetry connect
clawmetry sync
```

সিঙ্ক ডেমন যেকোনো চলমান OpenShell কন্টেইনারের ভেতরে সেশন স্বয়ংক্রিয়ভাবে খুঁজে পাবে।

### ঐচ্ছিক: স্পষ্ট স্যান্ডবক্স নাম

যদি স্বয়ংক্রিয় শনাক্তকরণ কাজ না করে, ClawMetry-কে সঠিক স্যান্ডবক্সের দিকে নির্দেশ করুন:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### স্যান্ডবক্সের ভেতরে চালানো (উন্নত)

যদি আপনাকে অবশ্যই OpenShell স্যান্ডবক্সের **ভেতরে** সিঙ্ক ডেমন চালাতে হয়, ClawMetry ইনজেস্ট API-তে পৌঁছাতে পারার জন্য আপনার NemoClaw নেটওয়ার্ক পলিসিতে এই এগ্রেস রুলটি যোগ করুন:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

এভাবে অ্যাপ্লাই করুন:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### পোর্ট এবং এন্ডপয়েন্ট

| এন্ডপয়েন্ট | পোর্ট | প্রোটোকল | প্রয়োজনীয় |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | হ্যাঁ (সিঙ্ক ডেমন → ক্লাউড) |
| `localhost:8900` | 8900 | HTTP | হ্যাঁ (লোকাল ড্যাশবোর্ড UI) |
| Docker সকেট (`/var/run/docker.sock`) | — | ইউনিক্স সকেট | কন্টেইনার সেশন আবিষ্কারের জন্য |

সিঙ্ক ডেমন শুধুমাত্র `ingest.clawmetry.com`-এ আউটবাউন্ড HTTPS কল করে। কোনো ইনবাউন্ড পোর্টের দরকার নেই।

---

## ক্লাউড ডেপ্লয়মেন্ট

SSH টানেল, রিভার্স প্রক্সি, এবং Docker-এর জন্য **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** দেখুন।

## টেস্টিং

এই প্রজেক্টটি BrowserStack দিয়ে টেস্ট করা হয়েছে।

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## টেলিমেট্রি

আপনি নতুন মেশিনে প্রথমবার `clawmetry` CLI চালানোর সময় ClawMetry একটি একক
অ্যানোনিমাস "ফার্স্ট রান" পিং `https://app.clawmetry.com/api/install`-এ
পাঠায়। আমরা এটি ইনস্টল গণনা করতে (একটি OSS প্রজেক্টের জন্য আমাদের একমাত্র
মার্কেটিং মেট্রিক) এবং আমাদের ব্যবহারকারীরা কোন এজেন্ট ফ্রেমওয়ার্ক ইনস্টল করেছেন তা
জানতে ব্যবহার করি।

**প্রতি ইনস্টলে ঠিক একটি POST**, যাতে থাকে:

| ফিল্ড | উদাহরণ | কেন |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-এ স্টোর করা র‍্যান্ডম UUID | ডিডুপ; আপনার ইমেইল বা api_key-র সাথে লিঙ্কড নয় |
| `version` | `0.12.167` | কোন ভার্সন কতটা ব্যবহৃত হচ্ছে |
| `os` / `os_version` | `Darwin` / `25.3.0` | প্ল্যাটফর্ম সাপোর্ট অগ্রাধিকার |
| `python` | `3.11.15` | Python ভার্সন সাপোর্ট ম্যাট্রিক্স |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | পরবর্তীতে আমাদের কোন এজেন্টের সাথে ইন্টিগ্রেট করা উচিত |
| `is_ci` / `ci_provider` | `true` / `github_actions` | মানুষের ইনস্টল এবং CI নয়েজ আলাদা করা |

**আমরা যা পাঠাই না**: IP (ক্লাউড সার্ভার-সাইডে রিকোয়েস্ট থেকে
কান্ট্রি কোড ডেরাইভ করে, তারপর IP বাদ দেয়), হোস্টনেম, ইউজারনেম, ওয়ার্কস্পেস
পাথ, ফাইল কন্টেন্ট, আপনার api_key, আপনার ইমেইল, PII বা
ওয়ার্কস্পেস-স্পেসিফিক কিছু। ওয়্যার পেলোডটি
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-তে অডিটযোগ্য।

**অপ্ট আউট** (এর যেকোনো একটি এটি স্থায়ীভাবে নিষ্ক্রিয় করে):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # প্রতি-শেল
export DO_NOT_TRACK=1                          # W3C ক্রস-টুল স্ট্যান্ডার্ড
touch ~/.clawmetry/notelemetry                 # স্থায়ী ফাইল মার্কার
```

এখানে নেটওয়ার্ক ব্যর্থতা কখনও `clawmetry` চালানো ব্লক করে না — পিংটি
৩ সেকেন্ডের টাইমআউট সহ একটি ডেমন থ্রেডে ফায়ার-অ্যান্ড-ফরগেট।

## Star History

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
