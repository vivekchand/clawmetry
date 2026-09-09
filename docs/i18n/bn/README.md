<!-- i18n-src:61beb8393e2f -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**একটি এজেন্ট কোনো অগ্রগতি না করেই একশোটি টুল কল চালাতে পারে।** ClawMetry
আপনার কোডিং এজেন্টরা ইতিমধ্যেই যে সেশন ফাইলগুলো লেখে সেগুলো পড়ে, এবং টাইমলাইন,
টুল কলগুলো, এবং রানটাইম যে টোকেন ও খরচের তথ্য প্রকাশ করে তা একটি ভিউতে নিয়ে আসে —
যাতে আপনি বুঝতে পারেন কোন দীর্ঘ রান কাজ করছে আর কোনটা আটকে গেছে।

**৩০টি AI এজেন্ট রানটাইমের** সাথে কাজ করে — Claude Code, OpenAI Codex, Hermes, OpenClaw এবং আরও ২৬টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড। ([সম্পূর্ণ তালিকা](SUPPORTED_RUNTIMES.txt), ক্যাটালগ থেকে জেনারেট করা।)

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। কোনো কনফিগারেশন লাগে না। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে। কোনো কনফিগারেশন লাগে না: এটি আপনার কাছে যে
এজেন্ট রানটাইমগুলো ইতিমধ্যে আছে সেগুলো খুঁজে বের করে, শুধু পড়ার জন্য অ্যাক্সেস করে, এবং সেগুলো কীভাবে চলে তার কিছুই বদলায় না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ইনস্টল করার আগে

| | |
|---|---|
| **এটি কী করে** | আপনার এজেন্টরা ইতিমধ্যে যে সেশন ফাইল ও লগ লেখে সেগুলো পড়ে। কোনো SDK নেই, কোনো কোড পরিবর্তন নেই, আপনার অ্যাপে কোনো ইনস্ট্রুমেন্টেশন নেই। |
| **আপনি কী দেখেন** | সেশন টাইমলাইন, টুল-বাই-টুল রিপ্লে, টোকেন ও খরচের ব্রেকডাউন, এবং ট্র্যাজেক্টরি সিগন্যাল (লুপিং, বারবার ব্যর্থতা) — প্রতিটি রানটাইম অনুযায়ী। |
| **যা বিনামূল্যে** | `pip install clawmetry` কোনো অ্যাকাউন্ট, কী বা নেটওয়ার্ক কল ছাড়াই **OpenClaw, NVIDIA NemoClaw এবং Goose** পড়ে। বাকি ২৭টি — Claude Code, Codex, Cursor এবং বাকিগুলো — ক্লোজড-সোর্স `clawmetry-pro` কম্প্যানিয়ন দিয়ে পড়া হয়, যা ৭ দিনের ট্রায়াল বা একটি প্ল্যানের সাথে আসে — সঠিক বিভাজনের জন্য দেখুন [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)। |
| **কীভাবে শুরু করবেন** | `pip install clawmetry && clawmetry`, তারপর localhost:8900 খুলুন। এই মেশিনে এখনও কোনো এজেন্ট নেই? `clawmetry --sample` তিনটি লেবেলযুক্ত সিন্থেটিক সেশনে খোলে। |
| **আপনার মেশিন থেকে কী বের হয়** | আপনি `clawmetry connect` না চালালে কোনো সেশন ডেটা যায় না। ডিফল্টভাবে দুটি জিনিস চলে, দুটোই অপ্ট-আউট করা যায় এবং কোনোটিতেই সেশনের বিষয়বস্তু থাকে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং একটি PyPI ভার্সন চেক। প্রতিটি গন্তব্যের তালিকা [docs/EGRESS.md](docs/EGRESS.md)-এ আছে, যা মন্তব্য পড়ার বদলে ওয়্যার ক্যাপচার থেকে পুনর্নির্মিত। |

