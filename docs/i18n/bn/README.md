<!-- i18n-src:c99ac0512cae -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**একটি এজেন্ট অগ্রগতি না করেও শতাধিক টুল কল করতে পারে।** ClawMetry
আপনার কোডিং এজেন্টরা যে সেশন ফাইল ইতিমধ্যে লিখে রাখে সেগুলো পড়ে, এবং টাইমলাইন,
টুল কল এবং রানটাইম যে টোকেন ও খরচের তথ্য প্রকাশ করে তা একটি একক
ভিউতে নিয়ে আসে — যাতে আপনি বুঝতে পারেন কোন দীর্ঘ রান কাজ করছে আর কোনটা আটকে গেছে।

**৩৩টি AI এজেন্ট রানটাইমের** সাথে কাজ করে — Claude Code, OpenAI Codex, Hermes, OpenClaw এবং আরও ২৯টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড। ([সম্পূর্ণ তালিকা](SUPPORTED_RUNTIMES.txt), ক্যাটালগ থেকে তৈরি।)

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। শূন্য কনফিগারেশন। সবকিছু স্বয়ংক্রিয়ভাবে খুঁজে নেয়।

```bash
pip install clawmetry && clawmetry
```

এটি খোলে **http://localhost:8900** এ। শূন্য কনফিগারেশন: এটি আপনার কাছে ইতিমধ্যে থাকা
এজেন্ট রানটাইমগুলো খুঁজে বের করে, সেগুলো রিড-অনলি মোডে পড়ে, এবং সেগুলো কীভাবে চলে তার কিছুই পরিবর্তন করে না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ইনস্টল করার আগে

| | |
|---|---|
| **এটি কী করে** | আপনার এজেন্টরা যে সেশন ফাইল এবং লগ ইতিমধ্যে লিখে রাখে তা পড়ে। কোনো SDK নেই, কোডে কোনো পরিবর্তন নেই, আপনার অ্যাপে কোনো ইনস্ট্রুমেন্টেশন নেই। |
| **আপনি কী দেখেন** | সেশন টাইমলাইন, টুল-বাই-টুল রিপ্লে, টোকেন এবং খরচের বিভাজন, এবং ট্র্যাজেক্টরি সিগন্যাল (লুপিং, পুনরাবৃত্ত ব্যর্থতা) — প্রতিটি রানটাইমের জন্য। |
| **কী ফ্রি** | `pip install clawmetry` কোনো অ্যাকাউন্ট, কী বা নেটওয়ার্ক কল ছাড়াই **OpenClaw, NVIDIA NemoClaw, Goose এবং Qwen Code** পড়ে। বাকি ২৮টি — Claude Code, Codex, Cursor এবং অন্যান্য — ক্লোজড-সোর্স `clawmetry-pro` কম্প্যানিয়ন দ্বারা পড়া হয়, যা ৭-দিনের ট্রায়াল বা একটি প্ল্যানের সাথে আসে — সঠিক বিভাজনের জন্য দেখুন [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)। |
| **কীভাবে শুরু করবেন** | `pip install clawmetry && clawmetry`, তারপর localhost:8900 খুলুন। এই মেশিনে এখনো কোনো এজেন্ট নেই? `clawmetry --sample` তিনটি লেবেলযুক্ত সিন্থেটিক সেশনে খোলে। |
| **আপনার মেশিন থেকে কী বের হয়** | কোনো সেশন ডেটা নয়, যদি না আপনি `clawmetry connect` চালান। ডিফল্টরূপে দুটি জিনিস চলে, দুটোই অপ্ট-আউট করা যায় এবং কোনোটাই সেশন কনটেন্ট বহন করে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং একটি PyPI ভার্সন চেক। প্রতিটি গন্তব্য [docs/EGRESS.md](docs/EGRESS.md) এ তালিকাভুক্ত করা আছে, কমেন্ট পড়ে নয় বরং ওয়্যার ক্যাপচার থেকে পুনর্নির্মিত। |

বিচার করার আগে জানা জরুরি দুটি সীমাবদ্ধতা: রানটাইমগুলো খুবই
ভিন্ন ডেটা প্রকাশ করে (কিছু কোনো খরচই প্রকাশ করে না — [ম্যাট্রিক্স](docs/compatibility.md)
বলে কোনটা কোন রানটাইমে), এবং একটি অ্যাকশন পর্যবেক্ষণ করা সেটা বন্ধ করার
ক্ষমতার সমান নয় ([কোন কন্ট্রোলগুলো বাস্তব, প্রতিটি রানটাইমে](docs/APPROVALS.md))।


