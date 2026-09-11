<!-- i18n-src:12b97259721e -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**একটি এজেন্ট কোনো অগ্রগতি ছাড়াই শতাধিক টুল কল করতে পারে।** ClawMetry
আপনার কোডিং এজেন্টগুলো যেসব সেশন ফাইল ইতিমধ্যে লেখে সেগুলো পড়ে, এবং টাইমলাইন,
টুল কলগুলো এবং রানটাইম যে টোকেন ও খরচের তথ্য প্রকাশ করে তা একটি একক
ভিউতে নিয়ে আসে — যাতে আপনি বুঝতে পারেন একটি দীর্ঘ রান কাজ করছে নাকি আটকে গেছে।

**৩১টি AI এজেন্ট রানটাইমের** সাথে কাজ করে — Claude Code, OpenAI Codex, Hermes, OpenClaw এবং আরও ২৭টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড। ([সম্পূর্ণ তালিকা](SUPPORTED_RUNTIMES.txt), ক্যাটালগ থেকে জেনারেট করা।)

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। শূন্য কনফিগারেশন। সবকিছু স্বয়ংক্রিয়ভাবে সনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে। শূন্য কনফিগারেশন: এটি আপনার কাছে থাকা
এজেন্ট রানটাইমগুলো খুঁজে বের করে, সেগুলো শুধু-পাঠ (read-only) অবস্থায় পড়ে, এবং সেগুলো
কীভাবে চলে তার কিছুই পরিবর্তন করে না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ইনস্টল করার আগে

| | |
|---|---|
| **এটি কী করে** | আপনার এজেন্টগুলো ইতিমধ্যে যে সেশন ফাইল এবং লগ লেখে তা পড়ে। কোনো SDK নেই, কোড পরিবর্তন নেই, আপনার অ্যাপে কোনো ইন্সট্রুমেন্টেশন নেই। |
| **আপনি কী দেখবেন** | সেশন টাইমলাইন, টুল-বাই-টুল রিপ্লে, টোকেন এবং খরচের বিশ্লেষণ, এবং ট্র্যাজেক্টরি সংকেত (লুপিং, বারবার ব্যর্থতা) — প্রতিটি রানটাইম অনুযায়ী। |
| **যা বিনামূল্যে** | `pip install clawmetry` কোনো অ্যাকাউন্ট, কী বা নেটওয়ার্ক কল ছাড়াই **OpenClaw, NVIDIA NemoClaw এবং Goose** পড়ে। বাকি ২৭টি — Claude Code, Codex, Cursor এবং অন্যান্য — ক্লোজড-সোর্স `clawmetry-pro` কম্প্যানিয়ন দ্বারা পড়া হয়, যা ৭-দিনের ট্রায়াল বা একটি প্ল্যানের সাথে আসে — সঠিক বিভাজনের জন্য দেখুন [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)। |
| **কীভাবে শুরু করবেন** | `pip install clawmetry && clawmetry`, তারপর localhost:8900 খুলুন। এই মেশিনে এখনো কোনো এজেন্ট নেই? `clawmetry --sample` তিনটি লেবেলযুক্ত সিন্থেটিক সেশনে খোলে। |
| **আপনার মেশিন থেকে কী বের হয়** | আপনি `clawmetry connect` না চালালে কোনো সেশন ডেটা বের হয় না। ডিফল্টভাবে দুটি জিনিস চলে, উভয়ই অপ্ট-আউট করা যায় এবং কোনোটিই সেশন কন্টেন্ট বহন করে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং একটি PyPI ভার্সন চেক। প্রতিটি গন্তব্যের তালিকা [docs/EGRESS.md](docs/EGRESS.md)-এ আছে, যা মন্তব্য পড়ার পরিবর্তে ওয়্যার ক্যাপচার থেকে পুনর্নির্মিত। |

