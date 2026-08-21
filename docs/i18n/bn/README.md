<!-- i18n-src:dc34072b2955 -->
> বাংলা translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**আপনার এজেন্টের চিন্তাভাবনা দেখুন।** **২৩টি AI এজেন্ট রানটাইমের** জন্য রিয়েল-টাইম অবজার্ভেবিলিটি: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex এবং আরও ১৯টি। আপনার পুরো এজেন্ট ফ্লিটের জন্য একটি ড্যাশবোর্ড।

> 🌐 **এই ভাষায় পড়ুন:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [আরও →](docs/i18n/)

একটি কমান্ড। শূন্য কনফিগারেশন। সবকিছু স্বয়ংক্রিয়ভাবে শনাক্ত করে।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** এ খোলে। শূন্য কনফিগারেশন: এটি আপনার কাছে থাকা এজেন্ট রানটাইমগুলো খুঁজে বের করে, সেগুলো শুধু পড়ে (read-only), এবং সেগুলো কীভাবে চলে তাতে কোনো পরিবর্তন আনে না।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ২৩টি এজেন্ট রানটাইমের সাথে কাজ করে

**ওপেন সোর্স অ্যাপে বিনামূল্যে:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**পেইড প্ল্যানে:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

প্রতিটি রানটাইম একই ড্যাশবোর্ড পায়। একসাথে একাধিক চালান এবং হেডার সুইচার প্রতিটি ট্যাবকে তাদের যেকোনো একটির পরিসরে পুনরায় সাজিয়ে দেয়।

SDK দিয়ে নিজের এজেন্ট তৈরি করেছেন? ইন্টারসেপ্টর সেটির LLM কলও ট্র্যাক করে। দেখুন [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## আপনি যা পাবেন

- **সেশন ও ট্রান্সক্রিপ্ট**: প্রতিটি এজেন্ট ধাপে ধাপে কী করেছে, রিপ্লে সহ
- **খরচ ও টোকেন**: রানটাইম, মডেল, সেশন এবং দিন অনুযায়ী, অস্বাভাবিকতার সংকেত সহ
- **ফ্লো**: চ্যানেল, মডেল এবং টুলের মধ্য দিয়ে যাওয়া বার্তাগুলোর লাইভ ডায়াগ্রাম
- **ব্রেইন**: রিজনিং ও টুল-কল ইভেন্ট স্ট্রিম যেমনটা ঘটছে তখনই
- **মেমরি ও স্কিল**: প্রতিটি রানটাইম আসলে যে ফাইল ও স্কিল লোড করেছে
- **স্বাস্থ্য ও লগ**: ডিস্ক, মেমরি, এরর রেট, রেট লিমিট, লাইভ লগ স্ট্রিম
- **অ্যালার্ট**: বাজেট ক্যাপ, এরর স্পাইক, এজেন্ট-অফলাইন, যা Slack, Discord, PagerDuty, Telegram, Email-এ পাঠানো হয়
- **অ্যাপ্রুভাল**: ঝুঁকিপূর্ণ টুল কল চালানোর *আগে* বিরতি দিন এবং আপনার ফোন থেকে অনুমোদন করুন ([কীভাবে](docs/APPROVALS.md))

## মূল্য নির্ধারণ

| প্ল্যান | যা কভার করে | মূল্য |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, সম্পূর্ণ ড্যাশবোর্ড, শুধু লোকাল | $0 |
| **Starter** | উপরের বাকি সব রানটাইম, ফ্লিট ভিউ, ক্লাউড সিঙ্ক | নোড প্রতি মাসে $9 |
| **Pro** | Starter + গভর্নেন্স: অ্যাপ্রুভাল, টুল-রিস্ক পলিসি, ইভাল, অস্বাভাবিকতা শনাক্তকরণ, কস্ট অপটিমাইজার, OTel এক্সপোর্ট | নোড প্রতি মাসে $19 |

বার্ষিক প্ল্যান, এন্টারপ্রাইজ এবং হালনাগাদ সংখ্যা পাওয়া যাবে
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** এ। সেলফ-হোস্টেড লাইসেন্স
কী ক্লাউড ছাড়াই কাজ করে (`clawmetry license`)। সঠিক ফ্রি/পেইড বিভাজন আছে
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) এ।

## আপনার ডেটা আপনার মেশিনেই থাকে

ClawMetry লোকাল সেশন ফাইল ও লগ পড়ে। আপনি `clawmetry connect` না চালানো পর্যন্ত
কিছুই আপনার মেশিনের বাইরে যায় না। তখনও স্ন্যাপশটটি এমন একটি কী দিয়ে
এন্ড-টু-এন্ড এনক্রিপ্টেড থাকে যেটি কখনো আপনার মেশিন ছেড়ে যায় না, এবং
এটি আপনার ব্রাউজারে ডিক্রিপ্ট করা হয়।

## ইনস্টল করুন

```bash
pip install clawmetry     # তারপর: clawmetry
```

অথবা এক-লাইনার: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux বা Windows-এ Python 3.8+ প্রয়োজন, এবং একই মেশিনে অন্তত একটি এজেন্ট
রানটাইম প্রয়োজন। Docker নির্দেশনা: [docs/DOCKER.md](docs/DOCKER.md)।

## ডকুমেন্টেশন

| | |
|---|---|
| [রানটাইম কম্প্যাটিবিলিটি](docs/compatibility.md) | প্রতিটি অ্যাডাপ্টার কী পড়ে, এবং কীভাবে একটি রানটাইম যোগ করবেন |
| [Entitlements](docs/ENTITLEMENTS.md) | ফ্রি বনাম পেইড, টিয়ার ম্যাট্রিক্স, লাইসেন্স CLI |
| [অ্যাপ্রুভাল ও পলিসি](docs/APPROVALS.md) | প্রি-এক্সিকিউশন গেটিং, রিস্ক স্কোরিং, ফোন অ্যাপ্রুভাল |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | যেকোনো জায়গায় ট্রেস এক্সপোর্ট করুন, যেকোনো কিছু থেকে OTLP ইনজেস্ট করুন |
| [SDK ট্র্যাকিং](docs/SDK_TRACKING.md) | নিজে তৈরি করা এজেন্টদের জন্য খরচ অ্যাট্রিবিউশন |
| [চ্যাট চ্যানেল](docs/CHANNELS.md) | Flow-তে দেখানো চ্যাট অ্যাডাপ্টারগুলো |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | স্যান্ডবক্সড NVIDIA NemoClaw সেটআপ |
| [Docker](docs/DOCKER.md) | ইমেজ, কম্পোজ, ভলিউম মাউন্ট |
| [আর্কিটেকচার](ARCHITECTURE.md) · [ডেভেলপমেন্ট](docs/DEVELOPMENT.md) | ভেতরে কীভাবে কাজ করে; সোর্স থেকে চালানো |
| [টেলিমেট্রি](docs/TELEMETRY.md) | বেনামী ইনস্টল এবং ডেস্কটপ-ওপেন পিং, এবং সেগুলো কীভাবে বন্ধ করবেন |

## স্ক্রিনশট

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **ওভারভিউ**: টোকেন, সেশন, স্বাস্থ্য | **ব্রেইন**: লাইভ এজেন্ট ইভেন্ট স্ট্রিম |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **খরচ**: মডেল ও সেশন অনুযায়ী | **অ্যাপ্রুভাল**: ঝুঁকিপূর্ণ টুল কল গেট করুন |

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

MIT · তৈরি করেছেন [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