## ৩৩টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে ফ্রি:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে একাধিক চালান এবং হেডারের
সুইচার প্রতিটি ট্যাবকে সেগুলোর একটিতে পুনরায় স্কোপ করে।

নিজের SDK-তে নিজের এজেন্ট বানিয়েছেন? ইন্টারসেপ্টর তার LLM কলগুলোও
ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি কী পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট কী করেছে, টার্ন বাই টার্ন, রিপ্লে সহ
- **খরচ ও টোকেন**: প্রতি রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অ্যানোমালি ফ্ল্যাগ সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলের মধ্য দিয়ে চলমান মেসেজের লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং এবং টুল-কল ইভেন্ট স্ট্রিম, যেমনটা ঘটছে তেমনই
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী আকারের উইন্ডো ইউটিলাইজেশন, কম্প্যাকশন বনাম ফোর্সড ওভারফ্লো, সাথে আমরা *দেখতে পারি না* এমন বিষয়ের প্রতি-রানটাইম ম্যাপ ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমরি ও স্কিল**: প্রতিটি রানটাইম আসলে যে ফাইল ও স্কিল লোড করেছিল
- **হেলথ ও লগ**: ডিস্ক, মেমরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email-এ রুট করা
- **অ্যাপ্রুভাল**: ঝুঁকিপূর্ণ টুল কল *চলার আগে* থামিয়ে দিন এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ

কোনো এজেন্ট-তুলনা টুলে আস্থা রাখার আগে উত্তর দেওয়া জরুরি দুটি প্রশ্ন।

**এটি রানটাইমগুলোর মধ্যে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে সামলায়?**

একটি ইউটিলাইজেশন শতাংশ তার হর যতটা সৎ হয় ততটাই সৎ। ClawMetry
[একটি টেবিল থেকে](clawmetry/context_windows.py) প্রতি প্রোভাইডার অনুযায়ী উইন্ডোর আকার নির্ধারণ করে, যা আপনি পড়তে এবং PR করতে পারেন,
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM কভার করে। এটি সব ৩৩টি
রানটাইমকে একটি ভেন্ডরের স্কেল দিয়ে মাপে না। এটা গুরুত্বপূর্ণ: একটি 300K GPT-5 টার্ন
Anthropic-এর 200K-এর বিপরীতে স্কোর করা হলে ">100%, blown" দেখায়, যখন এটি আসলে
GPT-5-এর 400K-এর 75%। একই স্কেল একটি সত্যিকারের ওভারফ্লোড 130K DeepSeek টার্নকে
আরামদায়ক 65% হিসেবে আড়াল করে।

প্রতিটি উইন্ডো তার উৎসের সাথে আসে: `model_table`, `explicit_marker`,
`observed_floor`, বা মডেল না জানলে একটি সৎ `default`। অনুমানের উপর তৈরি একটি
গেজ লুকআপের উপর তৈরি একটির মতো একই কর্তৃত্ব নিয়ে কখনো রেন্ডার হয় না।

ClawMetry কিছু রানটাইমে কেবল কম্প্যাকশন ইভেন্ট দেখতে পায়। তাই
`GET /api/context-coverage` প্রতিটি রানটাইমের জন্য রিপোর্ট করে, একটি **শূন্য মানে
"পরিষ্কারভাবে চলেছে" নাকি "আমরা অন্ধ"** তা। একটি `0` যা আসলে অন্ধ বোঝায়
তা স্পষ্টভাবে বলে দেওয়া হয়। [সম্পূর্ণ বিবরণ](docs/CONTEXT_BLOWOUT.md)

**ইনস্ট্রুমেন্টেশনের খরচ কত?**

| পাথ | আপনার এজেন্টে যুক্ত | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সব ৩৩টি রানটাইম) | **0**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | অন |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+0.44 ms**, অথবা একটি 5s কলের 0.009% | অফ |
| প্রি-টুল হুক গেট (উষ্ণ ক্যাশ) | প্রতি গেটেড টুল কলে **+44 ms**, 36 ms ইন্টারপ্রেটার ফ্লোরের উপরে | অফ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+9.7 ms** | অফ |

