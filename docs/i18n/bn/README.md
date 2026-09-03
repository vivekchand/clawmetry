<!-- i18n-src:9767c8001c9c -->
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

**আপনার এজেন্ট কীভাবে চিন্তা করছে তা দেখুন।** **৩০টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজার্ভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ২৬টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এই ভাষায় পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। কোনো কনফিগারেশন লাগে না। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত হয়।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে। কোনো কনফিগারেশন লাগে না: এটি আপনার কাছে থাকা এজেন্ট রানটাইমগুলো খুঁজে বের করে, সেগুলো শুধু পড়ে (read-only), এবং সেগুলো কীভাবে চলে তার কিছুই পরিবর্তন করে না।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ৩০টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে বিনামূল্যে:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে একাধিক চালান এবং হেডার সুইচার প্রতিটি ট্যাবকে সেগুলোর যেকোনো একটির পরিসরে পুনরায় স্কোপ করবে।

কোনো SDK ব্যবহার করে নিজের এজেন্ট তৈরি করেছেন? ইন্টারসেপ্টর সেটির LLM কলও ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি যা পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট কী করেছে, টার্ন বাই টার্ন, রিপ্লে সহ
- **খরচ ও টোকেন**: রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অ্যানোমালি ফ্ল্যাগ সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলের মধ্য দিয়ে চলাচলকারী মেসেজের লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং এবং টুল-কল ইভেন্ট স্ট্রিম যেমনটা ঘটছে ঠিক তেমনি
- **কনটেক্সট ব্লোআউট**: প্রোভাইডার অনুযায়ী উইন্ডোর আকার, কমপ্যাকশন বনাম জোরপূর্বক ওভারফ্লো, সাথে আমরা কী *দেখতে পারি না* তার একটি রানটাইম-ভিত্তিক ম্যাপ ([কীভাবে](docs/CONTEXT_BLOWOUT.md))
- **মেমরি ও স্কিলস**: প্রতিটি রানটাইম আসলে যে ফাইল ও স্কিলগুলো লোড করেছিল
- **স্বাস্থ্য ও লগ**: ডিস্ক, মেমরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, Slack, Discord, PagerDuty, Telegram, Email এ রাউট করা
- **অ্যাপ্রুভালস**: ঝুঁকিপূর্ণ টুল কল *চলার আগেই* থামান এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## কনটেক্সট ব্লোআউট, এবং পর্যবেক্ষণের খরচ কত

যেকোনো এজেন্ট-তুলনা টুলকে বিশ্বাস করার আগে দুটি প্রশ্নের উত্তর জানা দরকার।

**এটি বিভিন্ন রানটাইম জুড়ে কনটেক্সট-উইন্ডো ব্লোআউট কীভাবে সামাল দেয়?**

একটি ইউটিলাইজেশন শতাংশ ততটাই সৎ যতটা সৎ সেই সংখ্যা যা দিয়ে এটি ভাগ করা হয়। ClawMetry [আপনি পড়তে এবং PR করতে পারেন এমন একটি টেবিল](clawmetry/context_windows.py) থেকে প্রোভাইডার অনুযায়ী উইন্ডোর আকার নির্ধারণ করে, যা Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama এবং GLM কভার করে। এটি একটি ভেন্ডরের স্কেল দিয়ে সব ২৬টি রানটাইম মাপে না। এটি গুরুত্বপূর্ণ: একটি ৩০০K GPT-5 টার্ন Anthropic-এর ২০০K এর বিপরীতে স্কোর করা হলে দেখাবে ">১০০%, ব্লোন", যদিও এটি আসলে GPT-5 এর ৪০০K এর ৭৫%। একই স্কেল একটি সত্যিকারের ওভারফ্লো হওয়া ১৩০K DeepSeek টার্নকে একটি আরামদায়ক ৬৫% হিসেবে লুকিয়ে ফেলে।

