<!-- i18n-src:d21bea5161e0 -->
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

**আপনার এজেন্টকে চিন্তা করতে দেখুন।** **৩০টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম পর্যবেক্ষণ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ২৬টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এটি পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। জিরো কনফিগ। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত হয়।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে। জিরো কনফিগ: এটি আপনার কাছে ইতিমধ্যে থাকা এজেন্ট
রানটাইমগুলো খুঁজে বের করে, সেগুলো শুধু-পড়ার (read-only) মোডে পড়ে, এবং সেগুলো কীভাবে চলে সে ব্যাপারে কিছুই পরিবর্তন করে না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ৩০টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে ফ্রি:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একই সাথে একাধিক চালান এবং হেডার
সুইচার প্রতিটি ট্যাবকে সেগুলোর যেকোনো একটির উপর পুনরায় স্কোপ করে দেয়।

কোনো SDK ব্যবহার করে নিজের এজেন্ট তৈরি করেছেন? ইন্টারসেপ্টর সেটির LLM কলগুলোও
ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি যা পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট প্রতিটি টার্নে কী করেছে, রিপ্লে সহ
- **খরচ ও টোকেন**: রানটাইম, মডেল, সেশন ও দিন অনুযায়ী, অ্যানোমালি ফ্ল্যাগ সহ
- **ফ্লো**: চ্যানেল, মডেল ও টুলগুলোর মধ্য দিয়ে চলাচল করা মেসেজগুলোর লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং এবং টুল-কল ইভেন্ট স্ট্রিম, যা ঘটছে ঠিক তখনই
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী নির্ধারিত উইন্ডো ইউটিলাইজেশন, কমপ্যাকশন বনাম জোরপূর্বক ওভারফ্লো, এবং আমরা যা *দেখতে পারি না* তার একটি রানটাইম-ভিত্তিক ম্যাপ ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমরি ও স্কিল**: প্রতিটি রানটাইম প্রকৃতপক্ষে যে ফাইল ও স্কিল লোড করেছে
- **হেলথ ও লগ**: ডিস্ক, মেমরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email-এ রুট করা
- **অ্যাপ্রুভাল**: ঝুঁকিপূর্ণ টুল কলগুলো চালানোর *আগে* থামান এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ কী

যেকোনো এজেন্ট-তুলনা টুলকে বিশ্বাস করার আগে উত্তর জানা উচিত এমন দুটি প্রশ্ন।

**এটি রানটাইমজুড়ে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে সামলায়?**

একটি ইউটিলাইজেশন শতাংশ ততটাই সৎ যতটা সৎ সেই সংখ্যা যা দিয়ে এটিকে ভাগ করা হয়। ClawMetry
[একটি টেবিল থেকে](clawmetry/context_windows.py) প্রোভাইডার অনুযায়ী উইন্ডোর আকার নির্ধারণ করে, যা আপনি পড়তে এবং যাতে PR করতে
পারেন, যেখানে Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM কভার করা হয়েছে। এটি ২৬টি
রানটাইমকেই একই ভেন্ডরের স্কেল দিয়ে মাপে না। এটি গুরুত্বপূর্ণ: একটি ৩০০K GPT-5 টার্ন
যখন Anthropic-এর ২০০K এর বিপরীতে স্কোর করা হয় তখন তা ">১০০%, ব্লোন" দেখায়, যদিও প্রকৃতপক্ষে এটি
GPT-5-এর ৪০০K-এর ৭৫% মাত্র। একই স্কেল একটি সত্যিকারভাবে ওভারফ্লো হওয়া
১৩০K DeepSeek টার্নকে আরামদায়ক ৬৫% হিসেবে লুকিয়ে রাখে।

প্রতিটি উইন্ডো তার উৎস সহ পাঠানো হয়: `model_table`, `explicit_marker`,
`observed_floor`, অথবা মডেল না জানলে একটি সৎ `default`। একটি অনুমানের উপর নির্মিত
গেজ কখনো একটি লুকআপের উপর নির্মিত গেজের মতো একই কর্তৃত্ব নিয়ে রেন্ডার হয় না।

ClawMetry শুধুমাত্র কিছু রানটাইমে কমপ্যাকশন ইভেন্ট দেখতে পায়। তাই
`GET /api/context-coverage` প্রতিটি রানটাইমের জন্য রিপোর্ট করে যে একটি **শূন্য মানে
"পরিষ্কারভাবে চলেছে" নাকি "আমরা অন্ধ"**। যে `0` আসলে অন্ধত্ব বোঝায়, তা সেটাই বলে।
[সম্পূর্ণ বিস্তারিত](docs/CONTEXT_BLOWOUT.md)

**ইনস্ট্রুমেন্টেশনের খরচ কত?**