ডেমন হোস্ট খরচ: **2,762 events/sec** ইনজেস্ট, ডিস্কে **710 bytes/event**
(১০০k ইভেন্টে 67.7 MB), এবং একটি ব্যস্ত ইনস্টলে টিকে থাকা অবস্থায়
**~12% of one core**। শেষ সংখ্যাটি আমাদের নিজের বলা 5-10% বাজেটের
চেয়ে বেশি, তাই এটা পেজ থেকে বাদ দেওয়ার পরিবর্তে তাড়া করার মতো একটি বাগ হিসেবে প্রকাশ করা হলো।

Apple M2 Pro-তে `benchmarks/overhead.py` দিয়ে পরিমাপ করা। হারনেসটি
প্রতিটি কন্ডিশন আলাদা প্রসেসে চালায়, তাদের ক্রম পরিবর্তন করে, এবং
**রাউন্ডগুলো যদি তাদের চিহ্নে একমত না হয় তাহলে একটি সংখ্যা প্রিন্ট করতে অস্বীকার করে**। এক মিনিটে
আপনার নিজের মেশিনে এটি চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

প্রতিটি পাথ পরিমাপ করা হয়, হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ,
এবং হারনেসটি CI-তে Linux, macOS এবং Windows-এ চলে। জানার মতো দুটি ফলাফল:
প্রক্সির খরচ Windows-এ Linux-এর চেয়ে প্রায় সাত গুণ বেশি, এবং
ডেমন বর্তমানে একটি কোরের প্রায় 12% টিকিয়ে রাখে, যা আমাদের নিজের 5-10%
বাজেটের চেয়ে বেশি। কাঁচা JSON, পদ্ধতি এবং এখনো যা পরিমাপ করা হয়নি সেগুলো
[docs/OVERHEAD.md](docs/OVERHEAD.md) এ আছে।

## প্রাইসিং

| প্ল্যান | এটি যা কভার করে | দাম |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, সম্পূর্ণ ড্যাশবোর্ড, স্থানীয় শুধুমাত্র | $0 |
| **Starter** | উপরের বাকি সব রানটাইম, ফ্লিট ভিউ, ক্লাউড সিংক | $9 per node / month |
| **Pro** | Starter + কন্ট্রোল এবং ইভ্যালুয়েশন: অ্যাপ্রুভাল, টুল-রিস্ক পলিসি, ইভ্যাল, অ্যানোমালি ডিটেকশন, কস্ট অপ্টিমাইজার, OTel এক্সপোর্ট, টেম্পার-এভিডেন্ট অডিট লগ | $19 per node / month |

বাৎসরিক প্ল্যান, Enterprise এবং বর্তমান সংখ্যাগুলো আছে
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** এ। সেলফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। ফ্রি/পেইড বিভাজনের সঠিক বিবরণ
আছে [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) এ।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry স্থানীয় সেশন ফাইল এবং লগ পড়ে। **কোনো সেশন ডেটা আপনার বক্স থেকে বের হয় না
যদি না আপনি `clawmetry connect` চালান** — কোনো প্রম্পট, উত্তর, টুল আর্গুমেন্ট, ফাইল
কনটেন্ট বা লগ লাইন নয়। আপনি যখন কানেক্ট করেন, স্ন্যাপশটটি এন্ড-টু-এন্ড এনক্রিপ্টেড
থাকে একটি কী দিয়ে যা কখনো আপনার মেশিন থেকে বের হয় না, এবং আপনার ব্রাউজারে ডিক্রিপ্ট হয়। একটি
নোডের কী না থাকলে, আপলোডটি স্কিপ করা হয় প্লেন টেক্সটে পাঠানোর পরিবর্তে, এবং
কোনো সার্ভার রেসপন্স সেটা বন্ধ করতে পারে না।

কানেক্ট করার আগে ডিফল্টরূপে দুটি জিনিস চলে, দুটোই অপ্ট-আউট করা যায় এবং
কোনোটাই সেশন ডেটা বহন করে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং PyPI-এর বিপরীতে
একটি ভার্সন চেক। একটি ডিফল্ট ইনস্টল একটি স্টার্টআপ ব্যানার লাইনের জন্য আপনার পাবলিক
IP একবার লুকআপ করে। প্রতিটি গন্তব্য, এটি কী বহন করে এবং কীভাবে বন্ধ করবেন তা তালিকাভুক্ত করা আছে
[docs/EGRESS.md](docs/EGRESS.md) এ; সেলফ-হোস্টেড, রিপয়েন্টেড এবং এয়ার-গ্যাপড ইনস্টলগুলো
মোটেই কোনো discretionary আউটবাউন্ড কল করে না।