আপনি আউটপুট বিচার করার আগে জানা উচিত এমন দুটি সীমাবদ্ধতা: রানটাইমগুলো অনেক
ভিন্ন ডেটা প্রকাশ করে (কিছু কোনো খরচই প্রকাশ করে না — [ম্যাট্রিক্স](docs/compatibility.md)
বলে দেয় কোনটি, রানটাইম অনুযায়ী), এবং একটি অ্যাকশন পর্যবেক্ষণ করা এবং সেটি ব্লক করতে
পারার মধ্যে পার্থক্য আছে ([কোন নিয়ন্ত্রণগুলো বাস্তব, রানটাইম অনুযায়ী](docs/APPROVALS.md))।


## ৩১টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে বিনামূল্যে:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**একটি পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে একাধিক চালান এবং হেডার
সুইচার প্রতিটি ট্যাবকে তাদের যেকোনো একটির উপর পুনরায় স্কোপ করে।

SDK দিয়ে নিজের এজেন্ট বানিয়েছেন? ইন্টারসেপ্টর সেটির LLM কলগুলোও ট্র্যাক করে।
দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি যা পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট কী করেছে, টার্ন বাই টার্ন, রিপ্লে সহ
- **খরচ ও টোকেন**: রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অসঙ্গতির চিহ্ন সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলের মধ্য দিয়ে চলমান মেসেজের লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং এবং টুল-কল ইভেন্ট স্ট্রিম, ঘটার সাথে সাথে
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী নির্ধারিত উইন্ডো সাইজ, কমপ্যাকশন বনাম জোরপূর্বক ওভারফ্লো, সেই সাথে আমরা *দেখতে পারি না* এমন একটি রানটাইম-ভিত্তিক মানচিত্র ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমরি ও স্কিল**: প্রতিটি রানটাইম আসলে যেসব ফাইল ও স্কিল লোড করেছে
- **স্বাস্থ্য ও লগ**: ডিস্ক, মেমরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email-এ রাউট করা
- **অনুমোদন**: ঝুঁকিপূর্ণ টুল কল চালানোর *আগে* থামিয়ে রাখুন এবং আপনার ফোন থেকে অনুমোদন দিন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ

যেকোনো এজেন্ট-তুলনাকারী টুলকে বিশ্বাস করার আগে উত্তর দেওয়ার যোগ্য দুটি প্রশ্ন।

**এটি বিভিন্ন রানটাইম জুড়ে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে হ্যান্ডেল করে?**

একটি ব্যবহারের শতাংশ ততটুকুই সৎ যতটা সৎ তার হর (denominator)। ClawMetry
প্রতিটি প্রোভাইডার অনুযায়ী উইন্ডোর আকার নির্ধারণ করে একটি টেবিল থেকে যা আপনি পড়তে ও
PR করতে পারেন ([clawmetry/context_windows.py](clawmetry/context_windows.py)), যা Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM কভার করে। এটি একটি ভেন্ডরের
স্কেল দিয়ে ৩১টি রানটাইমকে মাপে না। এটা গুরুত্বপূর্ণ: একটি 300K GPT-5 টার্নকে
Anthropic-এর 200K এর বিপরীতে স্কোর করলে ">100%, blown" দেখায়, অথচ প্রকৃতপক্ষে এটি
GPT-5-এর 400K এর ৭৫%। একই স্কেল সত্যিকারের ওভারফ্লো হওয়া একটি 130K DeepSeek
টার্নকে একটি আরামদায়ক ৬৫% হিসেবে লুকিয়ে রাখে।

প্রতিটি উইন্ডো তার উৎস (provenance) সহ আসে: `model_table`, `explicit_marker`,
`observed_floor`, অথবা মডেল না জানা থাকলে একটি সৎ `default`। একটি অনুমানের
উপর তৈরি গেজ কখনো একটি লুকআপের উপর তৈরি গেজের মতো একই কর্তৃত্ব নিয়ে দেখানো হয় না।