| পাথ | আপনার এজেন্টে যোগ হয় | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সবগুলো ৩০ রানটাইম) | **০**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | চালু |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+০.৪৪ ms**, অথবা একটি ৫s কলের ০.০০৯% | বন্ধ |
| প্রি-টুল হুক গেট (উষ্ণ ক্যাশ) | প্রতি গেটেড টুল কলে **+৪৪ ms**, একটি ৩৬ ms ইন্টারপ্রেটার ফ্লোরের উপর | বন্ধ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+৯.৭ ms** | বন্ধ |

ডিমন হোস্ট খরচ: ইনজেস্ট **২,৭৬২ ইভেন্ট/সেকেন্ড**, ডিস্কে প্রতি ইভেন্টে **৭১০ বাইট**
(প্রতি ১ লক্ষ ইভেন্টে ৬৭.৭ MB), এবং একটি ব্যস্ত ইনস্টলে স্থায়ীভাবে **~১২% এক কোর**।
এই শেষ সংখ্যাটি আমাদের নিজস্ব ঘোষিত ৫-১০% বাজেটের চেয়ে বেশি, তাই এটি
পাতা থেকে বাদ দেওয়ার পরিবর্তে তাড়া করার মতো একটি বাগ হিসেবে প্রকাশিত হয়েছে।

Apple M2 Pro-তে `benchmarks/overhead.py` দিয়ে পরিমাপ করা হয়েছে। হারনেসটি
প্রতিটি কন্ডিশন আলাদা প্রসেসে চালায়, সেগুলোর ক্রম পরিবর্তন করে, এবং **রাউন্ডগুলো
এর চিহ্নে একমত না হলে কোনো সংখ্যা প্রিন্ট করতে অস্বীকার করে**। এক মিনিটে
নিজের মেশিনে এটি চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

প্রতিটি পাথ পরিমাপ করা হয়েছে, হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ,
এবং হারনেসটি CI-তে Linux, macOS এবং Windows-এ চলে। জানার মতো দুটি ফলাফল:
Windows-এ প্রক্সির খরচ Linux-এর তুলনায় প্রায় সাত গুণ বেশি, এবং
ডিমনটি বর্তমানে প্রায় ১২% এক কোর স্থায়ীভাবে ব্যবহার করে, যা আমাদের নিজস্ব ৫-১০%
বাজেটের চেয়ে বেশি। কাঁচা JSON, পদ্ধতি, এবং এখনও যা পরিমাপ করা হয়নি, তা
[docs/OVERHEAD.md](docs/OVERHEAD.md)-এ আছে।

## মূল্য নির্ধারণ

| প্ল্যান | এতে যা অন্তর্ভুক্ত | মূল্য |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, সম্পূর্ণ ড্যাশবোর্ড, শুধুমাত্র লোকাল | $0 |
| **Starter** | উপরের প্রতিটি অন্যান্য রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | প্রতি নোড / মাসে $৯ |
| **Pro** | Starter + কন্ট্রোল ও ইভালুয়েশন: অ্যাপ্রুভাল, টুল-রিস্ক পলিসি, ইভাল, অ্যানোমালি ডিটেকশন, কস্ট অপ্টিমাইজার, OTel এক্সপোর্ট, টেম্পার-এভিডেন্ট অডিট লগ | প্রতি নোড / মাসে $১৯ |

বার্ষিক প্ল্যান, এন্টারপ্রাইজ এবং বর্তমান সংখ্যাগুলো
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**-এ আছে। সেলফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। ফ্রি/পেইড এর সঠিক বিভাজন
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-এ আছে।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry স্থানীয় সেশন ফাইল এবং লগ পড়ে। **আপনি `clawmetry connect` না চালালে
কোনো সেশন ডেটা আপনার বক্সের বাইরে যায় না** — কোনো প্রম্পট, রিপ্লাই, টুল আর্গুমেন্ট, ফাইল
কন্টেন্ট বা লগ লাইন নয়। আপনি যখন কানেক্ট করেন, তখন স্ন্যাপশটটি এমন একটি কী দিয়ে
এন্ড-টু-এন্ড এনক্রিপ্ট করা হয় যা কখনো আপনার মেশিন ছেড়ে যায় না, এবং আপনার ব্রাউজারে ডিক্রিপ্ট করা হয়। কোনো
নোডের কী না থাকলে, আপলোডটি স্কিপ করা হয় বরং কাঁচা অবস্থায় পাঠানোর পরিবর্তে, এবং কোনো
সার্ভার রেসপন্স সেটি বন্ধ করতে পারে না।

