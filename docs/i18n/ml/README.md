<!-- i18n-src:dc34072b2955 -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **23 AI ഏജന്റ് റൺടൈമുകൾ**ക്കായുള്ള തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & മറ്റ് 19 എണ്ണം. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരു ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് ഈ ഭാഷകളിൽ വായിക്കുക:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരു കമാൻഡ്. സീറോ കോൺഫിഗ്. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു. സീറോ കോൺഫിഗ്: നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകൾ ഇത് കണ്ടെത്തുന്നു, റീഡ്-ഒൺലി ആയി അവ വായിക്കുന്നു, അവ പ്രവർത്തിക്കുന്ന രീതിയിൽ ഒന്നും മാറ്റുന്നില്ല.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**പണമടച്ചുള്ള പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

എല്ലാ റൺടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കുന്നു. ഒരേസമയം പലതും പ്രവർത്തിപ്പിക്കൂ, ഹെഡറിലെ സ്വിച്ചർ ഓരോ ടാബും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

SDK ഉപയോഗിച്ച് സ്വന്തമായി ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും ചെയ്തത് എന്താണ്, ഓരോ ടേണിലും, റീപ്ലേയോടെ
- **ചെലവും ടോക്കണുകളും**: റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവ പ്രകാരം, അസാധാരണത്വ ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ തത്സമയ ഡയഗ്രം
- **ബ്രെയിൻ**: സംഭവിക്കുമ്പോൾ തന്നെയുള്ള റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ആരോഗ്യവും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, പിശക് നിരക്കുകൾ, റേറ്റ് ലിമിറ്റുകൾ, തത്സമയ ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബജറ്റ് കാപ്പുകൾ, പിശക് സ്‌പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യപ്പെടുന്നു
- **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ *പ്രവർത്തിക്കുന്നതിന് മുൻപ്* താൽക്കാലികമായി നിർത്തി നിങ്ങളുടെ ഫോണിൽ നിന്ന് അംഗീകരിക്കൂ ([എങ്ങനെ](docs/APPROVALS.md))

## വിലനിർണ്ണയം

| പ്ലാൻ | ഇത് ഉൾക്കൊള്ളുന്നത് | വില |
|---|---|---|
| **ഫ്രീ** | OpenClaw + NVIDIA NemoClaw, പൂർണ്ണ ഡാഷ്ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിൽ പറഞ്ഞ മറ്റെല്ലാ റൺടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | ഒരു നോഡിന് $9 / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + ഗവേണൻസ്: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, evals, അസാധാരണത്വ കണ്ടെത്തൽ, cost optimizer, OTel export | ഒരു നോഡിന് $19 / മാസം |

വാർഷിക പ്ലാനുകൾ, എന്റർപ്രൈസ്, നിലവിലെ കണക്കുകൾ എന്നിവ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ലഭ്യമാണ്. സെൽഫ്-ഹോസ്റ്റഡ് ലൈസൻസ്
കീകൾ ക്ലൗഡ് ഇല്ലാതെയും പ്രവർത്തിക്കും (`clawmetry license`). കൃത്യമായ ഫ്രീ/പെയ്ഡ് വിഭജനം
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ ഉണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ നിലനിൽക്കുന്നു

ClawMetry ലോക്കൽ സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ
നിങ്ങളുടെ ബോക്സിൽ നിന്ന് ഒന്നും പുറത്തുപോകില്ല. അപ്പോൾ പോലും, സ്നാപ്ഷോട്ട് നിങ്ങളുടെ മെഷീൻ വിട്ടുപോകാത്ത
ഒരു കീ ഉപയോഗിച്ച് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു, നിങ്ങളുടെ ബ്രൗസറിൽ ഡീക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു.

## ഇൻസ്റ്റാൾ ചെയ്യുക

```bash
pip install clawmetry     # then: clawmetry
```

അല്ലെങ്കിൽ ഒറ്റ-വരി കമാൻഡ്: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux അല്ലെങ്കിൽ Windows-ൽ Python 3.8+ ഉം, അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമും
ആവശ്യമാണ്. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

## ഡോക്യുമെന്റേഷൻ

| | |
|---|---|
| [റൺടൈം അനുയോജ്യത](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും എന്താണ് വായിക്കുന്നത്, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [Entitlements](docs/ENTITLEMENTS.md) | ഫ്രീ vs പെയ്ഡ്, ടയർ മാട്രിക്സ്, ലൈസൻസ് CLI |
| [അപ്രൂവലുകളും പോളിസികളും](docs/APPROVALS.md) | പ്രീ-എക്സിക്യൂഷൻ ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | എവിടെയും ട്രെയ്സുകൾ എക്സ്പോർട്ട് ചെയ്യുക, എവിടെ നിന്നും OTLP ഇൻജസ്റ്റ് ചെയ്യുക |
| [SDK ട്രാക്കിംഗ്](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കായുള്ള ചെലവ് ആട്രിബ്യൂഷൻ |
| [ചാറ്റ് ചാനലുകൾ](docs/CHANNELS.md) | ഫ്ലോയിൽ കാണിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | സാൻഡ്ബോക്സ്ഡ് NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, compose, വോളിയം മൗണ്ടുകൾ |
| [ആർക്കിടെക്ചർ](ARCHITECTURE.md) · [ഡെവലപ്മെന്റ്](docs/DEVELOPMENT.md) | ഇത് ഉള്ളിൽ എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്‌സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കൽ |
| [ടെലിമെട്രി](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **ഓവർവ്യൂ**: ടോക്കണുകൾ, സെഷനുകൾ, ആരോഗ്യം | **ബ്രെയിൻ**: തത്സമയ ഏജന്റ് ഇവന്റ് സ്ട്രീം |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **ചെലവ്**: മോഡലും സെഷനും അനുസരിച്ച് | **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ ഗേറ്റ് ചെയ്യുക |

കൂടുതൽ, ഓരോ റൺടൈമിനും അനുസരിച്ച്: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ലൈസൻസ്

MIT · നിർമ്മിച്ചത് [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
