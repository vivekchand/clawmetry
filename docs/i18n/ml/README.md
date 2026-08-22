<!-- i18n-src:c111f32e69a5 -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **26 AI ഏജന്റ് റൺടൈമുകൾക്കായി** തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, കൂടാതെ വേറെ 22 എണ്ണം. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് ഈ ഭാഷകളിലും വായിക്കാം:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരു കമാൻഡ്. കോൺഫിഗറേഷൻ ഒന്നും വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തും.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കും. കോൺഫിഗറേഷൻ ആവശ്യമില്ല: നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകൾ ഇത് കണ്ടെത്തുന്നു, അവ റീഡ്-ഒൺലി ആയി വായിക്കുന്നു, അവ എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്നതിൽ ഒന്നും മാറ്റുന്നില്ല.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**പണം നൽകുന്ന പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

എല്ലാ റൺടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കും. ഒന്നിലധികം ഒരേസമയം പ്രവർത്തിപ്പിക്കൂ, ഹെഡറിലെ സ്വിച്ചർ ഓരോ ടാബും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

നിങ്ങൾ സ്വന്തമായി ഒരു SDK ഉപയോഗിച്ച് ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യും. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും എന്ത് ചെയ്തു, ഓരോ ടേണിലും, റീപ്ലേയോടെ
- **ചെലവും ടോക്കണുകളും**: ഓരോ റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവ പ്രകാരം, അസാധാരണത്വ ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ തത്സമയ ഡയഗ്രം
- **ബ്രെയിൻ**: സംഭവിക്കുന്ന നിമിഷം തന്നെയുള്ള റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ആരോഗ്യവും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, പിശക് നിരക്കുകൾ, റേറ്റ് ലിമിറ്റുകൾ, തത്സമയ ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബജറ്റ് പരിധികൾ, പിശക് കുതിച്ചുചാട്ടങ്ങൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യുന്നു
- **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ പ്രവർത്തിക്കുന്നതിന് *മുമ്പ്* താൽക്കാലികമായി നിർത്തുകയും നിങ്ങളുടെ ഫോണിൽ നിന്ന് അംഗീകരിക്കുകയും ചെയ്യുക ([എങ്ങനെ](docs/APPROVALS.md))

## വിലനിർണ്ണയം

| പ്ലാൻ | ഇത് എന്ത് ഉൾക്കൊള്ളുന്നു | വില |
|---|---|---|
| **സൗജന്യം** | OpenClaw + NVIDIA NemoClaw + Goose, പൂർണ്ണ ഡാഷ്ബോർഡ്, പ്രാദേശികം മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിലുള്ള മറ്റെല്ലാ റൺടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | ഒരു നോഡിന് $9 / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + ഗവേണൻസ്: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, ഇവാൾസ്, അസാധാരണത്വ കണ്ടെത്തൽ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel എക്സ്പോർട്ട് | ഒരു നോഡിന് $19 / മാസം |

വാർഷിക പ്ലാനുകൾ, എന്റർപ്രൈസ്, നിലവിലെ കണക്കുകൾ എന്നിവ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ഉണ്ട്. സ്വയം ഹോസ്റ്റ് ചെയ്ത ലൈസൻസ്
കീകൾ ക്ലൗഡ് ഇല്ലാതെയും പ്രവർത്തിക്കും (`clawmetry license`). സൗജന്യ/പണം നൽകുന്ന വിഭജനത്തിന്റെ കൃത്യമായ വിശദാംശങ്ങൾ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ ഉണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ നിലനിൽക്കുന്നു

ClawMetry പ്രാദേശിക സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ
നിങ്ങളുടെ ബോക്സിൽ നിന്ന് ഒന്നും പുറത്തുപോകുന്നില്ല. അപ്പോൾ പോലും, സ്നാപ്ഷോട്ട് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നത്
നിങ്ങളുടെ മെഷീനിൽ നിന്ന് ഒരിക്കലും പുറത്തുപോകാത്ത ഒരു കീ ഉപയോഗിച്ചാണ്, കൂടാതെ ഇത് നിങ്ങളുടെ ബ്രൗസറിൽ ഡീക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു.

## ഇൻസ്റ്റാൾ ചെയ്യുക

```bash
pip install clawmetry     # then: clawmetry
```

അല്ലെങ്കിൽ ഒറ്റ-ലൈൻ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux അല്ലെങ്കിൽ Windows-ൽ Python 3.8+ ഉം അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമും
ആവശ്യമാണ്. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

## ഡോക്യുമെന്റേഷൻ

| | |
|---|---|
| [റൺടൈം അനുയോജ്യത](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും എന്ത് വായിക്കുന്നു, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [എൻടൈറ്റിൽമെന്റുകൾ](docs/ENTITLEMENTS.md) | സൗജന്യം vs പണം നൽകുന്നത്, ടയർ മാട്രിക്സ്, ലൈസൻസ് CLI |
| [അപ്രൂവലുകളും പോളിസികളും](docs/APPROVALS.md) | പ്രീ-എക്സിക്യൂഷൻ ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | എവിടേക്കും ട്രെയ്സുകൾ എക്സ്പോർട്ട് ചെയ്യുക, എവിടെ നിന്നും OTLP ഇൻജെസ്റ്റ് ചെയ്യുക |
| [SDK ട്രാക്കിംഗ്](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് ആട്രിബ്യൂഷൻ |
| [ചാറ്റ് ചാനലുകൾ](docs/CHANNELS.md) | ഫ്ലോയിൽ കാണിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | സാൻഡ്ബോക്സ് ചെയ്ത NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, കമ്പോസ്, വോളിയം മൗണ്ടുകൾ |
| [ആർക്കിടെക്ചർ](ARCHITECTURE.md) · [ഡെവലപ്മെന്റ്](docs/DEVELOPMENT.md) | ഇത് അകത്ത് എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്‌സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കൽ |
| [ടെലിമെട്രി](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **അവലോകനം**: ടോക്കണുകൾ, സെഷനുകൾ, ആരോഗ്യം | **ബ്രെയിൻ**: തത്സമയ ഏജന്റ് ഇവന്റ് സ്ട്രീം |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **ചെലവ്**: മോഡലും സെഷനും പ്രകാരം | **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ ഗേറ്റ് ചെയ്യുന്നു |

കൂടുതൽ, ഓരോ റൺടൈം പ്രകാരവും: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## സ്റ്റാർ ചരിത്രം

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ലൈസൻസ്

MIT · [@vivekchand](https://github.com/vivekchand) നിർമ്മിച്ചത് · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