কানেক্ট করার আগে ডিফল্টভাবে দুটি জিনিস চলে, উভয়ই অপ্ট-আউট করা যায় এবং কোনোটিতেই
সেশন ডেটা থাকে না: একটি অজ্ঞাতনামা ইনস্টল পিং এবং PyPI-এর বিরুদ্ধে একটি ভার্সন চেক। একটি ডিফল্ট
ইনস্টল স্টার্টআপ ব্যানার লাইনের জন্য একবার আপনার পাবলিক IP-ও লুকআপ করে। প্রতিটি গন্তব্য, তা কী বহন করে
এবং কীভাবে বন্ধ করতে হয় তা
[docs/EGRESS.md](docs/EGRESS.md)-এ তালিকাভুক্ত আছে; সেলফ-হোস্টেড, রিপয়েন্টেড এবং এয়ার-গ্যাপড ইনস্টল
কোনো ঐচ্ছিক আউটবাউন্ড কল করে না।

ডিক্রিপশন আপনার ব্রাউজারে ঘটে, আমাদের পাঠানো কোডে। এটি আগে
একটি প্রতিশ্রুতি ছিল; এখন এটি এমন কিছু যা আপনি যাচাই করতে পারেন। আপনার কী স্পর্শ করে এমন প্রতিটি লাইন
একটি পঠনযোগ্য ফাইলে থাকে, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা wheel-এর ভেতরে পাঠানো হয় এবং যথাযথভাবে পরিবেশন করা হয়, একটি Subresource
Integrity হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা প্রকাশ করা কোডটিই চালাচ্ছে তা নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

এটি যা প্রমাণ করে না: আমরা যে পেজটি এই ফাইলটি লোড করে সেটিও পরিবেশন করি, তাই আমরা
একটি ভিন্ন পেজ পরিবেশন করতে পারতাম। ইন্টিগ্রিটি হ্যাশগুলো আপনাকে একটি আপোসকৃত CDN থেকে
রক্ষা করে, ভেন্ডর থেকে নয়। আপনি যা পান তা হলো, যেকোনো প্রতিস্থাপন
ইচ্ছাকৃত হতে হবে, পেজ সোর্সে দৃশ্যমান হতে হবে, এবং PyPI-তে থাকা একটি আর্টিফ্যাক্ট থেকে যা যে কেউ
ফেচ করতে পারে তার থেকে ভিন্ন হতে হবে। সেলফ-হোস্টিং বা শুধুমাত্র-লোকাল থাকা এই নির্ভরতাকে
সম্পূর্ণভাবে সরিয়ে দেয়।

## ইনস্টল

```bash
pip install clawmetry     # then: clawmetry
```

অথবা এক-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ প্রয়োজন, এবং একই মেশিনে অন্তত একটি
এজেন্ট রানটাইম প্রয়োজন। Docker নির্দেশাবলী: [docs/DOCKER.md](docs/DOCKER.md)।

## ডকুমেন্টেশন

