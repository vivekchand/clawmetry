<!-- i18n-src:88be2deff5d5 -->
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

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **30 AI ഏജന്റ് റണ്ടൈമുകൾക്കായുള്ള** തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & മറ്റ് 26 എണ്ണം. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് ഇനിപ്പറയുന്ന ഭാഷകളിലും വായിക്കാം:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരു കമാൻഡ്. കോൺഫിഗ് വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു. കോൺഫിഗ് വേണ്ട: നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റണ്ടൈമുകൾ ഇത് കണ്ടെത്തുന്നു, അവയെ റീഡ്-ഒൺലി ആയി വായിക്കുന്നു, അവ എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്നതിൽ ഒന്നും മാറ്റുന്നില്ല.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ഏജന്റ് റണ്ടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**പണമടച്ചുള്ള പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

എല്ലാ റണ്ടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കുന്നു. ഒന്നിലധികം ഒരേസമയം പ്രവർത്തിപ്പിക്കൂ, ഹെഡർ സ്വിച്ചർ ഓരോ ടാബിനെയും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

ഒരു SDK ഉപയോഗിച്ച് സ്വന്തമായി ഒരു ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. കാണുക [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും ചെയ്തത്, ടേൺ ബൈ ടേൺ, റീപ്ലേയോടെ
- **ചെലവും ടോക്കണുകളും**: റണ്ടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവ പ്രകാരം, അനോമലി ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ തത്സമയ ഡയഗ്രം
- **ബ്രെയിൻ**: സംഭവിക്കുന്ന സമയത്ത് തന്നെയുള്ള റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്**: ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ച് അളന്ന വിൻഡോ യൂട്ടിലൈസേഷൻ, കോംപാക്ഷൻ vs നിർബന്ധിത ഓവർഫ്ലോ, കൂടാതെ നമുക്ക് *കാണാൻ കഴിയാത്തതിന്റെ* റണ്ടൈം പ്രകാരമുള്ള മാപ്പ് ([എങ്ങനെ](docs/CONTEXT_BLOWOUT.md))
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റണ്ടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ഹെൽത്തും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, പിശക് നിരക്കുകൾ, റേറ്റ് ലിമിറ്റുകൾ, തത്സമയ ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബജറ്റ് പരിധികൾ, പിശക് സ്‌പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യപ്പെടുന്നു
- **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ പ്രവർത്തിക്കുന്നതിന് *മുൻപ്* താൽക്കാലികമായി നിർത്തി, നിങ്ങളുടെ ഫോണിൽ നിന്ന് അംഗീകരിക്കുക ([എങ്ങനെ](docs/APPROVALS.md))

## കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്, നിരീക്ഷിക്കുന്നതിന്റെ ചെലവ്

ഏതെങ്കിലും ഏജന്റ്-താരതമ്യ ടൂളിനെ വിശ്വസിക്കുന്നതിന് മുൻപ് ഉത്തരം കണ്ടെത്തേണ്ട രണ്ട് ചോദ്യങ്ങൾ.

**റണ്ടൈമുകളിലുടനീളമുള്ള കോൺടെക്സ്റ്റ്-വിൻഡോ ബ്ലോഔട്ട് ഇത് എങ്ങനെ കൈകാര്യം ചെയ്യുന്നു?**

ഒരു യൂട്ടിലൈസേഷൻ ശതമാനം അത് ഏതിനെ ഹരിക്കുന്നു എന്നതിനെ ആശ്രയിച്ച് മാത്രമേ വിശ്വസനീയമാകൂ. Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM എന്നിവ ഉൾക്കൊള്ളുന്ന, നിങ്ങൾക്ക് വായിക്കാനും PR ചെയ്യാനും കഴിയുന്ന [ഒരു ടേബിളിൽ](clawmetry/context_windows.py) നിന്ന് ClawMetry ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ച് വിൻഡോയുടെ വലുപ്പം നിശ്ചയിക്കുന്നു. ഒരു വെണ്ടറുടെ അളവുകോൽ ഉപയോഗിച്ച് 30 റണ്ടൈമുകളും അളക്കുന്നില്ല. അത് പ്രധാനമാണ്: Anthropic-ന്റെ 200K-നെതിരെ അളക്കുന്ന ഒരു 300K GPT-5 ടേൺ, GPT-5-ന്റെ 400K-യുടെ 75% മാത്രമായിരിക്കുമ്പോൾ ">100%, blown" എന്ന് വായിക്കപ്പെടും. അതേ അളവുകോൽ യഥാർത്ഥത്തിൽ ഓവർഫ്ലോ ആയ 130K DeepSeek ടേണിനെ സൗകര്യപ്രദമായ 65% ആയി മറയ്ക്കുന്നു.

ഓരോ വിൻഡോയും അതിന്റെ ഉത്ഭവ വിവരത്തോടെയാണ് വരുന്നത്: `model_table`, `explicit_marker`, `observed_floor`, അല്ലെങ്കിൽ മോഡൽ അറിയാത്തപ്പോൾ സത്യസന്ധമായ ഒരു `default`. ഊഹത്തിന്റെ അടിസ്ഥാനത്തിൽ നിർമ്മിച്ച ഒരു ഗേജ്, ഒരു ലുക്കപ്പിന്റെ അടിസ്ഥാനത്തിൽ നിർമ്മിച്ചതിന്റെ അതേ അധികാരത്തോടെ ഒരിക്കലും ദൃശ്യമാകില്ല.

ClawMetry-ക്ക് ചില റണ്ടൈമുകളിൽ മാത്രമേ കോംപാക്ഷൻ ഇവന്റുകൾ കാണാൻ കഴിയൂ. അതിനാൽ `GET /api/context-coverage`, ഓരോ റണ്ടൈമിനും, ഒരു പൂജ്യം അർത്ഥമാക്കുന്നത് **"വൃത്തിയായി ഓടി" എന്നാണോ അതോ "നമുക്ക് കാണാൻ കഴിയുന്നില്ല" എന്നാണോ** എന്ന് റിപ്പോർട്ട് ചെയ്യുന്നു. യഥാർത്ഥത്തിൽ കാഴ്ചയില്ലായ്മ അർത്ഥമാക്കുന്ന ഒരു `0` അങ്ങനെ പറയുന്നു.
[പൂർണ്ണ വിശദാംശം](docs/CONTEXT_BLOWOUT.md)

**ഇൻസ്ട്രുമെന്റേഷന് എന്ത് ചെലവ് വരും?**

| പാത | നിങ്ങളുടെ ഏജന്റിലേക്ക് ചേർക്കപ്പെടുന്നത് | ഡിഫോൾട്ട്? |
|---|---|---|
| സെഷൻ-ഫയൽ ടെയിലിംഗ് (എല്ലാ 30 റണ്ടൈമുകളും) | **0**. പ്രത്യേക പ്രോസസ്, നിങ്ങളുടെ ഏജന്റിൽ ClawMetry കോഡ് ഇല്ല | ഓൺ |
| HTTP ഇന്റർസെപ്റ്റർ (`CLAWMETRY_INTERCEPT=1`) | ഓരോ LLM കോളിനും **+0.44 ms**, അഥവാ 5s കോളിന്റെ 0.009% | ഓഫ് |
| പ്രീ-ടൂൾ ഹുക്ക് ഗേറ്റ് (warm cache) | ഗേറ്റ് ചെയ്ത ഓരോ ടൂൾ കോളിനും **+44 ms**, 36 ms ഇന്റർപ്രെറ്റർ ഫ്ലോറിന് മുകളിൽ | ഓഫ് |
| എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സി | ഓരോ LLM കോളിനും **+9.7 ms** | ഓഫ് |

ഡെമൺ ഹോസ്റ്റ് ചെലവ്: ഇൻജസ്റ്റ് **2,762 ഇവന്റുകൾ/സെക്കൻഡ്**, ഡിസ്കിൽ **710 ബൈറ്റ്/ഇവന്റ്** (100k ഇവന്റുകൾക്ക് 67.7 MB), തിരക്കേറിയ ഒരു ഇൻസ്റ്റാളിൽ സ്ഥിരമായി **ഒരു കോറിന്റെ ~12%**. ഞങ്ങൾ പ്രഖ്യാപിച്ച 5-10% ബജറ്റിനേക്കാൾ കൂടുതലാണ് ആ അവസാന സംഖ്യ, അതിനാൽ പേജിൽ നിന്ന് ഒഴിവാക്കുന്നതിന് പകരം പിന്തുടരേണ്ട ഒരു ബഗ് ആയി അത് പ്രസിദ്ധീകരിക്കുന്നു.

Apple M2 Pro-യിൽ `benchmarks/overhead.py` ഉപയോഗിച്ച് അളന്നത്. ഹാർനെസ് ഓരോ കണ്ടീഷനും വേറെ പ്രോസസിൽ ഓടിക്കുന്നു, അവയുടെ ക്രമം മാറ്റിമാറ്റുന്നു, കൂടാതെ **റൗണ്ടുകൾ അതിന്റെ ചിഹ്നത്തിൽ വിയോജിക്കുമ്പോൾ ഒരു സംഖ്യ പ്രിന്റ് ചെയ്യാൻ വിസമ്മതിക്കുന്നു**. ഒരു മിനിറ്റിനുള്ളിൽ നിങ്ങളുടെ സ്വന്തം മെഷീനിൽ ഇത് പ്രവർത്തിപ്പിക്കൂ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ഹുക്ക് ഗേറ്റുകളും എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സിയും ഉൾപ്പെടെ എല്ലാ പാതയും അളക്കപ്പെടുന്നു, ഹാർനെസ് CI-യിൽ Linux, macOS, Windows എന്നിവയിൽ പ്രവർത്തിക്കുന്നു. അറിഞ്ഞിരിക്കേണ്ട രണ്ട് ഫലങ്ങൾ: Linux-നെ അപേക്ഷിച്ച് Windows-ൽ പ്രോക്സിക്ക് ഏകദേശം ഏഴ് മടങ്ങ് കൂടുതൽ ചെലവാകുന്നു, കൂടാതെ ഡെമൺ നിലവിൽ ഏകദേശം ഒരു കോറിന്റെ 12% സ്ഥിരമായി ഉപയോഗിക്കുന്നു, ഇത് ഞങ്ങളുടെ സ്വന്തം 5-10% ബജറ്റിനേക്കാൾ കൂടുതലാണ്. റോ JSON, രീതി, ഇനിയും അളക്കാത്തത് എന്നിവ [docs/OVERHEAD.md](docs/OVERHEAD.md) ൽ ഉണ്ട്.

## വിലനിർണ്ണയം

| പ്ലാൻ | ഇത് ഉൾക്കൊള്ളുന്നത് | വില |
|---|---|---|
| **സൗജന്യം** | OpenClaw + NVIDIA NemoClaw + Goose, പൂർണ്ണ ഡാഷ്ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിലുള്ള മറ്റെല്ലാ റണ്ടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | $9 ഓരോ നോഡിനും / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + നിയന്ത്രണവും വിലയിരുത്തലും: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, evals, അനോമലി ഡിറ്റക്ഷൻ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel എക്സ്പോർട്ട്, ടാമ്പർ-എവിഡന്റ് ഓഡിറ്റ് ലോഗ് | $19 ഓരോ നോഡിനും / മാസം |

വാർഷിക പ്ലാനുകൾ, Enterprise, നിലവിലെ സംഖ്യകൾ എന്നിവ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ലഭ്യമാണ്. സെൽഫ്-ഹോസ്റ്റഡ് ലൈസൻസ്
കീകൾ ക്ലൗഡ് ഇല്ലാതെ പ്രവർത്തിക്കും (`clawmetry license`). കൃത്യമായ സൗജന്യ/പണമടച്ചുള്ള വിഭജനം
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ ഉണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ നിലനിൽക്കുന്നു

ClawMetry ലോക്കൽ സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. **നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ ഒരു സെഷൻ ഡാറ്റയും നിങ്ങളുടെ മെഷീനിൽ നിന്ന് പുറത്തുപോകില്ല** — പ്രോംപ്റ്റുകൾ, മറുപടികൾ, ടൂൾ ആർഗ്യുമെന്റുകൾ, ഫയൽ ഉള്ളടക്കങ്ങൾ, ലോഗ് ലൈനുകൾ എന്നിവയൊന്നും ഇല്ല. നിങ്ങൾ കണക്റ്റ് ചെയ്യുമ്പോൾ, ഒരിക്കലും നിങ്ങളുടെ മെഷീൻ വിട്ടുപോകാത്ത ഒരു കീ ഉപയോഗിച്ച് സ്നാപ്പ്ഷോട്ട് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു, നിങ്ങളുടെ ബ്രൗസറിൽ ഡീക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു. ഒരു നോഡിന് കീ ഇല്ലെങ്കിൽ, അപ്‌ലോഡ് വ്യക്തമായി അയക്കുന്നതിന് പകരം ഒഴിവാക്കപ്പെടുന്നു, ഒരു സെർവർ റെസ്പോൺസിനും അത് ഓഫ് ചെയ്യാൻ കഴിയില്ല.

നിങ്ങൾ കണക്റ്റ് ചെയ്യുന്നതിന് മുൻപ് തന്നെ, ഡിഫോൾട്ടായി രണ്ട് കാര്യങ്ങൾ പ്രവർത്തിക്കുന്നു, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ചെയ്യാവുന്നതും ഏതെങ്കിലും സെഷൻ ഡാറ്റ വഹിക്കാത്തതും: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI-ക്കെതിരായ ഒരു വേർഷൻ ചെക്കും. ഒരു ഡിഫോൾട്ട് ഇൻസ്റ്റാൾ ഒരു സ്റ്റാർട്ടപ്പ് ബാനർ ലൈനിനായി നിങ്ങളുടെ പബ്ലിക് IP ഒരു തവണ ലുക്ക് അപ്പ് ചെയ്യുന്നു. ഓരോ ഡെസ്റ്റിനേഷനും, അത് എന്ത് വഹിക്കുന്നു, അത് എങ്ങനെ ഓഫ് ചെയ്യാം എന്നതും [docs/EGRESS.md](docs/EGRESS.md) ൽ പട്ടികപ്പെടുത്തിയിരിക്കുന്നു; സെൽഫ്-ഹോസ്റ്റഡ്, റീപോയിന്റഡ്, എയർ-ഗ്യാപ്പ്ഡ് ഇൻസ്റ്റാളുകൾ ഒരു ഓപ്ഷണൽ ഔട്ട്ബൗണ്ട് കോളും ചെയ്യുന്നില്ല.

ഡീക്രിപ്ഷൻ നിങ്ങളുടെ ബ്രൗസറിൽ, ഞങ്ങൾ നിങ്ങൾക്ക് നൽകുന്ന കോഡിൽ സംഭവിക്കുന്നു. അത് മുൻപ് ഒരു വാഗ്ദാനമായിരുന്നു; ഇപ്പോൾ അത് നിങ്ങൾക്ക് പരിശോധിക്കാൻ കഴിയുന്ന ഒന്നാണ്. നിങ്ങളുടെ കീ സ്പർശിക്കുന്ന ഓരോ ലൈനും ഒരൊറ്റ വായിക്കാവുന്ന ഫയലിലാണ് ഉള്ളത്, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ഇത് wheel-ന്റെ ഉള്ളിൽ ഷിപ്പ് ചെയ്യപ്പെടുന്നു, അതേപടി സെർവ് ചെയ്യപ്പെടുന്നു, ഒരു Subresource Integrity ഹാഷിനൊപ്പം പിൻ ചെയ്യപ്പെട്ടിരിക്കുന്നു. ബ്രൗസർ ഞങ്ങൾ പ്രസിദ്ധീകരിച്ചത് തന്നെയാണ് പ്രവർത്തിപ്പിക്കുന്നത് എന്ന് സ്ഥിരീകരിക്കാൻ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ഇത് തെളിയിക്കാത്തത് എന്ത്: ഈ ഫയൽ ലോഡ് ചെയ്യുന്ന പേജ് ഞങ്ങൾ സെർവ് ചെയ്യുന്നു, അതിനാൽ ഞങ്ങൾക്ക് വ്യത്യസ്തമായ ഒരു പേജ് സെർവ് ചെയ്യാൻ കഴിയും. ഇന്റഗ്രിറ്റി ഹാഷുകൾ നിങ്ങളെ ഒരു കോംപ്രമൈസ്ഡ് CDN-ൽ നിന്ന് സംരക്ഷിക്കുന്നു, വെണ്ടറിൽ നിന്നല്ല. നിങ്ങൾക്ക് ലഭിക്കുന്നത് എന്തെന്നാൽ, ഏതൊരു മാറ്റിസ്ഥാപിക്കലും ബോധപൂർവമായതും, പേജ് സോഴ്‌സിൽ ദൃശ്യമായതും, ആർക്കും ലഭ്യമാക്കാൻ കഴിയുന്ന PyPI-യിലെ ഒരു ആർട്ടിഫാക്റ്റിൽ നിന്ന് വ്യത്യസ്തവുമായിരിക്കണം എന്നാണ്. സെൽഫ്-ഹോസ്റ്റിംഗ് അല്ലെങ്കിൽ ലോക്കൽ-ഒൺലി ആയി തുടരുന്നത് ഈ ആശ്രിതത്വത്തെ പൂർണ്ണമായും ഒഴിവാക്കുന്നു.

## ഇൻസ്റ്റാൾ

```bash
pip install clawmetry     # തുടർന്ന്: clawmetry
```

അല്ലെങ്കിൽ ഒറ്റ-വരി കമാൻഡ്: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux, Windows എന്നിവയിൽ Python 3.8+ ആവശ്യമാണ്, കൂടാതെ അതേ മെഷീനിൽ ഒരു ഏജന്റ് റണ്ടൈം എങ്കിലും വേണം. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

അല്ലെങ്കിൽ ഏജന്റിനെ ഇത് നിങ്ങൾക്കായി സെറ്റപ്പ് ചെയ്യാൻ അനുവദിക്കൂ. ClawMetry ഇൻസ്റ്റാൾ ചെയ്യാനും, മെഷീനിലെ ഏജന്റുകൾ എന്താണ് ചെയ്യുന്നതെന്നും ചെലവഴിക്കുന്നതെന്നും റിപ്പോർട്ട് ചെയ്യാനും, അഭ്യർത്ഥനയിൽ ഒരു സെഷൻ നിർത്താനും, അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ അംഗീകാരത്തിനായി പിടിച്ചുവയ്ക്കാനും Claude Code, Codex, Cursor, Gemini CLI, Copilot അല്ലെങ്കിൽ OpenCode-നെ പഠിപ്പിക്കുന്ന [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) സ്കിൽ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ഡോക്യുമെന്റേഷൻ

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും വായിക്കുന്നത്, ഒരു റണ്ടൈം എങ്ങനെ ചേർക്കാം |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ഓരോ പ്രൊവൈഡറിനും വിൻഡോകൾ, കോംപാക്ഷൻ vs ഓവർഫ്ലോ, ഓരോ റണ്ടൈമിന്റെയും കവറേജ് |
| [Overhead](docs/OVERHEAD.md) | ഇൻസ്ട്രുമെന്റേഷന് എന്ത് ചെലവ് വരും, അളന്നത്, പുനർനിർമ്മിക്കാനുള്ള ഹാർനെസോടെ |
| [Entitlements](docs/ENTITLEMENTS.md) | സൗജന്യം vs പണമടച്ചുള്ളത്, ടയർ മാട്രിക്സ്, ലൈസൻസ് CLI |
| [Approvals & policies](docs/APPROVALS.md) | പ്രീ-എക്സിക്യൂഷൻ ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ട്രെയ്സുകൾ എവിടെയും എക്സ്പോർട്ട് ചെയ്യുക, എവിടെ നിന്നും OTLP ഇൻജസ്റ്റ് ചെയ്യുക |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain അറ്റം മുതൽ അറ്റം വരെ, പ്രവർത്തിപ്പിക്കാവുന്ന ഉദാഹരണങ്ങളോടെ |
| [SDK tracking](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് അട്രിബ്യൂഷൻ |
| [Chat channels](docs/CHANNELS.md) | ഫ്ലോയിൽ കാണിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | സാൻഡ്‌ബോക്സ്ഡ് NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, compose, വോളിയം മൗണ്ടുകൾ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ഇത് ഉള്ളിൽ എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്‌സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കൽ |
| [Telemetry](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

താഴെയുള്ള ഓരോ സംഖ്യയും ഒരു യഥാർത്ഥ മെഷീനിൽ നിന്നുള്ളതാണ്, റീഡ്-ഒൺലി, ഒന്നും സീഡ് ചെയ്യാതെ.

**എന്ത് സംഭവിച്ചു എന്ന് മാത്രമല്ല, എപ്പോൾ എന്തെങ്കിലും തെറ്റാണ് എന്നും ഇത് നിങ്ങളോട് പറയുന്നു.**
മുകളിൽ രണ്ട് അനോമലി ബാനറുകൾ: ദിവസ ശരാശരിയുടെ 7 മടങ്ങ് ചെലവ്, 4.2 മടങ്ങ് കോസ്റ്റ് സ്പൈക്ക്. അതിന് താഴെ, 667 അടുത്തിടെയുള്ള സെഷനുകളിൽ 324 എണ്ണം ഒരു waste സിഗ്നൽ വഹിക്കുന്നു, കാരണം അനുസരിച്ച് ഇനംതിരിച്ചത്.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**പണം എവിടെപ്പോയി എന്ന് ഓരോ വിൻഡോയിലും ഇത് നിങ്ങളെ കാണിക്കുന്നു.**
ഇന്ന് $252.47, ഈ ആഴ്ച $513.15, ഈ മാസം $1,312.92, ഓരോന്നിന് പിന്നിലെ ടോക്കണുകളും നിങ്ങളുടെ സബ്സ്ക്രിപ്ഷൻ ഇതിനകം എത്ര കവർ ചെയ്യുന്നു എന്നതും സഹിതം. അതിന് താഴെ, ഏകദേശം $1,128/മാസം വീണ്ടെടുക്കാവുന്നതായി ഇനംതിരിച്ചത്, കാഷ് പുനരുപയോഗം വഴി ഇതിനകം $17,256/മാസം ലാഭിച്ചത്.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ഒരു സന്ദേശം എങ്ങനെ ഉത്തരമായി മാറുന്നു എന്ന് ഇത് വരയ്ക്കുന്നു.**
തത്സമയ ഫ്ലോ ഡയഗ്രം: നിങ്ങൾ, അത് വന്ന ചാനൽ, ഗേറ്റ്‌വേ, ഇപ്പോൾ ഉത്തരം നൽകുന്ന മോഡൽ, അത് ഉപയോഗിച്ച ഓരോ ടൂളും. ജോലി അവയിലൂടെ നീങ്ങുമ്പോൾ നോഡുകൾ പ്രകാശിക്കുന്നു.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**മെഷീനിലെ ഓരോ ഏജന്റും, ഒരൊറ്റ ടേബിളിൽ.**
അത് എന്ത് പ്രവർത്തിപ്പിക്കുന്നു, കഴിഞ്ഞ 24 മണിക്കൂറിലും അതിന്റെ ജീവിതകാലം മുഴുവനിലും അതിന്റെ ചെലവ് എത്ര, അത് അവസാനം കണ്ടത് എപ്പോൾ, ആരാണ് അതിന്റെ ഉടമ, ഒരു സബ്സ്ക്രിപ്ഷൻ ബിൽ കവർ ചെയ്യുന്നുണ്ടോ. ഇവിടെ 14 ഏജന്റുകൾ, 3 സെഷനുകൾ പ്രവർത്തിക്കുന്നു, 13 നിശബ്ദം.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ഒരു ടേണിന്റെ സമയവും പണവും എവിടെപ്പോയി എന്ന് ടൂൾ പ്രകാരം ഇത് കാണിക്കുന്നു.**
ഒരു യഥാർത്ഥ സെഷന്റെ ഒരു ടേൺ: $1.16 ന് 11.2 മിനിറ്റിൽ 11 ടൂളുകൾ. ഓരോ Bash കോളിനും മോഡൽ കോളിനും ടൈംലൈനിൽ അതിന്റേതായ ബാർ ലഭിക്കുന്നു, അതിനാൽ 4.1 മിനിറ്റ് ഓടിയ കമാൻഡും 226ms ഓടിയതും ഒറ്റനോട്ടത്തിൽ വേർതിരിച്ചറിയാം.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ചെലവ് മാത്രമല്ല, ജോലിയെയും ഇത് ഗ്രേഡ് ചെയ്യുന്നു.**
ഈ ആഴ്ച ഒരു A: 54 ടാസ്ക്കുകൾ വൃത്തിയായി തിരികെവന്നു, 2 പരുക്കൻ ടാസ്ക്കുകൾക്ക് $48.57 ചെലവായി, വിലയിരുത്താൻ വേണ്ടത്ര പ്രവർത്തനം ഇല്ലാത്ത റണ്ണുകൾ വിജയങ്ങളായി എണ്ണുന്നതിന് പകരം ഗ്രേഡിൽ നിന്ന് ഒഴിവാക്കപ്പെടുന്നു. ഓരോ പരുക്കൻ റണ്ണും അതിന്റെ ട്രെയ്സിലേക്ക് ലിങ്ക് ചെയ്യുന്നു.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**കോൺടെക്സ്റ്റ് വിൻഡോ എന്തുകൊണ്ട് നിറഞ്ഞുകൊണ്ടേയിരിക്കുന്നു എന്ന് ഇത് കാണിക്കുന്നു.**
അവസാന ടേണിൽ 1M-ടോക്കൺ വിൻഡോയുടെ 715K, 83.3% പീക്ക്, ഓവർഫ്ലോയിലല്ല, എല്ലാം മുൻകൂട്ടി ഫയർ ചെയ്ത 4 കോംപാക്ഷനുകൾ, കൂടാതെ അതിന് പിന്നിലെ ഓരോ ടേണിന്റെയും യൂട്ടിലൈസേഷൻ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**നിങ്ങൾ ഒന്നും കോൺഫിഗർ ചെയ്യാതെ തന്നെ ഡിറ്റക്ഷൻ പ്രവർത്തിക്കുന്നു.**
ബിൽറ്റ്-ഇൻ ഡിറ്റക്ടറുകൾ ഇൻസ്റ്റാൾ ചെയ്തതു മുതൽ ഓണാണ്: ഏജന്റ് നിശബ്ദമായി, ടെലിമെട്രി ഫീഡ് നിലച്ചു, കോസ്റ്റ് സ്പൈക്ക്, ടോക്കൺ ബർസ്റ്റ്, പിശകുകൾ കൂടുന്നു, പിശക് സ്പൈക്ക്, ബജറ്റ് പരിധി, ഭീഷണി സിഗ്നേച്ചർ പൊരുത്തപ്പെട്ടു, സെക്യൂരിറ്റി ടൂൾ കണ്ടെത്തൽ, സെക്യൂരിറ്റി പോസ്ചർ മാറ്റം. നിങ്ങളുടെ സ്വന്തം നിയമങ്ങൾ ഇതിന് മുകളിൽ ഓപ്ഷണലാണ്.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**അപകടസാധ്യതയുള്ള ഒരു കോൾ പിടിച്ചുവയ്ക്കൽ ഓപ്റ്റ്-ഇൻ ആണ്, ഓഫ് ആയാണ് ഷിപ്പ് ചെയ്യുന്നത്.**
Recursive ഡിലീറ്റുകൾ, force pushes, sudo, secrets, പാക്കേജ് ഇൻസ്റ്റാളുകൾ, ഔട്ട്ബൗണ്ട് കോളുകൾ എന്നിവയ്ക്കെല്ലാം നിങ്ങൾക്ക് ഓൺ ചെയ്യാവുന്ന ഒരു നിയമമുണ്ട്. നിങ്ങൾ ചെയ്യുന്നത് വരെ, ClawMetry നിരീക്ഷിക്കുന്നു, ഒന്നും മാറ്റുന്നില്ല. ഒന്ന് ഓണായിക്കഴിഞ്ഞാൽ, പൊരുത്തപ്പെടുന്ന കോളുകൾ ഇവിടെ (അല്ലെങ്കിൽ നിങ്ങളുടെ ഫോണിൽ) അംഗീകാരത്തിനോ നിരാകരണത്തിനോ വേണ്ടി കാത്തിരിക്കുന്നു.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

കൂടുതൽ, ഓരോ റണ്ടൈം പ്രകാരവും: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## സ്റ്റാർ ചരിത്രം

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
