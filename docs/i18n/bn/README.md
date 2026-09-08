<!-- i18n-src:88be2deff5d5 -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্ট কী ভাবছে তা দেখুন।** **৩০টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজার্ভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ২৬টি। আপনার সম্পূর্ণ এজেন্ট ফ্লিটের জন্য একটি মাত্র ড্যাশবোর্ড।

> 🌐 **এটি এই ভাষায় পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। জিরো কনফিগ। সবকিছু স্বয়ংক্রিয়ভাবে সনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে। জিরো কনফিগ: এটি আপনার মেশিনে ইতিমধ্যে থাকা এজেন্ট রানটাইমগুলো খুঁজে বের করে, শুধু-পড়ার মোডে সেগুলো পড়ে, এবং সেগুলো কীভাবে চলে তা কিছুই পরিবর্তন করে না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ৩০টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে বিনামূল্যে:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে একাধিক চালান এবং হেডার সুইচার প্রতিটি ট্যাবকে সেগুলোর যেকোনো একটির পরিসরে পুনরায় নিয়ে আসবে।

নিজের এজেন্ট কোনো SDK দিয়ে তৈরি করেছেন? ইন্টারসেপ্টর তারও LLM কলগুলো ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি যা পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট কী করেছে, টার্ন বাই টার্ন, রিপ্লে সহ
- **খরচ ও টোকেন**: প্রতিটি রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অ্যানোমালি ফ্ল্যাগ সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলের মধ্য দিয়ে বার্তা চলাচলের লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং এবং টুল-কল ইভেন্ট স্ট্রিম, ঘটার সাথে সাথেই
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী উইন্ডো সাইজ, কমপ্যাকশন বনাম জোরপূর্বক ওভারফ্লো, এবং আমরা কী দেখতে *পারি না* তার একটি প্রতি-রানটাইম ম্যাপ ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমোরি ও স্কিল**: প্রতিটি রানটাইম আসলে যে ফাইল ও স্কিল লোড করেছে
- **হেলথ ও লগ**: ডিস্ক, মেমোরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email-এ রুট করা
- **অ্যাপ্রুভাল**: ঝুঁকিপূর্ণ টুল কল চালানোর *আগে* থামিয়ে দিন এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ কত

যেকোনো এজেন্ট-তুলনা টুলকে বিশ্বাস করার আগে জিজ্ঞাসা করার মতো দুটি প্রশ্ন।

**এটি রানটাইমজুড়ে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে সামলায়?**

একটি ইউটিলাইজেশন পার্সেন্টেজ ততটাই সৎ যতটা সৎ সেই সংখ্যা যা দিয়ে সেটি ভাগ করা হয়। ClawMetry [আপনি পড়তে ও PR করতে পারেন এমন একটি টেবিল](clawmetry/context_windows.py) থেকে প্রোভাইডার অনুযায়ী উইন্ডো সাইজ নির্ধারণ করে, যা Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM কভার করে। এটি একটিমাত্র ভেন্ডরের স্কেল দিয়ে সব ৩০টি রানটাইম মাপে না। এটা গুরুত্বপূর্ণ: Anthropic-এর ২০০K এর বিপরীতে একটি ৩০০K GPT-5 টার্নের স্কোর ">১০০%, ব্লোন" দেখাবে, যদিও এটি আসলে GPT-5-এর ৪০০K-এর ৭৫% মাত্র। একই স্কেল একটি সত্যিকারের ওভারফ্লো হওয়া ১৩০K DeepSeek টার্নকে আরামদায়ক ৬৫% হিসেবে লুকিয়ে রাখে।

প্রতিটি উইন্ডোতে এর উৎস উল্লেখ থাকে: `model_table`, `explicit_marker`, `observed_floor`, অথবা মডেল না জানা থাকলে একটি সৎ `default`। অনুমানের উপর তৈরি একটি গেজ কখনও লুকআপের উপর তৈরি একটির সমান কর্তৃত্ব নিয়ে রেন্ডার হয় না।