ডিক্রিপশনটি আপনার ব্রাউজারে হয়, এমন কোডে যা আমরা আপনাকে সার্ভ করি। এটা আগে
একটি প্রতিশ্রুতি ছিল; এখন এটা এমন কিছু যা আপনি যাচাই করতে পারেন। আপনার কী স্পর্শ করে
এমন প্রতিটি লাইন একটি পাঠযোগ্য ফাইলে থাকে, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা wheel-এর ভেতরে শিপ হয় এবং হুবহু সার্ভ করা হয়, একটি Subresource
Integrity হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা যা প্রকাশ করেছি তাই চালায় কিনা নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

এটা যা প্রমাণ করে না: আমরা সেই পেজটি সার্ভ করি যা ফাইলটি লোড করে, তাই আমরা একটি
আলাদা পেজ সার্ভ করতে পারতাম। Integrity হ্যাশ আপনাকে একটি কম্প্রোমাইজড CDN থেকে রক্ষা করে,
ভেন্ডর থেকে নয়। আপনি যা লাভ করেন তা হলো যে কোনো প্রতিস্থাপন ইচ্ছাকৃত হতে হবে,
পেজ সোর্সে দৃশ্যমান হতে হবে, এবং PyPI-তে থাকা একটি আর্টিফ্যাক্ট থেকে আলাদা হতে হবে
যা যে কেউ ফেচ করতে পারে। সেলফ-হোস্টিং বা স্থানীয়-শুধু থাকলে এই নির্ভরতা
সম্পূর্ণরূপে দূর হয়।

## ইনস্টল

```bash
pip install clawmetry     # then: clawmetry
```

অথবা ওয়ান-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ প্রয়োজন, এবং একই মেশিনে অন্তত একটি
এজেন্ট রানটাইম। Docker নির্দেশনা: [docs/DOCKER.md](docs/DOCKER.md)।