আপনি ফলাফল বিচার করার আগে জানা দরকার এমন দুটি সীমাবদ্ধতা: রানটাইমগুলো খুব
ভিন্ন ধরনের ডেটা প্রকাশ করে (কিছু একেবারেই কোনো খরচ প্রকাশ করে না — [ম্যাট্রিক্স](docs/compatibility.md)
বলে দেয় কোনগুলো, প্রতিটি রানটাইম অনুযায়ী), এবং কোনো কাজ পর্যবেক্ষণ করা মানেই সেটা
আটকানোর সামর্থ্য থাকা নয় ([কোন নিয়ন্ত্রণগুলো বাস্তব, প্রতিটি রানটাইম অনুযায়ী](docs/APPROVALS.md))।


## ৩০টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে বিনামূল্যে:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে বেশ কয়েকটি চালান এবং হেডার
সুইচার প্রতিটি ট্যাবকে তাদের যেকোনো একটিতে পুনরায় স্কোপ করে।

আপনার নিজের এজেন্ট একটি SDK দিয়ে তৈরি করেছেন? ইন্টারসেপ্টর সেটির LLM কলও
ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি যা পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট কী করেছে, টার্ন বাই টার্ন, রিপ্লে সহ
- **খরচ ও টোকেন**: রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অ্যানোমালি ফ্ল্যাগ সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলের মধ্য দিয়ে মেসেজ চলাচলের লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং ও টুল-কল ইভেন্ট স্ট্রিম, যেমনটা ঘটছে ঠিক তেমনই
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী উইন্ডো সাইজ, কম্প্যাকশন বনাম জোরপূর্বক ওভারফ্লো, এবং আমরা কী *দেখতে পারি না* তার একটি প্রতি-রানটাইম ম্যাপ ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমরি ও স্কিল**: প্রতিটি রানটাইম আসলে কোন ফাইল ও স্কিল লোড করেছে
- **হেলথ ও লগ**: ডিস্ক, মেমরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email-এ রুট করা
- **অ্যাপ্রুভাল**: ঝুঁকিপূর্ণ টুল কল চালানোর *আগেই* থামিয়ে দিন এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ

যেকোনো এজেন্ট-তুলনা টুল বিশ্বাস করার আগে দুটি প্রশ্নের উত্তর জানা দরকার।

**এটি রানটাইম জুড়ে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে সামলায়?**

একটি ব্যবহারের শতাংশ যতটা সৎ হয়, তা নির্ভর করে সেটা কী দিয়ে ভাগ করা হচ্ছে তার উপর। ClawMetry
[একটি টেবিল থেকে](clawmetry/context_windows.py) প্রোভাইডার অনুযায়ী উইন্ডো সাইজ নির্ধারণ করে, যা আপনি পড়তে ও
PR করতে পারেন, এবং এটি Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM কভার করে। এটি একটি ভেন্ডরের স্কেল দিয়ে
৩০টি রানটাইমই মাপে না। এটা গুরুত্বপূর্ণ: একটি ৩০০K GPT-5 টার্ন Anthropic-এর ২০০K এর
বিপরীতে স্কোর করলে ">১০০%, ব্লোন" পড়া যায়, যখন এটি আসলে GPT-5-এর ৪০০K-এর ৭৫%। একই
স্কেল একটি প্রকৃতপক্ষে ওভারফ্লো হওয়া ১৩০K DeepSeek টার্নকে একটি আরামদায়ক ৬৫% হিসেবে লুকিয়ে ফেলে।

প্রতিটি উইন্ডো তার উৎসের প্রমাণসহ আসে: `model_table`, `explicit_marker`,
`observed_floor`, অথবা মডেলটি না জানলে একটি সৎ `default`। একটি অনুমানের উপর
তৈরি গেজ কখনোই একটি লুকআপের উপর তৈরি গেজের মতো একই কর্তৃত্ব নিয়ে রেন্ডার হয় না।