ClawMetry শুধু কিছু রানটাইমে কমপ্যাকশন ইভেন্ট দেখতে পায়। তাই `GET /api/context-coverage` প্রতিটি রানটাইম অনুযায়ী রিপোর্ট করে, একটি শূন্য মানে **"পরিষ্কার চলেছে" নাকি "আমরা অন্ধ"**। যে `0`-এর অর্থ আসলে অন্ধত্ব, তা সেটাই বলে।
[সম্পূর্ণ বিস্তারিত](docs/CONTEXT_BLOWOUT.md)

**ইনস্ট্রুমেন্টেশনের খরচ কত?**

| পাথ | আপনার এজেন্টে যোগ হয় | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সব ৩০টি রানটাইম) | **০**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | চালু |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+০.৪৪ ms**, অথবা ৫সেকেন্ডের একটি কলের ০.০০৯% | বন্ধ |
| প্রি-টুল হুক গেট (ওয়ার্ম ক্যাশ) | প্রতি গেটেড টুল কলে **+৪৪ ms**, ৩৬ ms ইন্টারপ্রেটার ফ্লোরের উপরে | বন্ধ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+৯.৭ ms** | বন্ধ |

ডেমন হোস্ট খরচ: **২,৭৬২ ইভেন্ট/সেকেন্ড** ইনজেস্ট, ডিস্কে প্রতি-ইভেন্ট **৭১০ বাইট** (প্রতি ১ লাখ ইভেন্টে ৬৭.৭ MB), এবং ব্যস্ত একটি ইনস্টলে সাসটেইন্ড **~১২% একটি কোর**। এই শেষ সংখ্যাটি আমাদের নিজস্ব ঘোষিত ৫-১০% বাজেটের চেয়ে বেশি, তাই এটি পাতা থেকে বাদ না দিয়ে তাড়া করার মতো একটি বাগ হিসেবেই প্রকাশ করা হলো।

Apple M2 Pro-তে `benchmarks/overhead.py` দিয়ে মাপা হয়েছে। হারনেসটি প্রতিটি কন্ডিশন আলাদা প্রসেসে চালায়, তাদের অর্ডার পাল্টায়, এবং **রাউন্ডগুলো এর চিহ্নে (sign) একমত না হলে কোনো সংখ্যা প্রিন্ট করতে অস্বীকার করে**। আপনার নিজের মেশিনে এক মিনিটে এটি চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ প্রতিটি পাথ মাপা হয়, এবং হারনেসটি CI-তে Linux, macOS এবং Windows-এ চলে। জানার মতো দুটি ফলাফল: Windows-এ প্রক্সির খরচ Linux-এর প্রায় সাতগুণ, এবং ডেমন বর্তমানে একটি কোরের প্রায় ১২% সাসটেইন করে, যা আমাদের নিজস্ব ৫-১০% বাজেটের চেয়ে বেশি। কাঁচা JSON, পদ্ধতি, এবং যা এখনও মাপা হয়নি তা রয়েছে [docs/OVERHEAD.md](docs/OVERHEAD.md)-এ।

## মূল্য নির্ধারণ

| প্ল্যান | এটি যা কভার করে | মূল্য |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, সম্পূর্ণ ড্যাশবোর্ড, শুধু লোকাল | $0 |
| **Starter** | উপরের বাকি সব রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | প্রতি নোড / মাসে $9 |
| **Pro** | Starter + কন্ট্রোল এবং ইভালুয়েশন: অ্যাপ্রুভাল, টুল-রিস্ক পলিসি, ইভাল, অ্যানোমালি ডিটেকশন, কস্ট অপ্টিমাইজার, OTel এক্সপোর্ট, ট্যাম্পার-এভিডেন্ট অডিট লগ | প্রতি নোড / মাসে $19 |

