<!-- i18n-src:d21bea5161e0 -->
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

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **30 AI ഏജന്റ് റൺടൈമുകൾക്കായുള്ള** തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex കൂടാതെ 26 എണ്ണം കൂടി. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്‌ബോർഡ്.

> 🌐 **ഇത് ഈ ഭാഷകളിലും വായിക്കാം:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരൊറ്റ കമാൻഡ്. കോൺഫിഗ് ആവശ്യമില്ല. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു. കോൺഫിഗ് ആവശ്യമില്ല: നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകൾ ഇത് കണ്ടെത്തുന്നു, അവ റീഡ്-ഒൺലി ആയി വായിക്കുന്നു, അവ എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്നതിൽ ഒന്നും മാറ്റുന്നില്ല.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**പണമടച്ചുള്ള പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

എല്ലാ റൺടൈമിനും ഒരേ ഡാഷ്‌ബോർഡ് ലഭിക്കും. ഒന്നിലധികം ഒരേസമയം പ്രവർത്തിപ്പിക്കൂ, ഹെഡർ സ്വിച്ചർ ഓരോ ടാബിനെയും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

നിങ്ങൾ ഒരു SDK ഉപയോഗിച്ച് സ്വന്തം ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. കാണുക [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും ചെയ്തത് എന്താണ്, ടേൺ ബൈ ടേൺ, റീപ്ലേയോടെ
- **ചെലവും ടോക്കണുകളും**: ഓരോ റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവയ്ക്കായി, അനോമലി ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ തത്സമയ ഡയഗ്രം
- **ബ്രെയിൻ**: നടക്കുന്നത് പോലെ തന്നെ റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്**: ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ചുള്ള വിൻഡോ ഉപയോഗം, കോംപാക്ഷൻ vs നിർബന്ധിത ഓവർഫ്ലോ, കൂടാതെ നമുക്ക് *കാണാൻ കഴിയാത്തതിന്റെ* ഓരോ റൺടൈം അടിസ്ഥാനത്തിലുള്ള മാപ്പ് ([എങ്ങനെ](docs/CONTEXT_BLOWOUT.md))
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ആരോഗ്യവും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, പിശക് നിരക്കുകൾ, റേറ്റ് ലിമിറ്റുകൾ, തത്സമയ ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബജറ്റ് പരിധികൾ, പിശക് സ്പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യപ്പെടുന്നു
- **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ പ്രവർത്തിക്കുന്നതിന് *മുൻപ്* പോസ് ചെയ്യുകയും നിങ്ങളുടെ ഫോണിൽ നിന്ന് അംഗീകരിക്കുകയും ചെയ്യുക ([എങ്ങനെ](docs/APPROVALS.md))

## കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്, നിരീക്ഷണത്തിന്റെ ചെലവ്

ഏതൊരു ഏജന്റ്-താരതമ്യ ടൂളിനെയും വിശ്വസിക്കുന്നതിന് മുൻപ് ഉത്തരം നൽകേണ്ട രണ്ട് ചോദ്യങ്ങൾ.

**റൺടൈമുകളിലുടനീളമുള്ള കോൺടെക്സ്റ്റ്-വിൻഡോ ബ്ലോഔട്ട് ഇത് എങ്ങനെ കൈകാര്യം ചെയ്യുന്നു?**

ഒരു ഉപയോഗ ശതമാനം അത് ഏതിനെ വിഭജിക്കുന്നു എന്നതിനെപ്പോലെ മാത്രമേ സത്യസന്ധമാകൂ. ClawMetry, നിങ്ങൾക്ക് വായിക്കാനും PR ചെയ്യാനും കഴിയുന്ന [ഒരു ടേബിളിൽ](clawmetry/context_windows.py) നിന്ന് ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ച് വിൻഡോ വലുപ്പം നിശ്ചയിക്കുന്നു, ഇതിൽ Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM എന്നിവ ഉൾപ്പെടുന്നു. ഇത് 26 റൺടൈമുകളെയും ഒരു വെണ്ടറുടെ അളവുകോൽ ഉപയോഗിച്ച് അളക്കുന്നില്ല. അതു പ്രധാനമാണ്: Anthropicന്റെ 200K നൊപ്പം ഒരു 300K GPT-5 ടേൺ താരതമ്യം ചെയ്യുമ്പോൾ ">100%, ബ്ലോൺ" എന്ന് വായിക്കപ്പെടും, യഥാർത്ഥത്തിൽ അത് GPT-5ന്റെ 400Kന്റെ 75% മാത്രമാണെങ്കിലും. അതേ അളവുകോൽ യഥാർത്ഥത്തിൽ ഓവർഫ്ലോ ആയ 130K DeepSeek ടേണിനെ സുഖകരമായ 65% ആയി മറച്ചുവയ്ക്കുന്നു.

ഓരോ വിൻഡോയും അതിന്റെ പ്രോവനൻസോടെയാണ് വരുന്നത്: `model_table`, `explicit_marker`, `observed_floor`, അല്ലെങ്കിൽ മോഡൽ അറിയാത്തപ്പോൾ സത്യസന്ധമായ `default`. ഒരു ഊഹത്തിന്മേൽ നിർമ്മിച്ച ഗേജ് ഒരു ലുക്കപ്പിന്മേൽ നിർമ്മിച്ചതിന്റെ അതേ ആധികാരികതയോടെ ഒരിക്കലും റെൻഡർ ചെയ്യപ്പെടില്ല.

ClawMetryക്ക് ചില റൺടൈമുകളിൽ മാത്രമേ കോംപാക്ഷൻ ഇവന്റുകൾ കാണാൻ കഴിയൂ. അതിനാൽ `GET /api/context-coverage`, ഓരോ റൺടൈമിനും, **ഒരു പൂജ്യം "ക്ലീനായി ഓടി" എന്നാണോ അതോ "നമ്മൾ അന്ധരാണ്" എന്നാണോ** അർത്ഥമാക്കുന്നത് എന്ന് റിപ്പോർട്ട് ചെയ്യുന്നു. യഥാർത്ഥത്തിൽ അന്ധത അർത്ഥമാക്കുന്ന ഒരു `0`, അതങ്ങനെ തന്നെ പറയുന്നു.
[പൂർണ്ണ വിശദാംശം](docs/CONTEXT_BLOWOUT.md)

**ഇൻസ്ട്രുമെന്റേഷന്റെ ചെലവ് എത്രയാണ്?**

| പാത | നിങ്ങളുടെ ഏജന്റിലേക്ക് ചേർക്കുന്നത് | സ്ഥിരസ്ഥിതി? |
|---|---|---|
| സെഷൻ-ഫയൽ ടെയിലിംഗ് (എല്ലാ 30 റൺടൈമുകളും) | **0**. പ്രത്യേക പ്രോസസ്സ്, നിങ്ങളുടെ ഏജന്റിൽ ClawMetry കോഡ് ഇല്ല | ഓൺ |
| HTTP ഇന്റർസെപ്റ്റർ (`CLAWMETRY_INTERCEPT=1`) | ഓരോ LLM കോളിനും **+0.44 ms**, അല്ലെങ്കിൽ 5s കോളിന്റെ 0.009% | ഓഫ് |
| പ്രീ-ടൂൾ ഹുക്ക് ഗേറ്റ് (വാം കാഷെ) | 36 ms ഇന്റർപ്രെറ്റർ ഫ്ലോറിന് മുകളിൽ, ഓരോ ഗേറ്റഡ് ടൂൾ കോളിനും **+44 ms** | ഓഫ് |
| എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സി | ഓരോ LLM കോളിനും **+9.7 ms** | ഓഫ് |

ഡീമൺ ഹോസ്റ്റ് ചെലവ്: **2,762 ഇവന്റുകൾ/സെക്കൻഡ്** ഇൻജസ്റ്റ്, ഡിസ്കിൽ **710 ബൈറ്റ്/ഇവന്റ്**
(100k ഇവന്റുകൾക്ക് 67.7 MB), തിരക്കുള്ള ഒരു ഇൻസ്റ്റാളിൽ സ്ഥിരമായി **ഒരു കോറിന്റെ ~12%**. ആ അവസാന സംഖ്യ ഞങ്ങളുടെ സ്വന്തം 5-10% ബജറ്റിനേക്കാൾ കൂടുതലാണ്, അതിനാൽ പിന്തുടരേണ്ട ഒരു ബഗ് ആയി പ്രസിദ്ധീകരിക്കുന്നു, പേജിൽ നിന്ന് ഒഴിവാക്കിയിട്ടില്ല.

Apple M2 Pro-യിൽ `benchmarks/overhead.py` ഉപയോഗിച്ച് അളന്നത്. ഹാർനെസ്സ് ഓരോ കണ്ടീഷനും ഒരു പ്രത്യേക പ്രോസസ്സിൽ പ്രവർത്തിപ്പിക്കുന്നു, അവയുടെ ക്രമം മാറിമാറി വരുന്നു, കൂടാതെ **റൗണ്ടുകൾ അതിന്റെ ചിഹ്നത്തിൽ വിയോജിക്കുമ്പോൾ ഒരു സംഖ്യ പ്രിന്റ് ചെയ്യാൻ വിസമ്മതിക്കുന്നു**. ഇത് നിങ്ങളുടെ സ്വന്തം മെഷീനിൽ ഒരു മിനിറ്റിനുള്ളിൽ പ്രവർത്തിപ്പിക്കുക:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ഹുക്ക് ഗേറ്റുകളും എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സിയും ഉൾപ്പെടെ എല്ലാ പാതയും അളക്കപ്പെടുന്നു, ഹാർനെസ്സ് CI-യിൽ Linux, macOS, Windows എന്നിവയിൽ പ്രവർത്തിക്കുന്നു. അറിഞ്ഞിരിക്കേണ്ട രണ്ട് ഫലങ്ങൾ: Windowsൽ പ്രോക്സിക്ക് Linuxനേക്കാൾ ഏകദേശം ഏഴിരട്ടി ചെലവ് വരുന്നു, കൂടാതെ ഡീമൺ നിലവിൽ ഒരു കോറിന്റെ ഏകദേശം 12% സ്ഥിരമായി ഉപയോഗിക്കുന്നു, ഞങ്ങളുടെ സ്വന്തം 5-10% ബജറ്റിനേക്കാൾ കൂടുതൽ. റോ JSON, രീതി, ഇപ്പോഴും അളക്കപ്പെടാത്തത് എന്നിവ [docs/OVERHEAD.md](docs/OVERHEAD.md) ലുണ്ട്.

## വിലനിർണ്ണയം

| പ്ലാൻ | അതിൽ ഉൾപ്പെടുന്നത് | വില |
|---|---|---|
| **സൗജന്യം** | OpenClaw + NVIDIA NemoClaw + Goose, പൂർണ്ണ ഡാഷ്‌ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിൽ പറഞ്ഞ മറ്റെല്ലാ റൺടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | $9 ഓരോ നോഡിനും / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + കൺട്രോളും ഇവാലുവേഷനും: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, evals, അനോമലി ഡിറ്റക്ഷൻ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel എക്സ്പോർട്ട്, ടാമ്പർ-എവിഡന്റ് ഓഡിറ്റ് ലോഗ് | $19 ഓരോ നോഡിനും / മാസം |

വാർഷിക പ്ലാനുകളും, Enterprise-ഉം നിലവിലെ സംഖ്യകളും
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ഉണ്ട്. ക്ലൗഡ് ഇല്ലാതെ തന്നെ സെൽഫ്-ഹോസ്റ്റഡ് ലൈസൻസ്
കീകൾ പ്രവർത്തിക്കും (`clawmetry license`). സൗജന്യവും പണമടച്ചുള്ളതും തമ്മിലുള്ള കൃത്യമായ വിഭജനം
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ലുണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ നിലനിൽക്കുന്നു

ClawMetry ലോക്കൽ സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. **നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ ഒരു സെഷൻ ഡാറ്റയും നിങ്ങളുടെ ബോക്സിൽ നിന്ന് പുറത്തുപോകില്ല** — പ്രോംപ്റ്റുകളോ, മറുപടികളോ, ടൂൾ ആർഗ്യുമെന്റുകളോ, ഫയൽ ഉള്ളടക്കമോ, ലോഗ് ലൈനുകളോ ഇല്ല. നിങ്ങൾ കണക്ട് ചെയ്യുമ്പോൾ, സ്നാപ്ഷോട്ട് നിങ്ങളുടെ മെഷീനിൽ നിന്ന് ഒരിക്കലും പുറത്തുപോകാത്ത ഒരു കീ ഉപയോഗിച്ച് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുകയും, നിങ്ങളുടെ ബ്രൗസറിൽ ഡിക്രിപ്റ്റ് ചെയ്യപ്പെടുകയും ചെയ്യുന്നു. ഒരു നോഡിന് കീ ഇല്ലെങ്കിൽ, അപ്‌ലോഡ് ക്ലിയർ ടെക്സ്റ്റിൽ അയക്കുന്നതിന് പകരം ഒഴിവാക്കപ്പെടുന്നു, ഒരു സെർവർ പ്രതികരണത്തിനും അത് ഓഫ് ചെയ്യാൻ കഴിയില്ല.

നിങ്ങൾ കണക്ട് ചെയ്യുന്നതിന് മുൻപ് സ്ഥിരസ്ഥിതിയായി രണ്ട് കാര്യങ്ങൾ പ്രവർത്തിക്കും, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ചെയ്യാവുന്നവയാണ്, ഒന്നും സെഷൻ ഡാറ്റ വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI-ക്കെതിരായ ഒരു വേർഷൻ ചെക്കും. ഒരു സ്ഥിരസ്ഥിതി ഇൻസ്റ്റാൾ ഒരു സ്റ്റാർട്ടപ്പ് ബാനർ ലൈനിനായി നിങ്ങളുടെ പബ്ലിക് IP ഒരു തവണ നോക്കുന്നു. ഓരോ ലക്ഷ്യസ്ഥാനവും, അത് എന്ത് വഹിക്കുന്നു, അത് എങ്ങനെ ഓഫ് ചെയ്യാം എന്നിവ
[docs/EGRESS.md](docs/EGRESS.md) ൽ പട്ടികപ്പെടുത്തിയിട്ടുണ്ട്; സെൽഫ്-ഹോസ്റ്റഡ്, റീപോയിന്റഡ്, എയർ-ഗ്യാപ്ഡ് ഇൻസ്റ്റാളുകൾ
ഒരു discretionary ഔട്ട്ബൗണ്ട് കോളും ഉണ്ടാക്കുന്നില്ല.

ഡിക്രിപ്ഷൻ നിങ്ങളുടെ ബ്രൗസറിൽ, ഞങ്ങൾ നിങ്ങൾക്ക് നൽകുന്ന കോഡിൽ നടക്കുന്നു. അത് മുൻപ്
ഒരു വാഗ്ദാനമായിരുന്നു; ഇപ്പോൾ അത് നിങ്ങൾക്ക് പരിശോധിക്കാവുന്ന ഒന്നാണ്. നിങ്ങളുടെ കീ സ്പർശിക്കുന്ന ഓരോ വരിയും
ഒരൊറ്റ വായിക്കാവുന്ന ഫയലിലാണ്, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ഇത് wheel-നുള്ളിൽ ഷിപ്പ് ചെയ്യപ്പെടുകയും, verbatim ആയി സെർവ് ചെയ്യപ്പെടുകയും, ഒരു Subresource
Integrity ഹാഷ് ഉപയോഗിച്ച് പിൻ ചെയ്യപ്പെടുകയും ചെയ്യുന്നു. ബ്രൗസർ ഞങ്ങൾ പ്രസിദ്ധീകരിച്ചത് തന്നെ പ്രവർത്തിപ്പിക്കുന്നു എന്ന് സ്ഥിരീകരിക്കാൻ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ഇത് തെളിയിക്കാത്തത്: ഫയൽ ലോഡ് ചെയ്യുന്ന പേജ് ഞങ്ങൾ സെർവ് ചെയ്യുന്നു, അതിനാൽ ഞങ്ങൾക്ക് വ്യത്യസ്തമായ ഒരു
പേജ് സെർവ് ചെയ്യാൻ കഴിയും. Integrity ഹാഷുകൾ ഒരു കോംപ്രമൈസ്ഡ് CDN-ൽ നിന്ന് നിങ്ങളെ സംരക്ഷിക്കുന്നു,
വെണ്ടറിൽ നിന്നല്ല. നിങ്ങൾക്ക് ലഭിക്കുന്നത്, ഏതൊരു substitution-ഉം മന:പൂർവ്വമായതും, പേജ് സോഴ്‌സിൽ
ദൃശ്യമായതും, ആർക്കും ലഭ്യമാക്കാവുന്ന PyPI-യിലെ ഒരു ആർട്ടിഫാക്റ്റിൽ നിന്ന് വ്യത്യസ്തവുമായിരിക്കണം എന്നതാണ്.
സെൽഫ്-ഹോസ്റ്റ് ചെയ്യുന്നത് അല്ലെങ്കിൽ ലോക്കൽ-ഒൺലി ആയി തുടരുന്നത് ഈ ആശ്രിതത്വത്തെ പൂർണ്ണമായും ഒഴിവാക്കുന്നു.

## ഇൻസ്റ്റാൾ

```bash
pip install clawmetry     # തുടർന്ന്: clawmetry
```

അല്ലെങ്കിൽ ഒറ്റ-വരി കമാൻഡ്: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux അല്ലെങ്കിൽ Windows-ൽ Python 3.8+ ഉം, അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമും
ആവശ്യമാണ്. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

## ഡോക്യുമെന്റേഷൻ

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും വായിക്കുന്നത് എന്താണ്, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ചുള്ള വിൻഡോകൾ, കോംപാക്ഷൻ vs ഓവർഫ്ലോ, ഓരോ റൺടൈം കവറേജ് |
| [Overhead](docs/OVERHEAD.md) | ഇൻസ്ട്രുമെന്റേഷന്റെ ചെലവ്, അളന്നത്, അത് പുനർനിർമ്മിക്കാനുള്ള ഹാർനെസ്സ് സഹിതം |
| [Entitlements](docs/ENTITLEMENTS.md) | സൗജന്യം vs പണമടച്ചുള്ളത്, ടയർ മാട്രിക്സ്, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | എവിടെയും trace-കൾ എക്സ്പോർട്ട് ചെയ്യുക, എവിടെ നിന്നും OTLP ingest ചെയ്യുക |
| [SDK tracking](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് ആട്രിബ്യൂഷൻ |
| [Chat channels](docs/CHANNELS.md) | Flow-ൽ കാണിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, കമ്പോസ്, വോളിയം മൗണ്ടുകൾ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ഇത് അകത്ത് എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്‌സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കുന്നത് |
| [Telemetry](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

താഴെയുള്ള ഓരോ സംഖ്യയും ഒരു യഥാർത്ഥ മെഷീനിൽ നിന്നുള്ളതാണ്, റീഡ്-ഒൺലി, ഒന്നും സീഡ് ചെയ്യാതെ.

**എന്തെങ്കിലും തെറ്റാണെങ്കിൽ ഇത് നിങ്ങളോട് പറയുന്നു, എന്ത് സംഭവിച്ചു എന്ന് മാത്രമല്ല.**
മുകളിൽ രണ്ട് അനോമലി ബാനറുകൾ: ദിവസേനയുള്ള ശരാശരിയുടെ 7 ഇരട്ടി ചെലവ്, കൂടാതെ ഒരു
4.2x കോസ്റ്റ് സ്പൈക്ക്. അതിന് താഴെ, സമീപകാല 667 സെഷനുകളിൽ 324 എണ്ണം ഒരു waste
സിഗ്നൽ വഹിക്കുന്നു, കാരണം അനുസരിച്ച് itemized ചെയ്തിരിക്കുന്നു.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**പണം എവിടെ പോയി എന്ന് ഇത് നിങ്ങളെ കാണിക്കുന്നു, എല്ലാ വിൻഡോയിലും.**
ഇന്ന് $252.47, ഈ ആഴ്ച $513.15, ഈ മാസം $1,312.92, ഓരോന്നിനും പിന്നിലുള്ള ടോക്കണുകളും
നിങ്ങളുടെ സബ്സ്ക്രിപ്ഷൻ ഇതിനകം എത്ര കവർ ചെയ്യുന്നു എന്നതും ഉൾപ്പെടെ. അതിന് താഴെ,
ഏകദേശം $1,128/മാസം recoverable ആയി itemized ചെയ്തതും, cache reuse വഴി ഇതിനകം
$17,256/മാസം ലാഭിച്ചതും.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ഒരു സന്ദേശം എങ്ങനെ ഒരു ഉത്തരമായി മാറുന്നു എന്ന് ഇത് വരയ്ക്കുന്നു.**
തത്സമയ ഫ്ലോ ഡയഗ്രം: നിങ്ങൾ, അത് വന്ന ചാനൽ, ഗേറ്റ്‌വേ, ഇപ്പോൾ മറുപടി നൽകുന്ന
മോഡൽ, അത് ഉപയോഗിച്ച ഓരോ ടൂളും. ജോലി അവയിലൂടെ നീങ്ങുമ്പോൾ നോഡുകൾ പ്രകാശിക്കുന്നു.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**മെഷീനിലെ ഓരോ ഏജന്റും, ഒരു ടേബിളിൽ.**
അത് എന്താണ് പ്രവർത്തിപ്പിക്കുന്നത്, കഴിഞ്ഞ 24 മണിക്കൂറിലും അതിന്റെ ജീവിതകാലം മുഴുവനിലും അതിന്
എത്ര ചെലവ് വരുന്നു, അത് അവസാനം കണ്ടത് എപ്പോൾ, ആരാണ് ഉടമ, ഒരു സബ്സ്ക്രിപ്ഷൻ ബില്ല്
കവർ ചെയ്യുന്നുണ്ടോ എന്നത്. ഇവിടെ 14 ഏജന്റുകൾ, 3 സെഷനുകൾ പ്രവർത്തിക്കുന്നു, 13 നിശ്ചലം.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ഒരു ടേണിന്റെ സമയവും പണവും എവിടെ പോയി എന്ന് ഇത് ടൂൾ ബൈ ടൂൾ കാണിക്കുന്നു.**
ഒരു യഥാർത്ഥ സെഷന്റെ ഒരു ടേൺ: $1.16-ന് 11.2 മിനിറ്റിൽ 11 ടൂളുകൾ. ഓരോ Bash
കോളിനും മോഡൽ കോളിനും ടൈംലൈനിൽ അതിന്റേതായ ബാർ ലഭിക്കുന്നു, അതിനാൽ 4.1 മിനിറ്റ്
പ്രവർത്തിച്ച കമാൻഡും 226ms പ്രവർത്തിച്ചതും ഒറ്റനോട്ടത്തിൽ വേർതിരിച്ചറിയാൻ കഴിയും.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ഇത് ജോലിയെ ഗ്രേഡ് ചെയ്യുന്നു, ചെലവിനെ മാത്രമല്ല.**
ഈ ആഴ്ച ഒരു A: 54 ടാസ്കുകൾ ക്ലീനായി തിരികെ വന്നു, 2 റഫ് ആയവയ്ക്ക് $48.57 ചെലവായി,
വിലയിരുത്താൻ വളരെ കുറച്ച് പ്രവർത്തനം മാത്രമുള്ള റണ്ണുകൾ, വിജയങ്ങളായി കണക്കാക്കുന്നതിന്
പകരം ഗ്രേഡിൽ നിന്ന് ഒഴിവാക്കിയിരിക്കുന്നു. ഓരോ റഫ് റണ്ണും അതിന്റെ ട്രെയ്സിലേക്ക് ലിങ്ക് ചെയ്യുന്നു.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**കോൺടെക്സ്റ്റ് വിൻഡോ എന്തുകൊണ്ട് നിറഞ്ഞുകൊണ്ടിരിക്കുന്നു എന്ന് ഇത് കാണിക്കുന്നു.**
1M-ടോക്കൺ വിൻഡോയിൽ ഏറ്റവും പുതിയ ടേണിൽ 715K, 83.3% പീക്ക്, ഓവർഫ്ലോയിലല്ല
proactively ആയി മാത്രം ട്രിഗർ ചെയ്ത 4 കോംപാക്ഷനുകൾ, കൂടാതെ അതിന് പിന്നിലുള്ള ഓരോ ടേണിന്റെയും
ഉപയോഗം.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**നിങ്ങൾ ഒന്നും കോൺഫിഗർ ചെയ്യാതെ തന്നെ ഡിറ്റക്ഷൻ പ്രവർത്തിക്കുന്നു.**
ഇൻസ്റ്റാൾ ചെയ്തത് മുതൽ ബിൽറ്റ്-ഇൻ ഡിറ്റക്ടറുകൾ ഓണാണ്: ഏജന്റ് നിശബ്ദമായി, ടെലിമെട്രി ഫീഡ്
നിലച്ചു, കോസ്റ്റ് സ്പൈക്ക്, ടോക്കൺ ബർസ്റ്റ്, പിശകുകൾ ഉയരുന്നു, error spike, ബജറ്റ്
ത്രെഷോൾഡ്, threat signature പൊരുത്തപ്പെട്ടു, security tool ഫൈൻഡിംഗ്, സെക്യൂരിറ്റി പോസ്ചർ
മാറി. നിങ്ങളുടെ സ്വന്തം നിയമങ്ങൾ ഇതിന് മുകളിൽ ഓപ്ഷണൽ ആണ്.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**അപകടസാധ്യതയുള്ള ഒരു കോൾ പിടിച്ചുനിർത്തുന്നത് ഓപ്റ്റ്-ഇൻ ആണ്, ഓഫ് ആയാണ് ഷിപ്പ് ചെയ്യുന്നത്.**
Recursive delete-കൾ, force push-കൾ, sudo, secrets, package install-കൾ, outbound
കോളുകൾ എന്നിവയ്ക്ക് ഓരോന്നിനും നിങ്ങൾക്ക് ഓണാക്കാവുന്ന ഒരു നിയമം ഉണ്ട്. നിങ്ങൾ അത് ചെയ്യുന്നത് വരെ,
ClawMetry വീക്ഷിക്കുന്നു, ഒന്നും മാറ്റുന്നില്ല. ഒന്ന് ഓണായാൽ, പൊരുത്തപ്പെടുന്ന കോളുകൾ ഇവിടെ
(അല്ലെങ്കിൽ നിങ്ങളുടെ ഫോണിൽ) approve അല്ലെങ്കിൽ deny-ക്കായി കാത്തിരിക്കുന്നു.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

കൂടുതൽ, ഓരോ റൺടൈം അടിസ്ഥാനത്തിലും: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