ClawMetry শুধুমাত্র কিছু রানটাইমে কম্প্যাকশন ইভেন্ট দেখতে পারে। তাই
`GET /api/context-coverage` প্রতিটি রানটাইম অনুযায়ী রিপোর্ট করে যে **শূন্য মানে
"পরিষ্কারভাবে চলেছে" নাকি "আমরা অন্ধ"**। যে শূন্যের প্রকৃত অর্থ অন্ধ, সেটা তাই বলে।
[সম্পূর্ণ বিবরণ](docs/CONTEXT_BLOWOUT.md)

**ইনস্ট্রুমেন্টেশনের খরচ কত?**

| পথ | আপনার এজেন্টে যোগ হয় | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সব ৩০টি রানটাইম) | **০**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | চালু |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+০.৪৪ ms**, অর্থাৎ ৫s কলের ০.০০৯% | বন্ধ |
| প্রি-টুল হুক গেট (ওয়ার্ম ক্যাশে) | ৩৬ ms ইন্টারপ্রেটার ফ্লোরের উপর, প্রতি গেটেড টুল কলে **+৪৪ ms** | বন্ধ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+৯.৭ ms** | বন্ধ |

ডিমন হোস্ট খরচ: **২,৭৬২ ইভেন্ট/সেকেন্ড** ইনজেস্ট, ডিস্কে **৭১০ বাইট/ইভেন্ট**
(প্রতি ১ লাখ ইভেন্টে ৬৭.৭ MB), এবং ব্যস্ত ইনস্টলে টেকসইভাবে **এক কোরের প্রায় ১২%**।
সেই শেষ সংখ্যাটি আমাদের নিজস্ব ঘোষিত ৫-১০% বাজেটের চেয়ে বেশি, তাই এটি একটি
সমাধান করার বাগ হিসেবে প্রকাশিত হয়েছে, পাতা থেকে বাদ দেওয়া হয়নি।

Apple M2 Pro-তে `benchmarks/overhead.py` দিয়ে মাপা হয়েছে। হার্নেস প্রতিটি শর্তকে
আলাদা প্রসেসে চালায়, তাদের ক্রম পরিবর্তন করে, এবং **রাউন্ডগুলো তার চিহ্নের ব্যাপারে
একমত না হলে কোনো সংখ্যা প্রিন্ট করতে অস্বীকার করে**। এক মিনিটে আপনার নিজের মেশিনে
এটি চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

প্রতিটি পথ পরিমাপ করা হয়েছে, হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ, এবং হার্নেস
CI-তে Linux, macOS এবং Windows-এ চলে। জানার মতো দুটি ফলাফল: প্রক্সির খরচ Linux-এর
চেয়ে Windows-এ প্রায় সাতগুণ বেশি, এবং ডিমন বর্তমানে এক কোরের প্রায় ১২% টেকসইভাবে
ব্যবহার করে, যা আমাদের নিজস্ব ৫-১০% বাজেটের চেয়ে বেশি। কাঁচা JSON, পদ্ধতি, এবং
এখনও কী পরিমাপ করা হয়নি তা আছে [docs/OVERHEAD.md](docs/OVERHEAD.md)-এ।

## মূল্য নির্ধারণ

| প্ল্যান | এতে কী আছে | মূল্য |
|---|---|---|
| **ফ্রি** | OpenClaw + NVIDIA NemoClaw + Goose, সম্পূর্ণ ড্যাশবোর্ড, শুধুমাত্র লোকাল | $0 |
| **স্টার্টার** | উপরের বাকি প্রতিটি রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | নোড প্রতি / মাসে $9 |
| **Pro** | স্টার্টার + নিয়ন্ত্রণ ও মূল্যায়ন: অ্যাপ্রুভাল, টুল-রিস্ক পলিসি, ইভাল, অ্যানোমালি ডিটেকশন, কস্ট অপ্টিমাইজার, OTel এক্সপোর্ট, ট্যাম্পার-এভিডেন্ট অডিট লগ | নোড প্রতি / মাসে $19 |