প্রতিটি উইন্ডো তার প্রোভেন্যান্স সহ আসে: `model_table`, `explicit_marker`, `observed_floor`, অথবা যখন আমরা মডেলটি জানি না তখন একটি সৎ `default`। একটি অনুমানের উপর তৈরি গেজ কখনো একটি লুকআপের উপর তৈরি গেজের মতো একই কর্তৃত্ব নিয়ে রেন্ডার হয় না।

ClawMetry কিছু রানটাইমে শুধুমাত্র কমপ্যাকশন ইভেন্টগুলো দেখতে পায়। তাই `GET /api/context-coverage` প্রতিটি রানটাইম অনুযায়ী রিপোর্ট করে, একটি **শূন্যের মানে কি "পরিষ্কারভাবে চলেছে" নাকি "আমরা অন্ধ"**। একটি `0` যার প্রকৃত অর্থ অন্ধ, তা সেটাই বলে দেয়। [পূর্ণ বিবরণ](docs/CONTEXT_BLOWOUT.md)

**ইনস্ট্রুমেন্টেশনের খরচ কত?**

| পথ | আপনার এজেন্টে যোগ হয় | ডিফল্ট? |
|---|---|---|
| সেশন-ফাইল টেইলিং (সব ৩০টি রানটাইম) | **০**। আলাদা প্রসেস, আপনার এজেন্টে কোনো ClawMetry কোড নেই | চালু |
| HTTP ইন্টারসেপ্টর (`CLAWMETRY_INTERCEPT=1`) | প্রতি LLM কলে **+০.৪৪ ms**, অর্থাৎ ৫s কলের ০.০০৯% | বন্ধ |
| প্রি-টুল হুক গেট (ওয়ার্ম ক্যাশ) | প্রতি গেটেড টুল কলে **+৪৪ ms**, ৩৬ ms ইন্টারপ্রেটার ফ্লোরের উপরে | বন্ধ |
| এনফোর্সমেন্ট প্রক্সি | প্রতি LLM কলে **+৯.৭ ms** | বন্ধ |

ডেমন হোস্টের খরচ: **২,৭৬২ ইভেন্ট/সেকেন্ড** ইনজেস্ট, ডিস্কে **৭১০ বাইট/ইভেন্ট** (প্রতি ১ লক্ষ ইভেন্টে ৬৭.৭ MB), এবং একটি ব্যস্ত ইনস্টলে টেকসই **এক কোরের ~১২%**। এই শেষ সংখ্যাটি আমাদের নিজস্ব বলা ৫-১০% বাজেটের চেয়ে বেশি, তাই এটি পাতা থেকে বাদ না দিয়ে বরং তাড়া করার মতো একটি বাগ হিসেবে প্রকাশ করা হলো।

Apple M2 Pro তে `benchmarks/overhead.py` দিয়ে মাপা। হারনেস প্রতিটি কন্ডিশন আলাদা প্রসেসে চালায়, তাদের ক্রম পরিবর্তন করে, এবং **রাউন্ডগুলো তাদের সাইনের ব্যাপারে একমত না হলে কোনো সংখ্যা প্রিন্ট করতে অস্বীকার করে**। এক মিনিটে আপনার নিজের মেশিনে চালান:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

প্রতিটি পথ মাপা হয়েছে, হুক গেট এবং এনফোর্সমেন্ট প্রক্সি সহ, এবং হারনেস CI-তে Linux, macOS এবং Windows এ চলে। জানার মতো দুটি ফলাফল: প্রক্সির খরচ Windows এ Linux এর চেয়ে প্রায় সাত গুণ বেশি, এবং ডেমন বর্তমানে এক কোরের প্রায় ১২% টেকসইভাবে ব্যবহার করে, যা আমাদের নিজস্ব ৫-১০% বাজেটের চেয়ে বেশি। কাঁচা JSON, পদ্ধতি, এবং এখনো যা মাপা হয়নি তা রয়েছে [docs/OVERHEAD.md](docs/OVERHEAD.md) এ।

## মূল্য নির্ধারণ

