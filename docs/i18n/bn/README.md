<!-- i18n-src:a855a14295b0 -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**একটি এজেন্ট অগ্রগতি না করেই শতাধিক টুল কল করতে পারে।** ClawMetry
আপনার কোডিং এজেন্টরা যে সেশন ফাইলগুলো ইতিমধ্যে লিখে রাখে সেগুলো পড়ে, এবং টাইমলাইন,
টুল কল এবং রানটাইম যে টোকেন ও খরচের তথ্য প্রকাশ করে তা এক জায়গায় নিয়ে আসে —
যাতে আপনি বুঝতে পারেন কোন দীর্ঘ রান কাজ করছে আর কোনটা আটকে গেছে।

**৩২টি AI এজেন্ট রানটাইমের** সাথে কাজ করে — Claude Code, OpenAI Codex, Hermes, OpenClaw এবং আরও ২৮টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড। ([সম্পূর্ণ তালিকা](SUPPORTED_RUNTIMES.txt), ক্যাটালগ থেকে জেনারেট করা।)

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। কোনো কনফিগারেশন লাগে না। সবকিছু নিজে থেকেই শনাক্ত করে নেয়।

```bash
pip install clawmetry && clawmetry
```

খোলে **http://localhost:8900** এ। কোনো কনফিগারেশন লাগে না: এটি আপনার কাছে ইতিমধ্যে থাকা এজেন্ট রানটাইমগুলো খুঁজে বের করে, সেগুলো শুধু পড়ে (read-only), এবং সেগুলো কীভাবে চলছে তাতে কোনো পরিবর্তন করে না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ইনস্টল করার আগে

| | |
|---|---|
| **এটি কী করে** | আপনার এজেন্টরা ইতিমধ্যে যে সেশন ফাইল এবং লগ লিখে রাখে সেগুলো পড়ে। কোনো SDK নেই, কোডে কোনো পরিবর্তন নেই, আপনার অ্যাপে কোনো ইনস্ট্রুমেন্টেশন নেই। |
| **আপনি কী দেখবেন** | সেশন টাইমলাইন, টুল-বাই-টুল রিপ্লে, টোকেন ও খরচের বিভাজন, এবং ট্র্যাজেক্টরি সংকেত (লুপিং, বারবার ব্যর্থতা) — প্রতিটি রানটাইম অনুযায়ী। |
| **যা বিনামূল্যে** | `pip install clawmetry` কোনো অ্যাকাউন্ট, কী বা নেটওয়ার্ক কল ছাড়াই **OpenClaw, NVIDIA NemoClaw এবং Goose** পড়তে পারে। বাকি ২৭টি — Claude Code, Codex, Cursor এবং অন্যান্য — ক্লোজড-সোর্স `clawmetry-pro` কম্প্যানিয়ন দিয়ে পড়া হয়, যা ৭ দিনের ট্রায়াল বা প্ল্যানের সাথে আসে — সঠিক বিভাজনের জন্য দেখুন [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)। |
| **কীভাবে শুরু করবেন** | `pip install clawmetry && clawmetry`, তারপর localhost:8900 খুলুন। এই মেশিনে এখনও কোনো এজেন্ট নেই? `clawmetry --sample` তিনটি লেবেলযুক্ত সিন্থেটিক সেশনে খোলে। |
| **আপনার মেশিন থেকে কী বের হয়** | কোনো সেশন ডেটা নয়, যতক্ষণ না আপনি `clawmetry connect` চালান। ডিফল্টভাবে দুটি জিনিস চলে, দুটোই অপ্ট-আউট করা যায় এবং কোনোটিতেই সেশন কনটেন্ট থাকে না: একটি বেনামী ইনস্টল পিং এবং একটি PyPI ভার্সন চেক। প্রতিটি গন্তব্য [docs/EGRESS.md](docs/EGRESS.md)-এ তালিকাভুক্ত, যা মন্তব্য পড়ার পরিবর্তে ওয়্যার ক্যাপচার থেকে তৈরি। |