বার্ষিক প্ল্যান, এন্টারপ্রাইজ এবং বর্তমান সংখ্যাগুলো আছে
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**-এ। সেলফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। সঠিক ফ্রি/পেইড বিভাজন
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-এ আছে।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry লোকাল সেশন ফাইল এবং লগ পড়ে। আপনি `clawmetry connect` না চালালে
**কোনো সেশন ডেটা আপনার বক্স থেকে বের হয় না** — কোনো প্রম্পট, রিপ্লাই, টুল আর্গুমেন্ট,
ফাইল কনটেন্ট বা লগ লাইন নয়। আপনি যখন কানেক্ট করেন, স্ন্যাপশটটি এন্ড-টু-এন্ড এনক্রিপ্টেড
থাকে এমন একটি কী দিয়ে যা কখনো আপনার মেশিন থেকে বের হয় না, এবং আপনার ব্রাউজারে
ডিক্রিপ্ট করা হয়। যদি একটি নোডের কোনো কী না থাকে, আপলোডটি স্কিপ করা হয় সাদামাটাভাবে
পাঠানোর পরিবর্তে, এবং কোনো সার্ভার রেসপন্স সেটা বন্ধ করে দিতে পারে না।

আপনি কানেক্ট করার আগেই ডিফল্টভাবে দুটি জিনিস চলে, দুটোই অপ্ট-আউট করা যায় এবং
কোনোটিতেই সেশন ডেটা থাকে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং PyPI-এর বিপরীতে
একটি ভার্সন চেক। একটি ডিফল্ট ইনস্টল স্টার্টআপ ব্যানার লাইনের জন্য একবার আপনার
পাবলিক IP-ও দেখে নেয়। প্রতিটি গন্তব্য, তা কী বহন করে এবং কীভাবে সেটা বন্ধ করবেন তার
তালিকা [docs/EGRESS.md](docs/EGRESS.md)-এ দেওয়া আছে; সেলফ-হোস্টেড, রিপয়েন্টেড এবং
এয়ার-গ্যাপড ইনস্টলগুলো একেবারেই কোনো ঐচ্ছিক আউটবাউন্ড কল করে না।

ডিক্রিপশনটি আপনার ব্রাউজারে ঘটে, আমরা আপনাকে যে কোড দিই তাতে। এটা আগে একটা
প্রতিশ্রুতি ছিল; এখন এটা এমন কিছু যা আপনি যাচাই করতে পারেন। আপনার কী স্পর্শ করে এমন
প্রতিটি লাইন একটি পড়ার-যোগ্য ফাইলে আছে, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা হুইলের ভেতরে শিপ করা হয় এবং হুবহু সার্ভ করা হয়, একটি Subresource
Integrity হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা যা প্রকাশ করেছি তাই চালায় কিনা তা
নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

এটি যা প্রমাণ করে না: আমরা সেই পেজ সার্ভ করি যা ফাইলটি লোড করে, তাই আমরা একটি
ভিন্ন পেজ সার্ভ করতে পারতাম। ইন্টেগ্রিটি হ্যাশ আপনাকে একটি আপোসকৃত CDN থেকে রক্ষা করে,
ভেন্ডর থেকে নয়। আপনি যা পান তা হলো, যেকোনো প্রতিস্থাপন ইচ্ছাকৃত হতে হবে, পেজ সোর্সে
দৃশ্যমান হতে হবে, এবং PyPI-তে থাকা একটি আর্টিফ্যাক্ট থেকে আলাদা হতে হবে যা যে কেউ
নিয়ে আসতে পারে। সেলফ-হোস্টিং বা শুধুমাত্র লোকাল থাকা এই নির্ভরতাকে সম্পূর্ণভাবে সরিয়ে দেয়।

## ইনস্টল

```bash
pip install clawmetry     # তারপর: clawmetry
```