| প্ল্যান | এটি যা কভার করে | মূল্য |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, সম্পূর্ণ ড্যাশবোর্ড, শুধুমাত্র লোকাল | $০ |
| **Starter** | উপরে উল্লিখিত বাকি সব রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | প্রতি নোড / মাসে $৯ |
| **Pro** | Starter + কন্ট্রোল এবং মূল্যায়ন: অ্যাপ্রুভালস, টুল-রিস্ক পলিসি, ইভালস, অ্যানোমালি ডিটেকশন, কস্ট অপটিমাইজার, OTel এক্সপোর্ট, tamper-evident অডিট লগ | প্রতি নোড / মাসে $১৯ |

বার্ষিক প্ল্যান, Enterprise এবং বর্তমান সংখ্যাগুলো রয়েছে
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** এ। সেলফ-হোস্টেড লাইসেন্স
কী গুলো ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। ফ্রি/পেইড এর সঠিক বিভাজন
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) এ রয়েছে।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry লোকাল সেশন ফাইল এবং লগ পড়ে। **আপনি `clawmetry connect` না চালালে কোনো সেশন ডেটা
আপনার বক্স থেকে বের হয় না** — কোনো প্রম্পট, রিপ্লাই, টুল আর্গুমেন্ট, ফাইল
কন্টেন্ট বা লগ লাইন নয়। আপনি যখন কানেক্ট করেন, তখন স্ন্যাপশটটি এমন একটি
কী দিয়ে এন্ড-টু-এন্ড এনক্রিপ্ট করা হয় যা কখনো আপনার মেশিন ছেড়ে যায় না, এবং
আপনার ব্রাউজারে ডিক্রিপ্ট করা হয়। কোনো নোডের কী না থাকলে, আপলোডটি স্কিপ করা
হয় প্লেইনটেক্সটে পাঠানোর পরিবর্তে, এবং কোনো সার্ভার রেসপন্স সেটি বন্ধ করে দিতে
পারে না।

আপনি কানেক্ট করার আগে দুটি জিনিস ডিফল্টভাবে চলে, উভয়ই অপ্ট-আউট এবং
কোনোটিতেই সেশন ডেটা থাকে না: একটি অ্যানোনিমাস ইনস্টল পিং এবং PyPI এর
বিপরীতে একটি ভার্সন চেক। একটি ডিফল্ট ইনস্টল স্টার্টআপ ব্যানার লাইনের জন্য
একবার আপনার পাবলিক IP-ও লুকআপ করে। প্রতিটি গন্তব্য, এটি কী বহন করে এবং
কীভাবে সেটি বন্ধ করতে হয় তা [docs/EGRESS.md](docs/EGRESS.md) এ তালিকাভুক্ত
আছে; সেলফ-হোস্টেড, রিপয়েন্টেড এবং এয়ার-গ্যাপড ইনস্টলগুলো কোনো ঐচ্ছিক
আউটবাউন্ড কল করে না।

ডিক্রিপশনটি আপনার ব্রাউজারে ঘটে, আমরা আপনাকে যে কোড পরিবেশন করি তাতে।
এটি আগে একটি প্রতিশ্রুতি ছিল; এখন এটি এমন কিছু যা আপনি যাচাই করতে পারেন।
আপনার কী স্পর্শ করে এমন প্রতিটি লাইন একটি পঠনযোগ্য ফাইলে রয়েছে,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
যা wheel এর ভিতরে শিপ করে এবং যেমন আছে তেমনই পরিবেশিত হয়, একটি
Subresource Integrity হ্যাশ দিয়ে পিন করা। ব্রাউজার আমরা যা প্রকাশ করেছি
তাই চালায় কিনা তা নিশ্চিত করতে:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