বিচার করার আগে জানা দরকার এমন দুটি সীমাবদ্ধতা: রানটাইমগুলো খুবই ভিন্ন ভিন্ন ডেটা প্রকাশ করে (কিছু কোনো খরচই প্রকাশ করে না — [ম্যাট্রিক্স](docs/compatibility.md) বলে দেয় কোনটি, রানটাইম অনুযায়ী), এবং একটি অ্যাকশন পর্যবেক্ষণ করা এবং সেটা আটকাতে পারা এক জিনিস নয় ([কোন নিয়ন্ত্রণগুলো বাস্তব, রানটাইম অনুযায়ী](docs/APPROVALS.md))।


## ৩২টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে বিনামূল্যে:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে একাধিক চালান এবং হেডার সুইচার প্রতিটি ট্যাবকে তাদের যেকোনো একটির সাথে পুনরায় সাজিয়ে দেবে।

SDK দিয়ে নিজের এজেন্ট বানিয়েছেন? ইন্টারসেপ্টর তারও LLM কল ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি কী পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট কী করেছে, টার্ন বাই টার্ন, রিপ্লে সহ
- **খরচ ও টোকেন**: রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অস্বাভাবিকতার ফ্ল্যাগ সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলগুলোর মধ্য দিয়ে চলমান বার্তার লাইভ ডায়াগ্রাম
- **ব্রেইন**: যেভাবে ঘটছে সেভাবেই রিজনিং এবং টুল-কল ইভেন্ট স্ট্রিম
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী উইন্ডো সাইজ, কম্প্যাকশন বনাম জোরপূর্বক ওভারফ্লো, সাথে আমরা যা *দেখতে পারি না* তার একটি রানটাইম-ভিত্তিক ম্যাপ ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমরি ও স্কিল**: প্রতিটি রানটাইম আসলে যে ফাইল ও স্কিল লোড করেছে
- **স্বাস্থ্য ও লগ**: ডিস্ক, মেমরি, এরর হার, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email-এ পাঠানো হয়
- **অনুমোদন**: ঝুঁকিপূর্ণ টুল কল চলার *আগে* থামান এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ

যেকোনো এজেন্ট-তুলনা টুলকে বিশ্বাস করার আগে জানা দরকার এমন দুটি প্রশ্ন।

**এটি রানটাইমজুড়ে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে সামলায়?**

একটি ইউটিলাইজেশন শতাংশ যতটা সৎ, তা নির্ভর করে সেটা কী দিয়ে ভাগ করা হচ্ছে তার উপর। ClawMetry
[একটি টেবিল থেকে](clawmetry/context_windows.py) প্রতিটি প্রোভাইডার অনুযায়ী উইন্ডোর আকার নির্ধারণ করে,
যা আপনি পড়তে ও PR করতে পারেন, এবং যাতে রয়েছে Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM। এটি ৩২টি রানটাইমকেই একটি ভেন্ডরের মাপকাঠি দিয়ে
মাপে না। এটা গুরুত্বপূর্ণ: Anthropic-এর ২০০K এর বিপরীতে মাপা একটি ৩০০K GPT-5 টার্ন
">১০০%, ব্লোন" দেখায়, যেখানে বাস্তবে এটি GPT-5-এর ৪০০K-এর ৭৫%। একই মাপকাঠি
একটি প্রকৃতপক্ষে ওভারফ্লো হওয়া ১৩০K DeepSeek টার্নকে একটি স্বস্তিদায়ক ৬৫% হিসেবে লুকিয়ে ফেলে।

প্রতিটি উইন্ডোর সাথে তার উৎস থাকে: `model_table`, `explicit_marker`,
`observed_floor`, অথবা মডেল না জানা থাকলে একটি সৎ `default`। অনুমানের উপর
তৈরি একটি গেজ কখনোই লুকআপের উপর তৈরি গেজের মতো একই কর্তৃত্ব নিয়ে রেন্ডার হয় না।