ClawMetry শুধুমাত্র কিছু রানটাইমে কমপ্যাকশন ইভেন্ট দেখতে পারে। তাই
`GET /api/context-coverage` প্রতিটি রানটাইম অনুযায়ী রিপোর্ট করে, একটি
শূন্য মানে **"পরিষ্কারভাবে চলেছে" নাকি "আমরা দেখতে পাচ্ছি না"**। একটি `0` যার প্রকৃত অর্থ
অন্ধ, সেটি তা বলে দেয়। [সম্পূর্ণ বিবরণ](docs/CONTEXT_BLOWOUT.md)

**ইন্সট্রুমেন্টেশনের খরচ কত?**

| পাথ | আপনার এজেন্টে যোগ হয় | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সব ৩১টি রানটাইম) | **০**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | চালু |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+০.৪৪ ms**, অর্থাৎ একটি 5s কলের ০.০০৯% | বন্ধ |
| প্রি-টুল হুক গেট (ওয়ার্ম ক্যাশে) | ৩৬ ms ইন্টারপ্রেটার ফ্লোরের উপর, প্রতি গেটেড টুল কলে **+৪৪ ms** | বন্ধ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+৯.৭ ms** | বন্ধ |

ডেমন হোস্ট খরচ: **২,৭৬২ ইভেন্ট/সেকেন্ড** ইনজেস্ট, ডিস্কে প্রতি ইভেন্টে **৭১০ বাইট**
(১০০k ইভেন্টে ৬৭.৭ MB), এবং ব্যস্ত ইনস্টলে টেকসইভাবে **এক কোরের প্রায় ১২%**।
এই শেষ সংখ্যাটি আমাদের নিজেদের ঘোষিত ৫-১০% বাজেটের চেয়ে বেশি, তাই এটি
পৃষ্ঠা থেকে বাদ দেওয়ার পরিবর্তে একটি তাড়া করার মতো বাগ হিসেবে প্রকাশ করা হয়েছে।

একটি Apple M2 Pro-তে `benchmarks/overhead.py` দিয়ে পরিমাপ করা। হার্নেস প্রতিটি
কন্ডিশন আলাদা প্রসেসে চালায়, তাদের ক্রম পরিবর্তন করে, এবং **যখন রাউন্ডগুলো তার
সাইনের ব্যাপারে একমত হয় না তখন একটি সংখ্যা প্রিন্ট করতে অস্বীকার করে**। এটি নিজের মেশিনে
এক মিনিটে চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

প্রতিটি পাথ মাপা হয়েছে, হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ, এবং হার্নেস
CI-তে Linux, macOS এবং Windows-এ চলে। জানার যোগ্য দুটি ফলাফল: প্রক্সিটি Windows-এ
Linux-এর তুলনায় প্রায় সাতগুণ বেশি খরচ করে, এবং ডেমন বর্তমানে টেকসইভাবে এক
কোরের প্রায় ১২% ব্যবহার করে, যা আমাদের নিজেদের ৫-১০% বাজেটের চেয়ে বেশি। র র JSON, পদ্ধতি,
এবং এখনো যা মাপা হয়নি তা [docs/OVERHEAD.md](docs/OVERHEAD.md)-এ আছে।

## মূল্য নির্ধারণ

| প্ল্যান | যা কভার করে | মূল্য |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, সম্পূর্ণ ড্যাশবোর্ড, শুধু স্থানীয় | $0 |
| **Starter** | উপরের প্রতিটি অন্যান্য রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | নোড প্রতি $9 / মাস |
| **Pro** | Starter + নিয়ন্ত্রণ এবং মূল্যায়ন: অনুমোদন, টুল-ঝুঁকি নীতি, evals, অসঙ্গতি সনাক্তকরণ, কস্ট অপ্টিমাইজার, OTel এক্সপোর্ট, টেম্পার-এভিডেন্ট অডিট লগ | নোড প্রতি $19 / মাস |