এটি যা প্রমাণ করে না: আমরা সেই পেজটি পরিবেশন করি যা ফাইলটি লোড করে, তাই
আমরা একটি ভিন্ন পেজ পরিবেশন করতে পারি। ইন্টিগ্রিটি হ্যাশগুলো আপনাকে একটি
কম্প্রোমাইজড CDN থেকে রক্ষা করে, ভেন্ডর থেকে নয়। আপনি যা পান তা হলো যেকোনো
প্রতিস্থাপন ইচ্ছাকৃত হতে হবে, পেজ সোর্সে দৃশ্যমান হতে হবে, এবং PyPI এর একটি
আর্টিফ্যাক্ট থেকে আলাদা হতে হবে যা যে কেউ ফেচ করতে পারে। সেলফ-হোস্টিং বা
শুধুমাত্র লোকাল থাকা এই নির্ভরতাকে সম্পূর্ণরূপে সরিয়ে দেয়।

## ইনস্টল

```bash
pip install clawmetry     # then: clawmetry
```

অথবা এক লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows এ Python 3.8+ প্রয়োজন, এবং একই মেশিনে কমপক্ষে একটি
এজেন্ট রানটাইম প্রয়োজন। Docker নির্দেশাবলী: [docs/DOCKER.md](docs/DOCKER.md)।