ClawMetry শুধু কিছু রানটাইমে কম্প্যাকশন ইভেন্ট দেখতে পারে। তাই
`GET /api/context-coverage` রিপোর্ট করে, প্রতিটি রানটাইম অনুযায়ী, একটি **শূন্য মানে
"পরিষ্কারভাবে চলেছে" নাকি "আমরা অন্ধ"**। যে `0` আসলে অন্ধত্ব বোঝায় তা তেমনই বলে।
[বিস্তারিত](docs/CONTEXT_BLOWOUT.md)

**ইনস্ট্রুমেন্টেশনের খরচ কত?**

| পথ | আপনার এজেন্টে যোগ হয় | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সব ৩২টি রানটাইম) | **০**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | চালু |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+০.৪৪ ms**, অথবা ৫s কলের ০.০০৯% | বন্ধ |
| প্রি-টুল হুক গেট (ওয়ার্ম ক্যাশে) | ৩৬ ms ইন্টারপ্রেটার ফ্লোরের উপর প্রতি গেটেড টুল কলে **+৪৪ ms** | বন্ধ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+৯.৭ ms** | বন্ধ |

ডেমন হোস্ট খরচ: **২,৭৬২ ইভেন্ট/সেকেন্ড** ইনজেস্ট, ডিস্কে **৭১০ বাইট/ইভেন্ট**
(১ লক্ষ ইভেন্টে ৬৭.৭ MB), এবং একটি ব্যস্ত ইনস্টলে ক্রমাগত **এক কোরের প্রায় ১২%**। সেই
শেষ সংখ্যাটি আমাদের নিজস্ব ৫-১০% বাজেটের চেয়ে বেশি, তাই এটি পাতা থেকে বাদ দেওয়ার বদলে
তাড়া করার মতো একটি বাগ হিসেবে প্রকাশিত হয়েছে।

Apple M2 Pro-তে `benchmarks/overhead.py` দিয়ে পরিমাপ করা। হার্নেস প্রতিটি শর্তকে
একটি আলাদা প্রসেসে চালায়, তাদের ক্রম পাল্টায়, এবং **রাউন্ডগুলো এর চিহ্ন নিয়ে একমত না হলে
কোনো সংখ্যা প্রিন্ট করতে অস্বীকার করে**। আপনার নিজের মেশিনে এক মিনিটে চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

প্রতিটি পথ পরিমাপ করা হয়েছে, হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ,
এবং হার্নেস CI-তে Linux, macOS এবং Windows-এ চলে। জানার মতো দুটি ফলাফল:
প্রক্সিটি Windows-এ Linux-এর তুলনায় প্রায় সাত গুণ বেশি খরচ করে, এবং
ডেমন বর্তমানে এক কোরের প্রায় ১২% বজায় রাখে, যা আমাদের নিজস্ব ৫-১০%
বাজেটের চেয়ে বেশি। কাঁচা JSON, পদ্ধতি, এবং এখনও যা পরিমাপ করা হয়নি তা রয়েছে
[docs/OVERHEAD.md](docs/OVERHEAD.md)-এ।

## মূল্য নির্ধারণ

| প্ল্যান | এতে কী অন্তর্ভুক্ত | মূল্য |
|---|---|---|
| **ফ্রি** | OpenClaw + NVIDIA NemoClaw + Goose, সম্পূর্ণ ড্যাশবোর্ড, শুধু লোকাল | $0 |
| **স্টার্টার** | উপরের বাকি সব রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | নোড প্রতি $9 / মাস |
| **Pro** | স্টার্টার + নিয়ন্ত্রণ ও মূল্যায়ন: অনুমোদন, টুল-ঝুঁকি নীতি, evals, অস্বাভাবিকতা শনাক্তকরণ, খরচ অপটিমাইজার, OTel এক্সপোর্ট, টেম্পার-এভিডেন্ট অডিট লগ | নোড প্রতি $19 / মাস |