| | |
|---|---|
| [রানটাইম কম্প্যাটিবিলিটি](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং কীভাবে একটি রানটাইম যোগ করতে হয় |
| [কনটেক্সট ব্লোআউট](docs/CONTEXT_BLOWOUT.md) | প্রোভাইডার-অনুযায়ী উইন্ডো, কমপ্যাকশন বনাম ওভারফ্লো, রানটাইম-ভিত্তিক কভারেজ |
| [ওভারহেড](docs/OVERHEAD.md) | ইনস্ট্রুমেন্টেশনের খরচ কত, পরিমাপ করা, এটি পুনরুৎপাদনের হারনেস সহ |
| [এনটাইটেলমেন্ট](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টিয়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [অ্যাপ্রুভাল ও পলিসি](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, রিস্ক স্কোরিং, ফোন অ্যাপ্রুভাল |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো কিছু থেকে OTLP ইনজেস্ট করুন |
| [SDK ট্র্যাকিং](docs/SDK_TRACKING.md) | নিজে তৈরি করা এজেন্টগুলোর জন্য কস্ট অ্যাট্রিবিউশন |
| [চ্যাট চ্যানেল](docs/CHANNELS.md) | ফ্লো-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [আর্কিটেকচার](ARCHITECTURE.md) · [ডেভেলপমেন্ট](docs/DEVELOPMENT.md) | এটি ভেতরে কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [টেলিমেট্রি](docs/TELEMETRY.md) | অজ্ঞাতনামা ইনস্টল ও ডেস্কটপ-ওপেন পিং, এবং সেগুলো কীভাবে বন্ধ করতে হয় |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, শুধু-পড়ার মোডে, কিছুই সাজানো ছাড়াই।

**এটি আপনাকে বলে কখন কিছু ভুল হচ্ছে, শুধু কী ঘটেছে তা নয়।**
উপরে দুটি অ্যানোমালি ব্যানার: দৈনিক গড়ের ৭ গুণ চলমান খরচ, এবং একটি
৪.২ গুণ কস্ট স্পাইক। সেগুলোর নিচে, সাম্প্রতিক ৬৬৭টি সেশনের মধ্যে ৩২৪টি একটি
অপচয় সংকেত বহন করছে, কারণ অনুযায়ী তালিকাভুক্ত।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটি আপনাকে দেখায় টাকা কোথায় গেছে, প্রতিটি উইন্ডোতে।**
আজ $২৫২.৪৭, এই সপ্তাহে $৫১৩.১৫, এই মাসে $১,৩১২.৯২, প্রতিটির পেছনের টোকেন সহ
এবং আপনার সাবস্ক্রিপশন ইতিমধ্যে কতটা কভার করে। এর নিচে,
প্রায় $১,১২৮/মাস পুনরুদ্ধারযোগ্য হিসেবে তালিকাভুক্ত এবং ক্যাশ পুনর্ব্যবহারের মাধ্যমে ইতিমধ্যে সাশ্রয় হওয়া
$১৭,২৫৬/মাস।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটি আঁকে কীভাবে একটি মেসেজ একটি উত্তরে পরিণত হয়।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, যে চ্যানেলে এটি এসেছে, গেটওয়ে, এখন উত্তর দেওয়া
মডেল, এবং প্রতিটি টুল যা এটি ব্যবহার করেছে। কাজ যেমন এগুলোর মধ্য দিয়ে যায়, নোডগুলো
আলোকিত হয়।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনের প্রতিটি এজেন্ট, একটি টেবিলে।**
এটি কী চালায়, গত ২৪ ঘণ্টায় এবং তার সারাজীবনে এটির খরচ কত, এটি
সর্বশেষ কখন দেখা গেছে, এটির মালিক কে, এবং একটি সাবস্ক্রিপশন বিলটি কভার করছে কিনা। এখানে ১৪টি এজেন্ট,
৩টি সেশন কাজ করছে, ১৩টি শান্ত।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটি দেখায় একটি টার্নের সময় ও অর্থ কোথায় গেছে, টুল অনুযায়ী।**
একটি বাস্তব সেশনের একটি টার্ন: ১১.২ মিনিটে ১১টি টুল $১.১৬ খরচে। প্রতিটি
Bash কল এবং মডেল কল টাইমলাইনে তার নিজস্ব বার পায়, তাই ৪.১ মিনিট ধরে চলা
কমান্ড এবং ২২৬ms ধরে চলা কমান্ড এক নজরেই আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটি কাজটি গ্রেড করে, শুধু খরচ নয়।**
এই সপ্তাহে একটি A: ৫৪টি টাস্ক পরিষ্কারভাবে সম্পন্ন হয়েছে, ২টি খারাপ কাজের খরচ $৪৮.৫৭,
এবং যে রানগুলোতে বিচার করার মতো যথেষ্ট কার্যকলাপ নেই সেগুলো জয় হিসেবে গণনা করার পরিবর্তে
গ্রেড থেকে বাদ দেওয়া হয়েছে। প্রতিটি খারাপ রান তার ট্রেসের সাথে লিঙ্ক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটি দেখায় কেন কনটেক্সট উইন্ডো ক্রমাগত ভরে যাচ্ছে।**
সর্বশেষ টার্নে ১M-টোকেন উইন্ডোর ৭১৫K, একটি ৮৩.৩% পিক, ৪টি কমপ্যাকশন
যা সবগুলোই ওভারফ্লোর পরিবর্তে সক্রিয়ভাবে ঘটেছে, প্লাস এর পেছনের প্রতিটি
টার্নের ইউটিলাইজেশন।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনার কোনো কনফিগারেশন ছাড়াই ডিটেকশন চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টলের পর থেকেই চালু: এজেন্ট চুপ হয়ে গেছে, টেলিমেট্রি ফিড
বন্ধ হয়ে গেছে, কস্ট স্পাইক, টোকেন বার্স্ট, বাড়তে থাকা এরর, এরর স্পাইক, বাজেট
থ্রেশহোল্ড, থ্রেট সিগনেচার মিলেছে, সিকিউরিটি টুল ফাইন্ডিং, সিকিউরিটি পোজিশন
পরিবর্তিত হয়েছে। আপনার নিজের নিয়মগুলো এর উপরে ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**একটি ঝুঁকিপূর্ণ কল আটকে রাখা ঐচ্ছিক, এবং ডিফল্টভাবে বন্ধ থাকে।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড
কল প্রতিটির জন্য আপনি চালু করতে পারেন এমন একটি নিয়ম আছে। আপনি চালু না করা পর্যন্ত, ClawMetry শুধু দেখে এবং
কিছুই পরিবর্তন করে না। একবার একটি চালু হলে, মিলে যাওয়া কলগুলো এখানে (অথবা আপনার ফোনে)
অনুমোদন বা প্রত্যাখ্যানের জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, রানটাইম অনুযায়ী: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## স্টার হিস্ট্রি

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## লাইসেন্স

MIT · [@vivekchand](https://github.com/vivekchand) দ্বারা তৈরি · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