বার্ষিক প্ল্যান, Enterprise এবং বর্তমান সংখ্যাগুলো
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**-এ আছে। সেল্ফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। সঠিক ফ্রি/পেইড বিভাজন
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-এ আছে।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry স্থানীয় সেশন ফাইল এবং লগ পড়ে। **আপনি `clawmetry connect` না চালালে
আপনার বক্স থেকে কোনো সেশন ডেটা বের হয় না** — কোনো প্রম্পট, রিপ্লাই, টুল আর্গুমেন্ট, ফাইল
কন্টেন্ট বা লগ লাইন নয়। আপনি যখন কানেক্ট করেন, স্ন্যাপশটটি এন্ড-টু-এন্ড এনক্রিপ্টেড
করা হয় এমন একটি কী দিয়ে যা কখনো আপনার মেশিন ছেড়ে যায় না, এবং আপনার ব্রাউজারে ডিক্রিপ্ট করা হয়।
কোনো নোডের যদি কোনো কী না থাকে, আপলোডটি স্কিপ করা হয় পরিষ্কার টেক্সটে পাঠানোর পরিবর্তে,
এবং কোনো সার্ভার রেসপন্স সেটি বন্ধ করতে পারে না।

আপনি কানেক্ট করার আগে ডিফল্টভাবে দুটি জিনিস চলে, উভয়ই অপ্ট-আউট করা যায় এবং
কোনোটিই সেশন ডেটা বহন করে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং PyPI-এর বিরুদ্ধে
একটি ভার্সন চেক। একটি ডিফল্ট ইনস্টল স্টার্টআপ ব্যানার লাইনের জন্য একবার আপনার
পাবলিক IP-ও লুকআপ করে। প্রতিটি গন্তব্য, এটি কী বহন করে এবং কীভাবে সেটি বন্ধ করবেন তার
তালিকা [docs/EGRESS.md](docs/EGRESS.md)-এ আছে; সেল্ফ-হোস্টেড, রিপয়েন্টেড এবং এয়ার-গ্যাপড
ইনস্টলগুলো একেবারেই কোনো ঐচ্ছিক আউটবাউন্ড কল করে না।

ডিক্রিপশনটি আপনার ব্রাউজারে ঘটে, আমরা আপনাকে যে কোড দিই তাতে। এটি আগে
একটি প্রতিশ্রুতি ছিল; এখন এটি এমন কিছু যা আপনি যাচাই করতে পারেন। আপনার কী স্পর্শ করা প্রতিটি
লাইন একটি পাঠযোগ্য ফাইলে থাকে, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা হুইলের ভেতরে শিপ হয় এবং যেমন আছে তেমনভাবে সার্ভ করা হয়, একটি সাবরিসোর্স
ইন্টেগ্রিটি হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা যা প্রকাশ করেছি তা চালাচ্ছে কিনা তা নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

এটি যা প্রমাণ করে না: আমরা সেই পেজ সার্ভ করি যেটি ফাইলটি লোড করে, তাই আমরা
একটি ভিন্ন পেজ সার্ভ করতে পারি। ইন্টেগ্রিটি হ্যাশ আপনাকে একটি আপোসকৃত CDN থেকে
রক্ষা করে, ভেন্ডর থেকে নয়। আপনি যা পান তা হলো যেকোনো প্রতিস্থাপন ইচ্ছাকৃত,
পেজ সোর্সে দৃশ্যমান, এবং PyPI-এর একটি আর্টিফ্যাক্ট থেকে ভিন্ন হতে হবে যা যে কেউ
ফেচ করতে পারে। সেল্ফ-হোস্টিং বা শুধু-স্থানীয় থাকা এই নির্ভরতা সম্পূর্ণরূপে দূর করে।

## ইনস্টল

```bash
pip install clawmetry     # তারপর: clawmetry
```