বার্ষিক প্ল্যান, এন্টারপ্রাইজ এবং বর্তমান সংখ্যাগুলো রয়েছে
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**-এ। সেলফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। ফ্রি/পেইড বিভাজনের সঠিক বিবরণ রয়েছে
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-এ।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry লোকাল সেশন ফাইল এবং লগ পড়ে। **আপনি `clawmetry connect` না চালানো পর্যন্ত
কোনো সেশন ডেটা আপনার মেশিন থেকে বের হয় না** — কোনো প্রম্পট, রিপ্লাই, টুল আর্গুমেন্ট, ফাইল
কনটেন্ট বা লগ লাইন নয়। আপনি যখন কানেক্ট করেন, স্ন্যাপশট এমন একটি কী দিয়ে এন্ড-টু-এন্ড এনক্রিপ্ট
করা হয় যা কখনো আপনার মেশিন ছেড়ে যায় না, এবং আপনার ব্রাউজারে ডিক্রিপ্ট হয়। যদি কোনো
নোডের কোনো কী না থাকে, আপলোডটি সাদামাটাভাবে পাঠানোর বদলে বাদ দেওয়া হয়, এবং কোনো
সার্ভার রেসপন্সই এটা বন্ধ করতে পারে না।

কানেক্ট করার আগে ডিফল্টভাবে দুটি জিনিস চলে, দুটোই অপ্ট-আউট করা যায় এবং কোনোটিতেই
সেশন ডেটা থাকে না: একটি বেনামী ইনস্টল পিং এবং PyPI-এর বিপরীতে একটি ভার্সন চেক। একটি
ডিফল্ট ইনস্টল স্টার্টআপ ব্যানার লাইনের জন্য আপনার পাবলিক IP একবার লুকআপও করে। প্রতিটি
গন্তব্য, তা কী বহন করে এবং কীভাবে বন্ধ করা যায় তা তালিকাভুক্ত রয়েছে
[docs/EGRESS.md](docs/EGRESS.md)-এ; সেলফ-হোস্টেড, রি-পয়েন্টেড এবং এয়ার-গ্যাপড ইনস্টলগুলো
কোনো ঐচ্ছিক আউটবাউন্ড কল করে না।

ডিক্রিপশন আপনার ব্রাউজারে হয়, এমন কোডে যা আমরা আপনাকে সার্ভ করি। এটা আগে একটা
প্রতিশ্রুতি ছিল; এখন এটা এমন কিছু যা আপনি যাচাই করতে পারেন। আপনার কী স্পর্শ করে এমন
প্রতিটি লাইন একটি পড়ার-যোগ্য ফাইলে থাকে, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা wheel-এর ভেতরে থাকে এবং একদম সেভাবেই সার্ভ করা হয়, একটি Subresource
Integrity হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা যা প্রকাশ করেছি তাই চালাচ্ছে কিনা তা নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

এটা যা প্রমাণ করে না: আমরাই সেই পেজ সার্ভ করি যা ফাইলটি লোড করে, তাই আমরা একটি
ভিন্ন পেজ সার্ভ করতে পারতাম। ইন্টেগ্রিটি হ্যাশ আপনাকে একটি কম্প্রোমাইজড CDN থেকে রক্ষা
করে, ভেন্ডর থেকে নয়। আপনি যা পান তা হলো, যেকোনো প্রতিস্থাপন ইচ্ছাকৃত হতে হবে, পেজ
সোর্সে দৃশ্যমান হতে হবে, এবং PyPI-এর একটি আর্টিফ্যাক্ট থেকে আলাদা হতে হবে যা যে কেউ
আনতে পারে। সেলফ-হোস্টিং বা শুধু লোকাল থাকা এই নির্ভরতাকে সম্পূর্ণরূপে সরিয়ে দেয়।