অথবা এজেন্টকে আপনার জন্য এটা সেটআপ করতে দিন। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
স্কিলটি Claude Code, Codex, Cursor, Gemini CLI, Copilot বা OpenCode-কে শেখায়
ClawMetry ইনস্টল করতে, মেশিনের এজেন্টরা কী করছে এবং কী খরচ করছে তা রিপোর্ট করতে,
অনুরোধে একটি সেশন থামাতে, এবং অনুমোদনের জন্য ঝুঁকিপূর্ণ টুল কল ধরে রাখতে:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ডকস

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং একটি রানটাইম কীভাবে যুক্ত করবেন |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | প্রতি-প্রোভাইডার উইন্ডো, কম্প্যাকশন বনাম ওভারফ্লো, প্রতি-রানটাইম কভারেজ |
| [Overhead](docs/OVERHEAD.md) | ইনস্ট্রুমেন্টেশনের খরচ কত, পরিমাপ করা, এটা পুনরুৎপাদনের হারনেস সহ |
| [Entitlements](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টায়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [Approvals & policies](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, রিস্ক স্কোরিং, ফোন অ্যাপ্রুভাল |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো জায়গা থেকে OTLP ইনজেস্ট করুন |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain শুরু থেকে শেষ পর্যন্ত, চালানো যায় এমন উদাহরণ সহ |
| [SDK tracking](docs/SDK_TRACKING.md) | আপনি নিজে তৈরি করা এজেন্টদের জন্য কস্ট অ্যাট্রিবিউশন |
| [Chat channels](docs/CHANNELS.md) | Flow-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ভেতরে এটি কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [Telemetry](docs/TELEMETRY.md) | অ্যানোনিমাস ইনস্টল এবং ডেস্কটপ-ওপেন পিং, এবং সেগুলো কীভাবে বন্ধ করবেন |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, রিড-অনলি, কিছু ছাড়াই সিডেড।

**এটা আপনাকে বলে কখন কিছু ভুল হয়েছে, শুধু কী ঘটেছে তা নয়।**
শীর্ষে দুটি অ্যানোমালি ব্যানার: দৈনিক গড়ের 7x খরচ চলছে, এবং একটি
4.2x কস্ট স্পাইক। তার নিচে, সাম্প্রতিক 667টি সেশনের মধ্যে 324টি একটি waste
সিগন্যাল বহন করছে, কারণ অনুযায়ী আলাদা করা।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটা আপনাকে দেখায় টাকা কোথায় গেল, প্রতিটি উইন্ডোতে।**
আজ $252.47, এই সপ্তাহে $513.15, এই মাসে $1,312.92, প্রতিটির পেছনে থাকা টোকেন
এবং আপনার সাবস্ক্রিপশন তার কতটা ইতিমধ্যে কভার করে তা সহ। তার নিচে,
প্রায় $1,128/mo পুনরুদ্ধারযোগ্য হিসেবে আলাদা করা এবং ক্যাশ পুনঃব্যবহারের মাধ্যমে
ইতিমধ্যে সাশ্রয় হওয়া $17,256/mo।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটা আঁকে কীভাবে একটি মেসেজ একটি উত্তরে পরিণত হয়।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, যে চ্যানেলে এটি এসেছে, গেটওয়ে, এখন উত্তর দেওয়া
মডেল, এবং এটা যে প্রতিটি টুলের কাছে পৌঁছেছে। কাজ সেগুলোর মধ্য দিয়ে চলার সাথে সাথে
নোডগুলো আলোকিত হয়।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনের প্রতিটি এজেন্ট, একটি টেবিলে।**
এটা কী চালায়, গত 24 ঘণ্টায় এবং তার জীবনকালে এর খরচ কত, কখন
এটা সর্বশেষ দেখা গেছে, এর মালিক কে, এবং একটি সাবস্ক্রিপশন বিলটি কভার করছে কিনা।
এখানে 14টি এজেন্ট, 3টি সেশন কাজ করছে, 13টি নিশ্চুপ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটা দেখায় একটি টার্নের সময় এবং টাকা কোথায় গেল, টুল বাই টুল।**
একটি বাস্তব সেশনের একটি টার্ন: $1.16-এ 11.2 মিনিটে 11টি টুল। প্রতিটি Bash
কল এবং মডেল কল টাইমলাইনে তার নিজস্ব বার পায়, যাতে 4.1 মিনিট চলা কমান্ড
এবং 226ms চলা কমান্ডকে এক নজরেই আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটা কাজের গ্রেড দেয়, শুধু খরচ নয়।**
এই সপ্তাহে একটি A: 54টি কাজ পরিষ্কারভাবে ফিরে এসেছে, 2টি কঠিন কাজের খরচ $48.57,
এবং যে রানগুলোতে বিচার করার মতো যথেষ্ট কার্যকলাপ নেই সেগুলোকে জয় হিসেবে গণনা করার
পরিবর্তে গ্রেড থেকে বাদ দেওয়া হয়েছে। প্রতিটি কঠিন রান তার ট্রেসের সাথে লিংক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটা দেখায় কেন কনটেক্সট উইন্ডো ভরে যেতে থাকে।**
সর্বশেষ টার্নে 1M-টোকেন উইন্ডোর 715K, একটি 83.3% পিক, 4টি কম্প্যাকশন
যেগুলো সবই ওভারফ্লোর বদলে প্রোঅ্যাকটিভলি ফায়ার হয়েছে, এবং তার পেছনের প্রতিটি
টার্নের ইউটিলাইজেশন।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনাকে কিছু কনফিগার করতে না হয়েই ডিটেকশন চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টল থেকেই অন থাকে: এজেন্ট নিশ্চুপ হয়ে গেছে, টেলিমেট্রি ফিড
বন্ধ হয়ে গেছে, কস্ট স্পাইক, টোকেন বার্স্ট, বেড়ে চলা এরর, এরর স্পাইক, বাজেট
থ্রেশহোল্ড, থ্রেট সিগনেচার মিলে গেছে, সিকিউরিটি টুল ফাইন্ডিং, সিকিউরিটি পসচার
পরিবর্তিত হয়েছে। এর উপরে আপনার নিজের নিয়ম ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ঝুঁকিপূর্ণ কল ধরে রাখা অপ্ট-ইন, এবং ডিফল্টরূপে বন্ধ থাকে।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড
কল, প্রতিটির জন্য একটি নিয়ম যা আপনি চালু করতে পারেন। যতক্ষণ না আপনি করেন, ClawMetry
পর্যবেক্ষণ করে এবং কিছুই পরিবর্তন করে না। একবার একটি চালু হলে, মিলে যাওয়া কলগুলো এখানে
(বা আপনার ফোনে) অনুমোদন বা অস্বীকৃতির জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, প্রতি রানটাইম: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## স্বীকৃতি

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## স্টার ইতিহাস

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