বার্ষিক প্ল্যান, Enterprise এবং বর্তমান সংখ্যাগুলো রয়েছে
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**-এ। সেলফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। ফ্রি/পেইড বিভাজনের সঠিক বিবরণ
রয়েছে [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-এ।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry লোকাল সেশন ফাইল এবং লগ পড়ে। **আপনি `clawmetry connect` না চালালে কোনো সেশন ডেটা আপনার বাক্সের বাইরে যায় না** — কোনো প্রম্পট, রিপ্লাই, টুল আর্গুমেন্ট, ফাইল কনটেন্ট বা লগ লাইন নয়। আপনি কানেক্ট করলে, স্ন্যাপশটটি এমন একটি কী দিয়ে এন্ড-টু-এন্ড এনক্রিপ্ট করা হয় যা কখনও আপনার মেশিন ছেড়ে যায় না, এবং আপনার ব্রাউজারে ডিক্রিপ্ট করা হয়। কোনো নোডের কী না থাকলে, আপলোডটি স্কিপ করা হয় বরং প্লেইন টেক্সটে পাঠানোর বদলে, এবং কোনো সার্ভার রেসপন্স এটি বন্ধ করতে পারে না।

দুটি জিনিস আপনি কানেক্ট করার আগেই ডিফল্টভাবে চলে, দুটিই অপ্ট-আউট এবং কোনোটিই সেশন ডেটা বহন করে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং PyPI-এর বিপরীতে একটি ভার্সন চেক। একটি ডিফল্ট ইনস্টল স্টার্টআপ ব্যানার লাইনের জন্য একবার আপনার পাবলিক IP-ও লুক আপ করে। প্রতিটি গন্তব্য, এটি কী বহন করে এবং কীভাবে সেটি বন্ধ করা যায় তা তালিকাভুক্ত রয়েছে
[docs/EGRESS.md](docs/EGRESS.md)-এ; সেলফ-হোস্টেড, রিপয়েন্টেড এবং এয়ার-গ্যাপড ইনস্টলগুলো
কোনো বিবেচনামূলক আউটবাউন্ড কল করে না।

ডিক্রিপশনটি আপনার ব্রাউজারে হয়, আমরা আপনাকে যে কোড দিই তাতে। এটি আগে একটি
প্রতিশ্রুতি ছিল; এখন এটি এমন কিছু যা আপনি যাচাই করতে পারেন। আপনার কী স্পর্শ করে এমন প্রতিটি লাইন
একটি পঠনযোগ্য ফাইলে থাকে, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা wheel-এর ভেতরে শিপ হয় এবং হুবহু সার্ভ করা হয়, একটি Subresource
Integrity হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা যা প্রকাশ করেছি তাই চালাচ্ছে কিনা নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

যা এটি প্রমাণ করে না: আমরা সেই পেজটি সার্ভ করি যা ফাইলটি লোড করে, তাই আমরা একটি
ভিন্ন পেজ সার্ভ করতে পারতাম। ইন্টিগ্রিটি হ্যাশ আপনাকে একটি কম্প্রোমাইজড CDN থেকে রক্ষা করে,
ভেন্ডর থেকে নয়। আপনি যা পান তা হলো, যেকোনো প্রতিস্থাপন
ইচ্ছাকৃত হতে হবে, পেজ সোর্সে দৃশ্যমান হতে হবে, এবং PyPI-এর একটি আর্টিফ্যাক্ট থেকে ভিন্ন হতে হবে
যা যে কেউ ফেচ করতে পারে। সেলফ-হোস্টিং বা শুধু-লোকাল থাকা এই নির্ভরতা
সম্পূর্ণরূপে সরিয়ে দেয়।

## ইনস্টল

```bash
pip install clawmetry     # তারপর: clawmetry
```

অথবা এক-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ প্রয়োজন, এবং একই মেশিনে অন্তত একটি এজেন্ট রানটাইম
প্রয়োজন। Docker নির্দেশাবলী: [docs/DOCKER.md](docs/DOCKER.md)।

অথবা এজেন্টকেই আপনার জন্য সেটআপ করতে দিন। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
স্কিলটি Claude Code, Codex, Cursor, Gemini CLI, Copilot বা OpenCode-কে
ClawMetry ইনস্টল করতে, মেশিনের এজেন্টগুলো কী করছে এবং কী খরচ করছে তা রিপোর্ট করতে,
অনুরোধে একটি সেশন বন্ধ করতে, এবং অনুমোদনের জন্য ঝুঁকিপূর্ণ টুল কল আটকে রাখতে শেখায়:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ডকুমেন্টেশন

| | |
|---|---|
| [রানটাইম কম্প্যাটিবিলিটি](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং কীভাবে একটি রানটাইম যোগ করতে হয় |
| [কনটেক্সট ব্লোআউট](docs/CONTEXT_BLOWOUT.md) | প্রোভাইডার অনুযায়ী উইন্ডো, কমপ্যাকশন বনাম ওভারফ্লো, প্রতি-রানটাইম কভারেজ |
| [ওভারহেড](docs/OVERHEAD.md) | ইনস্ট্রুমেন্টেশনের খরচ কত, মাপা, এবং এটি পুনরুৎপাদনের হারনেস সহ |
| [এনটাইটেলমেন্ট](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টিয়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [অ্যাপ্রুভাল ও পলিসি](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, রিস্ক স্কোরিং, ফোন অ্যাপ্রুভাল |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো কিছু থেকে OTLP ইনজেস্ট করুন |
| [নিজের এজেন্ট নিয়ে আসুন](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain সম্পূর্ণভাবে, চালানোর যোগ্য উদাহরণ সহ |
| [SDK ট্র্যাকিং](docs/SDK_TRACKING.md) | আপনার নিজের তৈরি এজেন্টগুলোর জন্য কস্ট অ্যাট্রিবিউশন |
| [চ্যাট চ্যানেল](docs/CHANNELS.md) | Flow-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [আর্কিটেকচার](ARCHITECTURE.md) · [ডেভেলপমেন্ট](docs/DEVELOPMENT.md) | ভেতরে এটি কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [টেলিমেট্রি](docs/TELEMETRY.md) | অ্যানোনিমাস ইনস্টল এবং ডেস্কটপ-ওপেন পিং, এবং সেগুলো কীভাবে বন্ধ করা যায় |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, শুধু-পড়ার মোডে, কিছুই সিড করা ছাড়াই।

**এটি আপনাকে বলে দেয় কখন কিছু ভুল হয়েছে, শুধু কী ঘটেছে তা নয়।**
উপরে দুটি অ্যানোমালি ব্যানার: দৈনিক গড়ের ৭ গুণ খরচ চলছে, এবং একটি
৪.২ গুণ কস্ট স্পাইক। এর নিচে, সাম্প্রতিক ৬৬৭টি সেশনের মধ্যে ৩২৪টিতে একটি
অপচয় সিগন্যাল বহন করছে, কারণ অনুযায়ী তালিকাভুক্ত।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটি আপনাকে দেখায় টাকা কোথায় গেল, প্রতিটি সময়সীমায়।**
আজ $252.47, এই সপ্তাহে $513.15, এই মাসে $1,312.92, প্রতিটির পেছনের টোকেন সহ
এবং আপনার সাবস্ক্রিপশন ইতিমধ্যে কতটা কভার করেছে। তার নিচে,
প্রায় $1,128/মাস পুনরুদ্ধারযোগ্য হিসেবে তালিকাভুক্ত এবং ক্যাশ পুনরায় ব্যবহারের মাধ্যমে ইতিমধ্যে
$17,256/মাস সাশ্রয় হয়েছে।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটি আঁকে কীভাবে একটি বার্তা একটি উত্তর হয়ে ওঠে।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, যে চ্যানেলে এটি এসেছে, গেটওয়ে, এই মুহূর্তে
উত্তর দিচ্ছে যে মডেল, এবং এটি যে প্রতিটি টুল ব্যবহার করেছে। কাজ এগুলোর
মধ্য দিয়ে চলার সময় নোডগুলো আলোকিত হয়।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনের প্রতিটি এজেন্ট, একটি টেবিলে।**
এটি কী চালায়, গত ২৪ ঘণ্টায় এবং সারাজীবনে এর খরচ কত, শেষবার
কখন দেখা গেছে, এর মালিক কে, এবং একটি সাবস্ক্রিপশন বিলটি কভার করছে কিনা। এখানে ১৪টি
এজেন্ট, ৩টি সেশন কাজ করছে, ১৩টি নিশ্চুপ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটি দেখায় একটি টার্নের সময় ও টাকা কোথায় গেল, টুল বাই টুল।**
একটি বাস্তব সেশনের একটি টার্ন: $1.16-এ ১১.২ মিনিটে ১১টি টুল। প্রতিটি Bash
কল এবং মডেল কল টাইমলাইনে নিজস্ব বার পায়, যাতে ৪.১ মিনিট ধরে চলা কমান্ড
এবং ২২৬ms ধরে চলা কমান্ড এক নজরে আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটি কাজের গ্রেড দেয়, শুধু খরচের নয়।**
এই সপ্তাহে একটি A: ৫৪টি টাস্ক পরিষ্কারভাবে ফিরে এসেছে, ২টি রুক্ষ (rough) টাস্ক $48.57
খরচ করেছে, এবং যে রানগুলোতে বিচারের জন্য যথেষ্ট কার্যকলাপ নেই সেগুলো জয় হিসেবে
গণনা না করে গ্রেড থেকে বাদ দেওয়া হয়েছে। প্রতিটি রুক্ষ রান তার ট্রেসের সাথে লিঙ্ক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটি দেখায় কেন কনটেক্সট উইন্ডো ক্রমাগত ভরে যাচ্ছে।**
সর্বশেষ টার্নে ১M-টোকেন উইন্ডোর ৭১৫K, একটি ৮৩.৩% পিক, ৪টি কমপ্যাকশন
যেগুলো সবগুলোই ওভারফ্লোর পরিবর্তে সক্রিয়ভাবে (proactively) ঘটেছিল, এবং তার পেছনের
প্রতিটি টার্নের ইউটিলাইজেশন।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনি কিছু কনফিগার না করেই ডিটেকশন চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টলের পর থেকেই চালু থাকে: এজেন্ট চুপ হয়ে গেছে, টেলিমেট্রি ফিড
বন্ধ হয়ে গেছে, কস্ট স্পাইক, টোকেন বার্স্ট, ক্রমবর্ধমান এরর, এরর স্পাইক, বাজেট
থ্রেশহোল্ড, থ্রেট সিগনেচার মিলেছে, সিকিউরিটি টুলের ফলাফল, সিকিউরিটি পোস্টার
পরিবর্তিত হয়েছে। আপনার নিজস্ব নিয়মগুলো এর উপরে ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**একটি ঝুঁকিপূর্ণ কল আটকে রাখা অপ্ট-ইন, এবং বন্ধ অবস্থায় শিপ হয়।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড
কলগুলোর প্রতিটির জন্য একটি নিয়ম আছে যা আপনি চালু করতে পারেন। আপনি চালু না করা পর্যন্ত,
ClawMetry পর্যবেক্ষণ করে এবং কিছুই পরিবর্তন করে না। একবার একটি চালু হলে, মিলে যাওয়া
কলগুলো এখানে (অথবা আপনার ফোনে) একটি অনুমোদন বা প্রত্যাখ্যানের জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, প্রতি রানটাইম অনুযায়ী: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

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