অথবা এক-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ লাগে, এবং একই মেশিনে অন্তত একটি এজেন্ট
রানটাইম দরকার। Docker নির্দেশাবলী: [docs/DOCKER.md](docs/DOCKER.md)।

অথবা এজেন্টকেই আপনার জন্য সেটআপ করতে দিন। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
স্কিল Claude Code, Codex, Cursor, Gemini CLI, Copilot বা OpenCode-কে শেখায় কীভাবে
ClawMetry ইনস্টল করতে হয়, মেশিনে থাকা এজেন্টরা কী করছে এবং কী খরচ করছে তা রিপোর্ট
করতে হয়, অনুরোধে একটি সেশন থামাতে হয়, এবং অনুমোদনের জন্য ঝুঁকিপূর্ণ টুল কল ধরে রাখতে হয়:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ডকুমেন্টেশন

| | |
|---|---|
| [রানটাইম কম্প্যাটিবিলিটি](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং একটি রানটাইম যোগ করার উপায় |
| [কনটেক্সট ব্লোআউট](docs/CONTEXT_BLOWOUT.md) | প্রোভাইডার অনুযায়ী উইন্ডো, কম্প্যাকশন বনাম ওভারফ্লো, প্রতি-রানটাইম কভারেজ |
| [ওভারহেড](docs/OVERHEAD.md) | ইনস্ট্রুমেন্টেশনের খরচ কত, পরিমাপকৃত, পুনরুৎপাদনের হার্নেস সহ |
| [এনটাইটেলমেন্ট](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টিয়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [অ্যাপ্রুভাল ও পলিসি](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, রিস্ক স্কোরিং, ফোন অ্যাপ্রুভাল |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো কিছু থেকে OTLP ইনজেস্ট করুন |
| [নিজের এজেন্ট নিয়ে আসুন](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain এন্ড টু এন্ড, চালানোর মতো উদাহরণ সহ |
| [SDK ট্র্যাকিং](docs/SDK_TRACKING.md) | আপনি নিজে তৈরি করা এজেন্টদের জন্য খরচ অ্যাট্রিবিউশন |
| [চ্যাট চ্যানেল](docs/CHANNELS.md) | Flow-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [আর্কিটেকচার](ARCHITECTURE.md) · [ডেভেলপমেন্ট](docs/DEVELOPMENT.md) | ভেতরে এটি কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [টেলিমেট্রি](docs/TELEMETRY.md) | অ্যানোনিমাস ইনস্টল ও ডেস্কটপ-ওপেন পিং, এবং সেগুলো কীভাবে বন্ধ করবেন |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, শুধুমাত্র পড়ার জন্য, কিছুই বসিয়ে দেওয়া হয়নি।

**কিছু ভুল হলে এটি আপনাকে জানায়, শুধু কী ঘটেছে তা নয়।**
উপরে দুটি অ্যানোমালি ব্যানার: খরচ দৈনিক গড়ের ৭ গুণ চলছে, এবং একটি ৪.২x
কস্ট স্পাইক। তার নিচে, সাম্প্রতিক ৬৬৭টি সেশনের মধ্যে ৩২৪টি একটি অপচয়
সিগন্যাল বহন করছে, কারণ অনুযায়ী তালিকাভুক্ত।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটি প্রতিটি উইন্ডোতে দেখায় টাকা কোথায় গেছে।**
আজ $252.47, এই সপ্তাহে $513.15, এই মাসে $1,312.92, প্রতিটির পেছনের
টোকেনসহ এবং আপনার সাবস্ক্রিপশন ইতিমধ্যে তার কতটা কভার করে তা সহ। তার নিচে,
পুনরুদ্ধারযোগ্য হিসেবে আইটেমাইজড প্রায় $1,128/মাস এবং ক্যাশ পুনর্ব্যবহারের
মাধ্যমে ইতিমধ্যে সাশ্রয় হওয়া $17,256/মাস।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটি আঁকে কীভাবে একটি মেসেজ একটি উত্তরে পরিণত হয়।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, এটি যে চ্যানেলে এসেছে, গেটওয়ে, এখন উত্তর দিচ্ছে
এমন মডেল, এবং এটি যে প্রতিটি টুলের কাছে পৌঁছেছে। কাজ যখন তাদের মধ্য দিয়ে
চলে তখন নোডগুলো আলোকিত হয়।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনে থাকা প্রতিটি এজেন্ট, একটি টেবিলে।**
এটি কী চালায়, গত ২৪ ঘণ্টায় এবং সারাজীবনে এর খরচ কত, কখন এটি সর্বশেষ
দেখা গেছে, কে এটির মালিক, এবং একটি সাবস্ক্রিপশন বিলটি কভার করছে কিনা।
এখানে ১৪টি এজেন্ট, ৩টি সেশন কাজ করছে, ১৩টি শান্ত।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটি দেখায় একটি টার্নের সময় ও টাকা কোথায় গেছে, টুল বাই টুল।**
একটি বাস্তব সেশনের একটি টার্ন: ১১.২ মিনিটে ১১টি টুল, $1.16 খরচে। প্রতিটি
Bash কল এবং মডেল কল টাইমলাইনে নিজস্ব বার পায়, তাই ৪.১ মিনিট ধরে চলা
কমান্ড এবং ২২৬ms ধরে চলা কমান্ড এক নজরে আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটি কাজের গ্রেড দেয়, শুধু খরচের নয়।**
এই সপ্তাহে একটি A: ৫৪টি টাস্ক পরিষ্কারভাবে ফেরত এসেছে, ২টি খারাপ কাজ $48.57
খরচ করেছে, এবং যেসব রানে বিচার করার মতো যথেষ্ট কার্যকলাপ নেই সেগুলো জয়
হিসেবে গণনা না করে গ্রেড থেকে বাদ দেওয়া হয়েছে। প্রতিটি খারাপ রান তার
ট্রেসের সাথে লিঙ্ক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটি দেখায় কেন কনটেক্সট উইন্ডো ক্রমাগত ভরে যাচ্ছে।**
সাম্প্রতিক টার্নে ১M-টোকেন উইন্ডোর ৭১৫K, একটি ৮৩.৩% পিক, ৪টি কম্প্যাকশন যা
সবগুলোই ওভারফ্লোর পরিবর্তে সক্রিয়ভাবে ঘটেছে, এবং এর পেছনে প্রতিটি টার্নের
ব্যবহারের হার।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনার কিছু কনফিগার না করেই ডিটেকশন চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টল থেকেই চালু: এজেন্ট চুপ হয়ে গেছে, টেলিমেট্রি
ফিড বন্ধ হয়ে গেছে, কস্ট স্পাইক, টোকেন বার্স্ট, বাড়তে থাকা এরর, এরর স্পাইক,
বাজেট থ্রেশহোল্ড, থ্রেট সিগনেচার মিলেছে, সিকিউরিটি টুল ফাইন্ডিং, সিকিউরিটি
পোস্চার পরিবর্তিত হয়েছে। আপনার নিজের নিয়মগুলো এর উপরে ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ঝুঁকিপূর্ণ কল ধরে রাখা ঐচ্ছিক, এবং বন্ধ অবস্থায় শিপ হয়।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড কল
প্রতিটি একটি নিয়ম পায় যা আপনি চালু করতে পারেন। আপনি না করা পর্যন্ত,
ClawMetry শুধু দেখে এবং কিছুই বদলায় না। একটি চালু করা হলে, মিলে যাওয়া
কলগুলো এখানে (বা আপনার ফোনে) অনুমোদন বা প্রত্যাখ্যানের জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, প্রতিটি রানটাইম অনুযায়ী: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## স্বীকৃতি

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## লাইসেন্স

MIT · তৈরি করেছেন [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