## ইনস্টল

```bash
pip install clawmetry     # তারপর: clawmetry
```

অথবা এক-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ দরকার, এবং একই মেশিনে অন্তত একটি এজেন্ট
রানটাইম দরকার। Docker নির্দেশনা: [docs/DOCKER.md](docs/DOCKER.md)।

অথবা এজেন্টকেই এটা সেটআপ করতে দিন। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
স্কিলটি Claude Code, Codex, Cursor, Gemini CLI, Copilot বা OpenCode-কে
ClawMetry ইনস্টল করতে, মেশিনের এজেন্টরা কী করছে ও খরচ করছে তা রিপোর্ট করতে,
অনুরোধে একটি সেশন থামাতে, এবং ঝুঁকিপূর্ণ টুল কল অনুমোদনের জন্য আটকে রাখতে শেখায়:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ডকুমেন্টেশন

| | |
|---|---|
| [রানটাইম কম্প্যাটিবিলিটি](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং কীভাবে একটি রানটাইম যোগ করবেন |
| [কনটেক্সট ব্লোআউট](docs/CONTEXT_BLOWOUT.md) | প্রোভাইডার-ভিত্তিক উইন্ডো, কম্প্যাকশন বনাম ওভারফ্লো, রানটাইম-ভিত্তিক কভারেজ |
| [ওভারহেড](docs/OVERHEAD.md) | ইনস্ট্রুমেন্টেশনের খরচ কত, পরিমাপ করা, পুনরুৎপাদনের হার্নেস সহ |
| [Entitlements](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টিয়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [অনুমোদন ও নীতি](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, ঝুঁকি স্কোরিং, ফোন অনুমোদন |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো কিছু থেকে OTLP ইনজেস্ট করুন |
| [নিজের এজেন্ট আনুন](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain এন্ড টু এন্ড, চালানোর যোগ্য উদাহরণ সহ |
| [SDK ট্র্যাকিং](docs/SDK_TRACKING.md) | আপনি নিজে বানানো এজেন্টগুলোর জন্য খরচ অ্যাট্রিবিউশন |
| [চ্যাট চ্যানেল](docs/CHANNELS.md) | ফ্লো-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [আর্কিটেকচার](ARCHITECTURE.md) · [ডেভেলপমেন্ট](docs/DEVELOPMENT.md) | ভেতরে এটা কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [টেলিমেট্রি](docs/TELEMETRY.md) | বেনামী ইনস্টল এবং ডেস্কটপ-ওপেন পিং, এবং কীভাবে সেগুলো বন্ধ করবেন |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, শুধু-পড়ার (read-only), কিছু ছাড়াই।

**এটি আপনাকে বলে কখন কিছু ভুল, শুধু কী ঘটেছে তা নয়।**
উপরে দুটি অ্যানোমালি ব্যানার: দৈনিক গড়ের ৭ গুণ খরচ চলছে, এবং একটি
৪.২x খরচ স্পাইক। তাদের নিচে, সাম্প্রতিক ৬৬৭টি সেশনের মধ্যে ৩২৪টিতে একটি অপচয়
সংকেত রয়েছে, কারণ অনুযায়ী বিস্তারিত।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটি দেখায় টাকা কোথায় গেছে, প্রতিটি উইন্ডোতে।**
আজ $252.47, এই সপ্তাহে $513.15, এই মাসে $1,312.92, প্রতিটির পেছনের টোকেন
এবং আপনার সাবস্ক্রিপশন ইতিমধ্যে তার কতটা কভার করে সহ। তার নিচে, প্রায় $1,128/মাস
পুনরুদ্ধারযোগ্য হিসেবে বিস্তারিত এবং ক্যাশ পুনর্ব্যবহারের মাধ্যমে ইতিমধ্যে $17,256/মাস সাশ্রয়।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটি আঁকে একটি বার্তা কীভাবে উত্তর হয়ে ওঠে।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, যে চ্যানেলে এটি এসেছে, গেটওয়ে, এই মুহূর্তে
উত্তর দিচ্ছে এমন মডেল, এবং যে প্রতিটি টুলের কাছে এটি গেছে। কাজ যতই এগোয়, নোডগুলো
তত জ্বলে ওঠে।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনের প্রতিটি এজেন্ট, একটি টেবিলে।**
এটি কী চালায়, গত ২৪ ঘণ্টায় এবং সারাজীবনে এর খরচ কত, শেষ কখন দেখা গেছে,
কে এর মালিক, এবং একটি সাবস্ক্রিপশন বিলটা কভার করছে কিনা। এখানে ১৪টি এজেন্ট,
৩টি সেশন কাজ করছে, ১৩টি নিশ্চুপ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটি দেখায় একটি টার্নের সময় ও অর্থ কোথায় গেছে, টুল বাই টুল।**
একটি বাস্তব সেশনের একটি টার্ন: ১১.২ মিনিটে $1.16 খরচে ১১টি টুল। প্রতিটি
Bash কল এবং মডেল কল টাইমলাইনে নিজস্ব বার পায়, তাই ৪.১ মিনিট ধরে চলা কমান্ড আর
২২৬ms ধরে চলা কমান্ডকে এক নজরেই আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটি কাজের গ্রেড দেয়, শুধু খরচের নয়।**
এই সপ্তাহে একটি A: ৫৪টি টাস্ক পরিষ্কারভাবে ফিরে এসেছে, ২টি খারাপ কাজের খরচ
$48.57, এবং বিচার করার মতো যথেষ্ট কার্যকলাপ নেই এমন রানগুলো জয় হিসেবে গণনা
না করে গ্রেড থেকে বাদ দেওয়া হয়েছে। প্রতিটি খারাপ রান তার ট্রেসের সাথে লিঙ্ক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটি দেখায় কেন কনটেক্সট উইন্ডো ক্রমাগত ভরে যাচ্ছে।**
সর্বশেষ টার্নে ১M-টোকেন উইন্ডোর মধ্যে ৭১৫K, একটি ৮৩.৩% শীর্ষ, ৪টি কম্প্যাকশন
যা সবগুলোই ওভারফ্লোর বদলে সক্রিয়ভাবে চালু হয়েছে, সাথে তার পেছনের প্রতিটি টার্নের
ইউটিলাইজেশন।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনার কোনো কনফিগারেশন ছাড়াই শনাক্তকরণ চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টল থেকেই চালু থাকে: এজেন্ট নিশ্চুপ হয়ে গেছে, টেলিমেট্রি ফিড
থেমে গেছে, খরচ স্পাইক, টোকেন বার্স্ট, এরর বাড়ছে, এরর স্পাইক, বাজেট
থ্রেশহোল্ড, থ্রেট সিগনেচার মিলেছে, সিকিউরিটি টুল ফাইন্ডিং, সিকিউরিটি অবস্থানে
পরিবর্তন। এর উপরে আপনার নিজস্ব নিয়মগুলো ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**একটি ঝুঁকিপূর্ণ কল আটকে রাখা ঐচ্ছিক, এবং বন্ধ অবস্থায় শিপ হয়।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড
কল প্রতিটিরই একটি নিয়ম রয়েছে যা আপনি চালু করতে পারেন। আপনি না করা পর্যন্ত, ClawMetry
শুধু দেখে এবং কিছুই পরিবর্তন করে না। একবার একটি চালু হলে, মিলে যাওয়া কলগুলো এখানে
(অথবা আপনার ফোনে) অনুমোদন বা প্রত্যাখ্যানের জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, রানটাইম অনুযায়ী: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## স্বীকৃতি

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## স্টার হিস্ট্রি

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