## ডকুমেন্টেশন

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং কীভাবে একটি রানটাইম যোগ করতে হয় |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | প্রোভাইডার-ভিত্তিক উইন্ডো, কমপ্যাকশন বনাম ওভারফ্লো, রানটাইম-ভিত্তিক কভারেজ |
| [Overhead](docs/OVERHEAD.md) | ইনস্ট্রুমেন্টেশনের খরচ কত, মাপা, এবং এটি পুনরুৎপাদন করার হারনেস সহ |
| [Entitlements](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টায়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [Approvals & policies](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, রিস্ক স্কোরিং, ফোন অ্যাপ্রুভাল |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো কিছু থেকে OTLP ইনজেস্ট করুন |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain সম্পূর্ণরূপে, চালানোর মতো উদাহরণ সহ |
| [SDK tracking](docs/SDK_TRACKING.md) | আপনার নিজের তৈরি এজেন্টের জন্য কস্ট অ্যাট্রিবিউশন |
| [Chat channels](docs/CHANNELS.md) | Flow তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ভেতরে এটি কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [Telemetry](docs/TELEMETRY.md) | অ্যানোনিমাস ইনস্টল এবং ডেস্কটপ-ওপেন পিং, এবং কীভাবে সেগুলো বন্ধ করতে হয় |

## স্ক্রিনশট

নিচের প্রতিটি সংখ্যা একটি বাস্তব মেশিন থেকে, শুধু-পড়ার (read-only), কিছুই সাজানো ছাড়া।

**এটি আপনাকে জানায় কখন কিছু ভুল হচ্ছে, শুধু কী ঘটেছে তা নয়।**
উপরে দুটি অ্যানোমালি ব্যানার: দৈনিক গড়ের ৭ গুণ খরচ চলছে, এবং একটি
৪.২ গুণ কস্ট স্পাইক। তার নিচে, সাম্প্রতিক ৬৬৭টি সেশনের মধ্যে ৩২৪টি একটি
ওয়েস্ট সিগন্যাল বহন করছে, কারণ অনুযায়ী তালিকাভুক্ত।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**এটি আপনাকে দেখায় টাকা কোথায় গেছে, প্রতিটি উইন্ডোতে।**
আজ $২৫২.৪৭, এই সপ্তাহে $৫১৩.১৫, এই মাসে $১,৩১২.৯২, প্রতিটির পেছনের
টোকেন এবং আপনার সাবস্ক্রিপশন ইতিমধ্যে কতটা কভার করে তা সহ। তার নিচে,
প্রায় $১,১২৮/মাস পুনরুদ্ধারযোগ্য হিসেবে তালিকাভুক্ত এবং ক্যাশ পুনঃব্যবহারের
মাধ্যমে ইতিমধ্যে $১৭,২৫৬/মাস সাশ্রয় হয়েছে।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**এটি আঁকে কীভাবে একটি মেসেজ একটি উত্তরে পরিণত হয়।**
লাইভ ফ্লো ডায়াগ্রাম: আপনি, এটি যে চ্যানেলে এসেছে, গেটওয়ে, এখন উত্তর
দেওয়া মডেল, এবং প্রতিটি টুল যা এটি ব্যবহার করেছে। কাজ যত এগিয়ে যায়
নোডগুলো তত জ্বলে ওঠে।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**মেশিনের প্রতিটি এজেন্ট, একটি টেবিলে।**
এটি কী চালায়, গত ২৪ ঘণ্টায় এবং তার লাইফটাইমে এর খরচ কত, শেষ কবে দেখা
গেছে, কে এটির মালিক, এবং একটি সাবস্ক্রিপশন বিল কভার করছে কিনা। এখানে
১৪টি এজেন্ট, ৩টি সেশন কাজ করছে, ১৩টি নিষ্ক্রিয়।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**এটি দেখায় একটি টার্নের সময় এবং টাকা কোথায় গেল, টুল বাই টুল।**
একটি বাস্তব সেশনের একটি টার্ন: ১১.২ মিনিটে ১১টি টুল, $১.১৬ খরচে। প্রতিটি
Bash কল এবং মডেল কল টাইমলাইনে তার নিজস্ব বার পায়, তাই যে কমান্ডটি ৪.১
মিনিট চলেছিল এবং যেটি ২২৬ms চলেছিল তা এক নজরে আলাদা করা যায়।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**এটি কাজটির মান যাচাই করে, শুধু খরচ নয়।**
এই সপ্তাহে একটি A: ৫৪টি টাস্ক পরিষ্কারভাবে সম্পন্ন হয়েছে, ২টি এলোমেলো
টাস্কে খরচ হয়েছে $৪৮.৫৭, এবং যে রানগুলোতে বিচার করার মতো যথেষ্ট কার্যকলাপ
ছিল না সেগুলোকে জয় হিসেবে গণনা না করে গ্রেড থেকে বাদ রাখা হয়েছে। প্রতিটি
এলোমেলো রান তার ট্রেসের সাথে লিংক করা।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**এটি দেখায় কেন কনটেক্সট উইন্ডো ক্রমাগত ভরে যাচ্ছে।**
সর্বশেষ টার্নে ১M-টোকেন উইন্ডোর ৭১৫K, একটি ৮৩.৩% পিক, ৪টি কমপ্যাকশন যা
সবগুলো ওভারফ্লোতে না হয়ে প্রোঅ্যাকটিভভাবে ঘটেছে, সাথে এর পেছনের প্রতিটি
টার্নের ইউটিলাইজেশন।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**আপনাকে কিছু কনফিগার না করেই ডিটেকশন চলে।**
বিল্ট-ইন ডিটেক্টরগুলো ইনস্টলের পর থেকেই চালু: এজেন্ট চুপ হয়ে গেছে,
টেলিমেট্রি ফিড বন্ধ হয়ে গেছে, কস্ট স্পাইক, টোকেন বার্স্ট, এরর বাড়ছে,
এরর স্পাইক, বাজেট থ্রেশহোল্ড, থ্রেট সিগনেচার মিলেছে, সিকিউরিটি টুল
ফাইন্ডিং, সিকিউরিটি পসচার পরিবর্তিত হয়েছে। আপনার নিজের নিয়মগুলো এর
উপরে ঐচ্ছিক।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**একটি ঝুঁকিপূর্ণ কল ধরে রাখা অপ্ট-ইন, এবং ডিফল্টভাবে বন্ধ থাকে।**
রিকার্সিভ ডিলিট, ফোর্স পুশ, sudo, সিক্রেট, প্যাকেজ ইনস্টল এবং আউটবাউন্ড
কল প্রতিটির নিজস্ব একটি নিয়ম রয়েছে যা আপনি চালু করতে পারেন। যতক্ষণ না
আপনি সেটি করছেন, ClawMetry শুধু দেখে এবং কিছুই পরিবর্তন করে না। একবার
একটি চালু হলে, মিলে যাওয়া কলগুলো এখানে (অথবা আপনার ফোনে) অনুমোদন বা
প্রত্যাখ্যানের জন্য অপেক্ষা করে।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

আরও, প্রতিটি রানটাইম অনুযায়ী: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

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