অথবা ওয়ান-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ প্রয়োজন, এবং একই মেশিনে অন্তত একটি
এজেন্ট রানটাইম। Docker নির্দেশাবলী: [docs/DOCKER.md](docs/DOCKER.md)।

অথবা এজেন্টকে আপনার জন্য এটি সেটআপ করতে দিন। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
স্কিলটি Claude Code, Codex, Cursor, Gemini CLI, Copilot বা OpenCode-কে শেখায়
ClawMetry ইনস্টল করতে, মেশিনের এজেন্টগুলো কী করছে এবং কী খরচ করছে তা রিপোর্ট করতে,
অনুরোধে একটি সেশন থামাতে, এবং অনুমোদনের জন্য ঝুঁকিপূর্ণ টুল কল ধরে রাখতে:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ডকুমেন্টেশন

| | |
|---|---|
| [রানটাইম সামঞ্জস্যতা](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং কীভাবে একটি রানটাইম যোগ করবেন |
| [কনটেক্সট ব্লোআউট](docs/CONTEXT_BLOWOUT.md) | প্রোভাইডার-প্রতি উইন্ডো, কমপ্যাকশন বনাম ওভারফ্লো, রানটাইম-প্রতি কভারেজ |
| [ওভারহেড](docs/OVERHEAD.md) | ইন্সট্রুমেন্টেশনের খরচ কত, পরিমাপ করা, পুনরুৎপাদনের হার্নেস সহ |
| [এনটাইটেলমেন্ট](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টায়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [অনুমোদন ও নীতি](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, ঝুঁকি স্কোরিং, ফোন অনুমোদন |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো জায়গা থেকে OTLP ইনজেস্ট করুন |
| [নিজের এজেন্ট নিয়ে আসুন](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain এন্ড টু এন্ড, চালানোর যোগ্য উদাহরণ সহ |
| [SDK ট্র্যাকিং](docs/SDK_TRACKING.md) | নিজের তৈরি এজেন্টগুলোর জন্য খরচ অ্যাট্রিবিউশন |
| [চ্যাট চ্যানেল](docs/CHANNELS.md) | Flow-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [আর্কিটেকচার](ARCHITECTURE.md) · [ডেভেলপমেন্ট](docs/DEVELOPMENT.md) | ভেতরে কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [টেলিমেট্রি](docs/TELEMETRY.md) | অ্যানোনিমাস ইনস্টল এবং ডেস্কটপ-ওপেন পিং, এবং কীভাবে সেগুলো বন্ধ করবেন |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, শুধু-পাঠ (read-only), কিছু সিড না করে।

**এটি আপনাকে বলে দেয় কখন কিছু ভুল হয়েছে, শুধু কী ঘটেছে তা নয়।**
উপরে দুটি অসঙ্গতি ব্যানার: দৈনিক গড়ের ৭ গুণ খরচ চলছে, এবং একটি
৪.২ গুণ কস্ট স্পাইক। তার নিচে, সাম্প্রতিক ৬৬৭টি সেশনের মধ্যে ৩২৪টি একটি অপচয়ের
সংকেত বহন করছে, কারণ অনুযায়ী বিভক্ত।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটি আপনাকে দেখায় টাকা কোথায় গেছে, প্রতিটি সময়সীমায়।**
আজ $252.47, এই সপ্তাহে $513.15, এই মাসে $1,312.92, প্রতিটির পেছনের টোকেন
এবং আপনার সাবস্ক্রিপশন ইতিমধ্যে কতটা কভার করে তার সাথে। তার নিচে,
প্রায় $1,128/মাস উদ্ধারযোগ্য হিসেবে তালিকাভুক্ত এবং ক্যাশ পুনর্ব্যবহারের মাধ্যমে ইতিমধ্যে
$17,256/মাস সাশ্রয় হয়েছে।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটি আঁকে কীভাবে একটি মেসেজ একটি উত্তরে পরিণত হয়।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, যে চ্যানেলে এটি এসেছে, গেটওয়ে, এখন উত্তর দিচ্ছে এমন
মডেল, এবং এটি যে প্রতিটি টুল ব্যবহার করেছে। কাজ তাদের মধ্য দিয়ে যাওয়ার সাথে সাথে
নোডগুলো আলোকিত হয়।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনের প্রতিটি এজেন্ট, একটি টেবিলে।**
এটি কী চালায়, গত ২৪ ঘণ্টায় এবং তার লাইফটাইমে এটি কত খরচ করে, কখন
এটি শেষবার দেখা গেছে, কার মালিকানাধীন, এবং একটি সাবস্ক্রিপশন বিলটি কভার করছে কিনা। এখানে
১৪টি এজেন্ট, ৩টি সেশন কাজ করছে, ১৩টি শান্ত।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটি দেখায় একটি টার্নের সময় এবং টাকা কোথায় গেছে, টুল বাই টুল।**
একটি বাস্তব সেশনের একটি টার্ন: ১১.২ মিনিটে ১১টি টুল, $1.16 খরচে। প্রতিটি Bash
কল এবং মডেল কল টাইমলাইনে নিজস্ব বার পায়, যাতে ৪.১ মিনিট চলা কমান্ড এবং
২২৬ms চলা কমান্ডটি এক নজরে আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটি কাজের মান দেয়, শুধু খরচ নয়।**
এই সপ্তাহে একটি A: ৫৪টি টাস্ক পরিষ্কারভাবে সম্পন্ন হয়েছে, ২টি রুক্ষ কাজে
$48.57 খরচ হয়েছে, এবং বিচার করার মতো যথেষ্ট কার্যকলাপ নেই এমন রানগুলো
জয় হিসেবে গণনা না করে গ্রেড থেকে বাদ দেওয়া হয়েছে। প্রতিটি রুক্ষ রান তার ট্রেসের সাথে
লিঙ্ক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটি দেখায় কেন কনটেক্সট উইন্ডো ক্রমাগত পূর্ণ হয়ে যাচ্ছে।**
সাম্প্রতিক টার্নে 1M-টোকেন উইন্ডোর 715K ব্যবহৃত, একটি ৮৩.৩% পিক, ৪টি কমপ্যাকশন
যেগুলো সবই ওভারফ্লোর পরিবর্তে প্রোঅ্যাক্টিভলি ফায়ার করেছে, এবং তার পেছনে প্রতিটি টার্নের
ব্যবহারের হার।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনার কোনো কনফিগারেশন ছাড়াই ডিটেকশন চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টল থেকেই চালু থাকে: এজেন্ট চুপ হয়ে গেছে, টেলিমেট্রি ফিড
বন্ধ হয়ে গেছে, কস্ট স্পাইক, টোকেন বার্স্ট, এরর বাড়ছে, এরর স্পাইক, বাজেট
থ্রেশহোল্ড, থ্রেট সিগনেচার মিলেছে, সিকিউরিটি টুল ফাইন্ডিং, সিকিউরিটি পোস্চার
পরিবর্তিত হয়েছে। আপনার নিজস্ব নিয়মগুলো এর উপরে ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ঝুঁকিপূর্ণ কল ধরে রাখা অপ্ট-ইন, এবং বন্ধ অবস্থায় শিপ হয়।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড
কলের প্রতিটির জন্য একটি নিয়ম আছে যা আপনি চালু করতে পারেন। যতক্ষণ না আপনি করেন,
ততক্ষণ ClawMetry দেখতে থাকে এবং কিছুই পরিবর্তন করে না। একটি চালু হলে, মিলে যাওয়া
কলগুলো এখানে (অথবা আপনার ফোনে) অনুমোদন বা প্রত্যাখ্যানের জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, প্রতিটি রানটাইম অনুযায়ী: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

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
