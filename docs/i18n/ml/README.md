<!-- i18n-src:9767c8001c9c -->
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

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **30 AI ഏജന്റ് റൺടൈമുകൾക്കായുള്ള** തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, കൂടാതെ മറ്റ് 26 എണ്ണം. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് ഈ ഭാഷകളിൽ വായിക്കാം:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരു കമാൻഡ്. കോൺഫിഗ് വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കും. കോൺഫിഗ് വേണ്ട: ഇത് നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകൾ കണ്ടെത്തുന്നു, അവ റീഡ്-ഒൺലി ആയി വായിക്കുന്നു, അവ പ്രവർത്തിക്കുന്ന രീതിയിൽ ഒന്നും മാറ്റുന്നില്ല.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**പണമടച്ചുള്ള പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

എല്ലാ റൺടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കും. ഒരേസമയം പലതും പ്രവർത്തിപ്പിക്കൂ, ഹെഡർ സ്വിച്ചർ ഓരോ ടാബും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

SDK ഉപയോഗിച്ച് സ്വന്തമായി ഒരു ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും എന്ത് ചെയ്തു, ഓരോ ടേണിലും, റീപ്ലേ സഹിതം
- **ചെലവും ടോക്കണുകളും**: റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവ അനുസരിച്ച്, അനോമലി ഫ്ലാഗുകൾ സഹിതം
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ തത്സമയ ഡയഗ്രം
- **ബ്രെയിൻ**: നടക്കുന്നതുപോലെ, റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്**: ഓരോ പ്രൊവൈഡറിനും അനുസൃതമായി വലുപ്പം നിശ്ചയിച്ച വിൻഡോ ഉപയോഗം, കോംപാക്ഷൻ vs നിർബന്ധിത ഓവർഫ്ലോ, കൂടാതെ നമുക്ക് *കാണാൻ കഴിയാത്തതിന്റെ* റൺടൈം അനുസരിച്ചുള്ള ഒരു മാപ്പ് ([എങ്ങനെ](docs/CONTEXT_BLOWOUT.md))
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ഹെൽത്തും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, പിശക് നിരക്കുകൾ, റേറ്റ് ലിമിറ്റുകൾ, തത്സമയ ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബജറ്റ് പരിധികൾ, പിശക് സ്പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യപ്പെടുന്നു
- **അപ്രൂവലുകൾ**: അപകടസാധ്യതയുള്ള ടൂൾ കോളുകൾ അവ പ്രവർത്തിക്കുന്നതിന് *മുമ്പ്* നിർത്തിവയ്ക്കുകയും നിങ്ങളുടെ ഫോണിൽ നിന്ന് അംഗീകരിക്കുകയും ചെയ്യുക ([എങ്ങനെ](docs/APPROVALS.md))

## കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്, കൂടാതെ നിരീക്ഷിക്കാനുള്ള ചെലവ്

ഏതെങ്കിലും ഏജന്റ്-താരതമ്യ ടൂളിനെ വിശ്വസിക്കുന്നതിന് മുമ്പ് ഉത്തരം കണ്ടെത്തേണ്ട രണ്ട് ചോദ്യങ്ങൾ.

**റൺടൈമുകൾക്കിടയിലുള്ള കോൺടെക്സ്റ്റ്-വിൻഡോ ബ്ലോഔട്ട് ഇത് എങ്ങനെയാണ് കൈകാര്യം ചെയ്യുന്നത്?**

ഒരു ഉപയോഗ ശതമാനം അത് ഏത് സംഖ്യ കൊണ്ട് ഹരിക്കുന്നു എന്നത് പോലെ മാത്രമേ സത്യസന്ധമാകൂ. ClawMetry, Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM എന്നിവ ഉൾപ്പെടുന്ന നിങ്ങൾക്ക് വായിക്കാനും PR ചെയ്യാനും കഴിയുന്ന [ഒരു ടേബിളിൽ](clawmetry/context_windows.py) നിന്ന് ഓരോ പ്രൊവൈഡറിനും അനുസൃതമായി വിൻഡോയുടെ വലുപ്പം നിശ്ചയിക്കുന്നു. ഇത് 26 റൺടൈമുകളും ഒരു വെണ്ടറുടെ അളവുകോൽ ഉപയോഗിച്ച് അളക്കുന്നില്ല. അത് പ്രധാനമാണ്: Anthropic-ന്റെ 200K-നെതിരെ അളന്ന ഒരു 300K GPT-5 ടേൺ, "അത് GPT-5-ന്റെ 400K-ന്റെ 75% ആയിരിക്കുമ്പോൾ" ">100%, ബ്ലോൺ" എന്ന് കാണിക്കുന്നു. അതേ അളവുകോൽ, യഥാർത്ഥത്തിൽ ഓവർഫ്ലോ ആയ ഒരു 130K DeepSeek ടേണിനെ സൗകര്യപ്രദമായ 65% ആയി മറയ്ക്കുന്നു.

ഓരോ വിൻഡോയും അതിന്റെ ഉത്ഭവ വിവരങ്ങളോടെ (provenance) ആണ് വരുന്നത്: `model_table`, `explicit_marker`, `observed_floor`, അല്ലെങ്കിൽ മോഡൽ അറിയാത്തപ്പോൾ സത്യസന്ധമായ ഒരു `default`. ഒരു ഊഹത്തിൽ നിർമ്മിച്ച ഗേജ്, ഒരു ലുക്കപ്പിൽ നിർമ്മിച്ചതിന്റെ അതേ ആധികാരികതയോടെ ഒരിക്കലും റെൻഡർ ചെയ്യപ്പെടില്ല.

ClawMetry-ക്ക് ചില റൺടൈമുകളിൽ മാത്രമേ കോംപാക്ഷൻ ഇവന്റുകൾ കാണാൻ കഴിയൂ. അതിനാൽ `GET /api/context-coverage`, ഓരോ റൺടൈമിനും, ഒരു **പൂജ്യം "ശരിയായി പ്രവർത്തിച്ചു" എന്നാണോ അതോ "നമുക്ക് കാഴ്ചയില്ല" എന്നാണോ അർത്ഥമാക്കുന്നത്** എന്ന് റിപ്പോർട്ട് ചെയ്യുന്നു. യഥാർത്ഥത്തിൽ ബ്ലൈൻഡ് എന്നർത്ഥമുള്ള ഒരു `0`, അത് അങ്ങനെ തന്നെ പറയുന്നു.
[പൂർണ്ണ വിശദാംശം](docs/CONTEXT_BLOWOUT.md)

**ഈ ഇൻസ്ട്രുമെന്റേഷന്റെ ചെലവ് എത്രയാണ്?**

| പാത്ത് | നിങ്ങളുടെ ഏജന്റിലേക്ക് ചേർക്കപ്പെടുന്നത് | ഡിഫോൾട്ട്? |
|---|---|---|
| സെഷൻ-ഫയൽ ടെയിലിംഗ് (എല്ലാ 30 റൺടൈമുകളും) | **0**. പ്രത്യേക പ്രോസസ്, നിങ്ങളുടെ ഏജന്റിൽ ClawMetry കോഡ് ഇല്ല | ഓൺ |
| HTTP ഇന്റർസെപ്റ്റർ (`CLAWMETRY_INTERCEPT=1`) | LLM കോൾ ഒന്നിന് **+0.44 ms**, അല്ലെങ്കിൽ ഒരു 5s കോളിന്റെ 0.009% | ഓഫ് |
| പ്രീ-ടൂൾ ഹുക്ക് ഗേറ്റ് (warm cache) | ഒരു 36 ms ഇന്റർപ്രെറ്റർ ഫ്ലോറിന് മുകളിൽ, ഗേറ്റ് ചെയ്ത ടൂൾ കോൾ ഒന്നിന് **+44 ms** | ഓഫ് |
| എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സി | LLM കോൾ ഒന്നിന് **+9.7 ms** | ഓഫ് |

ഡെമൺ ഹോസ്റ്റ് ചെലവ്: **2,762 ഇവന്റുകൾ/സെക്കൻഡ്** ഇൻജസ്റ്റ്, ഡിസ്കിൽ **710 ബൈറ്റ്/ഇവന്റ്** (100k ഇവന്റുകൾക്ക് 67.7 MB), കൂടാതെ തിരക്കുള്ള ഒരു ഇൻസ്റ്റാളിൽ സ്ഥിരമായി **ഒരു കോറിന്റെ ~12%**. ആ അവസാന സംഖ്യ ഞങ്ങളുടെ സ്വന്തം പ്രഖ്യാപിത 5-10% ബജറ്റിന് മുകളിലാണ്, അതിനാൽ അത് പേജിൽ നിന്ന് ഒഴിവാക്കുന്നതിന് പകരം പിന്തുടരേണ്ട ഒരു ബഗ് ആയി പ്രസിദ്ധീകരിച്ചിരിക്കുന്നു.

Apple M2 Pro-യിൽ `benchmarks/overhead.py` ഉപയോഗിച്ച് അളന്നത്. ഹാർനെസ് ഓരോ കണ്ടീഷനും പ്രത്യേക പ്രോസസിൽ പ്രവർത്തിപ്പിക്കുന്നു, അവയുടെ ക്രമം മാറ്റിമറിക്കുന്നു, കൂടാതെ **റൗണ്ടുകൾ അതിന്റെ ചിഹ്നത്തിൽ (sign) വിയോജിക്കുമ്പോൾ ഒരു സംഖ്യ പ്രിന്റ് ചെയ്യാൻ വിസമ്മതിക്കുന്നു**. ഒരു മിനിറ്റിനുള്ളിൽ നിങ്ങളുടെ സ്വന്തം മെഷീനിൽ ഇത് പ്രവർത്തിപ്പിക്കൂ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ഹുക്ക് ഗേറ്റുകളും എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സിയും ഉൾപ്പെടെ എല്ലാ പാത്തും അളക്കപ്പെടുന്നു, കൂടാതെ ഹാർനെസ് CI-യിൽ Linux, macOS, Windows എന്നിവയിൽ പ്രവർത്തിക്കുന്നു. അറിഞ്ഞിരിക്കേണ്ട രണ്ട് ഫലങ്ങൾ: Windows-ൽ Linux-നേക്കാൾ ഏകദേശം ഏഴ് മടങ്ങ് കൂടുതൽ ചെലവ് പ്രോക്സിക്ക് വരുന്നു, കൂടാതെ ഡെമൺ നിലവിൽ ഞങ്ങളുടെ സ്വന്തം 5-10% ബജറ്റിന് മുകളിൽ, ഒരു കോറിന്റെ ഏകദേശം 12% സ്ഥിരമായി ഉപയോഗിക്കുന്നു. റോ JSON, രീതി, ഇപ്പോഴും അളക്കാത്തത് എന്നിവ [docs/OVERHEAD.md](docs/OVERHEAD.md) ൽ ഉണ്ട്.

## വിലനിർണ്ണയം

| പ്ലാൻ | ഇത് ഉൾക്കൊള്ളുന്നത് | വില |
|---|---|---|
| **സൗജന്യം** | OpenClaw + NVIDIA NemoClaw + Goose, പൂർണ്ണ ഡാഷ്ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിലുള്ള മറ്റെല്ലാ റൺടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | നോഡ് ഒന്നിന് $9 / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + കൺട്രോളും ഇവാലുവേഷനും: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, ഇവാലുകൾ, അനോമലി ഡിറ്റക്ഷൻ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel എക്സ്പോർട്ട്, ടാമ്പർ-എവിഡന്റ് ഓഡിറ്റ് ലോഗ് | നോഡ് ഒന്നിന് $19 / മാസം |

വാർഷിക പ്ലാനുകൾ, എന്റർപ്രൈസ്, നിലവിലെ സംഖ്യകൾ എന്നിവ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ഉണ്ട്. സ്വയം-ഹോസ്റ്റ് ചെയ്ത ലൈസൻസ്
കീകൾ ക്ലൗഡ് ഇല്ലാതെയും പ്രവർത്തിക്കും (`clawmetry license`). കൃത്യമായ സൗജന്യ/പണമടച്ചുള്ള വിഭജനം
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ ഉണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ തുടരുന്നു

ClawMetry ലോക്കൽ സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. **നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിച്ചില്ലെങ്കിൽ ഒരു സെഷൻ ഡാറ്റയും
നിങ്ങളുടെ ബോക്സിൽ നിന്ന് പുറത്തുപോകില്ല** — പ്രോംപ്റ്റുകൾ, മറുപടികൾ, ടൂൾ ആർഗ്യുമെന്റുകൾ, ഫയൽ
ഉള്ളടക്കങ്ങൾ അല്ലെങ്കിൽ ലോഗ് ലൈനുകൾ ഇല്ല. നിങ്ങൾ കണക്റ്റ് ചെയ്യുമ്പോൾ, സ്നാപ്പ്ഷോട്ട് നിങ്ങളുടെ മെഷീൻ വിട്ടുപോകാത്ത
ഒരു കീ ഉപയോഗിച്ച് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു, കൂടാതെ നിങ്ങളുടെ ബ്രൗസറിൽ ഡീക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു. ഒരു
നോഡിന് കീ ഇല്ലെങ്കിൽ, അപ്‌ലോഡ് വ്യക്തമായ ടെക്സ്റ്റിൽ അയക്കുന്നതിന് പകരം ഒഴിവാക്കപ്പെടും, കൂടാതെ
ഒരു സെർവർ പ്രതികരണത്തിനും അത് ഓഫ് ചെയ്യാൻ കഴിയില്ല.

നിങ്ങൾ കണക്റ്റ് ചെയ്യുന്നതിന് മുമ്പ് രണ്ട് കാര്യങ്ങൾ ഡിഫോൾട്ടായി പ്രവർത്തിക്കുന്നു, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ആണ്, സെഷൻ ഡാറ്റ
ഒന്നും വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI-ക്കെതിരായ ഒരു വേർഷൻ ചെക്കും. ഒരു ഡിഫോൾട്ട് ഇൻസ്റ്റാൾ, ഒരു
സ്റ്റാർട്ടപ്പ് ബാനർ ലൈനിനായി നിങ്ങളുടെ പബ്ലിക് IP ഒരിക്കൽ നോക്കുകയും ചെയ്യുന്നു. ഓരോ ലക്ഷ്യസ്ഥാനവും, അത് എന്ത് വഹിക്കുന്നു,
അത് എങ്ങനെ ഓഫ് ചെയ്യാം എന്നും [docs/EGRESS.md](docs/EGRESS.md) ൽ ലിസ്റ്റ് ചെയ്തിരിക്കുന്നു; സ്വയം-ഹോസ്റ്റ് ചെയ്തതും,
പുനർ-നിർദ്ദേശിച്ചതും, എയർ-ഗാപ്പ്ഡ് ചെയ്തതുമായ ഇൻസ്റ്റാളുകൾ ഒട്ടും discretionary ഔട്ട്ബൗണ്ട് കോളുകൾ നടത്തുന്നില്ല.

ഡീക്രിപ്ഷൻ നിങ്ങളുടെ ബ്രൗസറിൽ, ഞങ്ങൾ നിങ്ങൾക്ക് സേവിക്കുന്ന കോഡിൽ നടക്കുന്നു. അത് മുമ്പ്
ഒരു വാഗ്ദാനമായിരുന്നു; ഇപ്പോൾ അത് നിങ്ങൾക്ക് പരിശോധിക്കാവുന്ന ഒന്നാണ്. നിങ്ങളുടെ കീയെ സ്പർശിക്കുന്ന ഓരോ ലൈനും ഒരു
വായിക്കാവുന്ന ഫയലിൽ [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js) ഉണ്ട്,
ഇത് wheel-നുള്ളിൽ ഷിപ്പ് ചെയ്യുകയും, verbatim ആയി സേവിക്കുകയും, ഒരു Subresource
Integrity ഹാഷ് ഉപയോഗിച്ച് പിൻ ചെയ്യുകയും ചെയ്യുന്നു. ബ്രൗസർ ഞങ്ങൾ പ്രസിദ്ധീകരിച്ചത് തന്നെ പ്രവർത്തിപ്പിക്കുന്നു എന്ന്
സ്ഥിരീകരിക്കാൻ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ഇത് തെളിയിക്കാത്തത്: ഫയൽ ലോഡ് ചെയ്യുന്ന പേജ് ഞങ്ങൾ സേവിക്കുന്നു, അതിനാൽ ഞങ്ങൾക്ക് ഒരു
വ്യത്യസ്ത പേജ് സേവിക്കാൻ കഴിയും. Integrity ഹാഷുകൾ ഒരു കോംപ്രമൈസ്ഡ് CDN-ൽ നിന്ന് നിങ്ങളെ സംരക്ഷിക്കുന്നു,
വെണ്ടറിൽ നിന്നല്ല. ഏതൊരു substitution-ഉം ബോധപൂർവ്വമായതും, പേജ് സോഴ്‌സിൽ ദൃശ്യമായതും, ആർക്കും
ലഭ്യമാക്കാവുന്ന PyPI-യിലെ ഒരു ആർട്ടിഫാക്റ്റിൽ നിന്ന് വ്യത്യസ്തവുമായിരിക്കണം എന്നതാണ് നിങ്ങൾക്ക് ലഭിക്കുന്നത്. സ്വയം-ഹോസ്റ്റ്
ചെയ്യുകയോ ലോക്കൽ-ഒൺലി ആയി തുടരുകയോ ചെയ്യുന്നത് ഈ ആശ്രിതത്വത്തെ പൂർണ്ണമായും ഒഴിവാക്കുന്നു.

## ഇൻസ്റ്റാൾ

```bash
pip install clawmetry     # തുടർന്ന്: clawmetry
```

അല്ലെങ്കിൽ ഒരു-ലൈൻ കമാൻഡ്: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux അല്ലെങ്കിൽ Windows-ൽ Python 3.8+ ഉം, അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമും
ആവശ്യമാണ്. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

## ഡോക്യുമെന്റേഷൻ

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും വായിക്കുന്നത് എന്ത്, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ഓരോ പ്രൊവൈഡറിനുമുള്ള വിൻഡോകൾ, കോംപാക്ഷൻ vs ഓവർഫ്ലോ, ഓരോ റൺടൈമിനുമുള്ള കവറേജ് |
| [Overhead](docs/OVERHEAD.md) | ഇൻസ്ട്രുമെന്റേഷന്റെ ചെലവ്, അളന്നത്, പുനഃസൃഷ്ടിക്കാനുള്ള ഹാർനെസ് സഹിതം |
| [Entitlements](docs/ENTITLEMENTS.md) | സൗജന്യം vs പണമടച്ചുള്ളത്, ടയർ മാട്രിക്സ്, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | പ്രീ-എക്സിക്യൂഷൻ ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | എവിടേക്കും ട്രെയ്സുകൾ എക്സ്പോർട്ട് ചെയ്യുക, എവിടെനിന്നും OTLP ഇൻജസ്റ്റ് ചെയ്യുക |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, പ്രവർത്തിപ്പിക്കാവുന്ന ഉദാഹരണങ്ങൾ സഹിതം |
| [SDK tracking](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് അട്രിബ്യൂഷൻ |
| [Chat channels](docs/CHANNELS.md) | Flow-ൽ കാണിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | സാൻഡ്ബോക്സ്ഡ് NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, compose, വോള്യം മൗണ്ടുകൾ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ഇത് അകത്ത് എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്‌സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കൽ |
| [Telemetry](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

താഴെയുള്ള ഓരോ സംഖ്യയും ഒരു യഥാർത്ഥ മെഷീനിൽ നിന്നുള്ളതാണ്, റീഡ്-ഒൺലി ആയി, ഒന്നും സീഡ് ചെയ്യാതെ.

**എന്തെങ്കിലും തെറ്റാണ് എന്ന് ഇത് നിങ്ങളോട് പറയുന്നു, എന്ത് സംഭവിച്ചു എന്നത് മാത്രമല്ല.**
മുകളിൽ രണ്ട് അനോമലി ബാനറുകൾ: ചെലവ് ദൈനംദിന ശരാശരിയുടെ 7 മടങ്ങ് പ്രവർത്തിക്കുന്നു, കൂടാതെ ഒരു
4.2 മടങ്ങ് കോസ്റ്റ് സ്പൈക്ക്. അവയ്ക്ക് താഴെ, 667 സമീപകാല സെഷനുകളിൽ 324 എണ്ണത്തിലും ഒരു waste
സിഗ്നൽ ഉണ്ട്, കാരണം അനുസരിച്ച് itemised.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**പണം എവിടെ പോയി എന്ന് ഇത് നിങ്ങൾക്ക് കാണിക്കുന്നു, എല്ലാ വിൻഡോയിലും.**
ഇന്ന് $252.47, ഈ ആഴ്ച $513.15, ഈ മാസം $1,312.92, ഓരോന്നിനും പിന്നിലുള്ള ടോക്കണുകളും
നിങ്ങളുടെ സബ്സ്ക്രിപ്ഷൻ ഇതിനകം എത്ര കവർ ചെയ്യുന്നു എന്നും സഹിതം. അതിന് താഴെ, ഏകദേശം $1,128/മാസം
recoverable ആയി itemised, കൂടാതെ cache reuse വഴി ഇതിനകം $17,256/മാസം ലാഭിച്ചു.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ഒരു സന്ദേശം എങ്ങനെ ഒരു ഉത്തരമായി മാറുന്നു എന്ന് ഇത് വരയ്ക്കുന്നു.**
തത്സമയ ഫ്ലോ ഡയഗ്രം: നിങ്ങൾ, അത് വന്ന ചാനൽ, ഗേറ്റ്‌വേ, ഇപ്പോൾ ഉത്തരം നൽകുന്ന മോഡൽ, അത്
ഉപയോഗിച്ച ഓരോ ടൂളും. ജോലി അവയിലൂടെ നീങ്ങുമ്പോൾ നോഡുകൾ പ്രകാശിക്കുന്നു.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**മെഷീനിലെ ഓരോ ഏജന്റും, ഒരു ടേബിളിൽ.**
അത് എന്താണ് പ്രവർത്തിപ്പിക്കുന്നത്, കഴിഞ്ഞ 24 മണിക്കൂറിലും അതിന്റെ ജീവിതകാലത്തും അതിന് എത്ര ചെലവായി, അത്
അവസാനം എപ്പോൾ കണ്ടു, ആരാണ് ഉടമ, ഒരു സബ്സ്ക്രിപ്ഷൻ ബില്ല് കവർ ചെയ്യുന്നുണ്ടോ. ഇവിടെ 14 ഏജന്റുകൾ, 3
സെഷനുകൾ പ്രവർത്തിക്കുന്നു, 13 നിശബ്ദം.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ഒരു ടേണിന്റെ സമയവും പണവും എവിടെ പോയി എന്ന് ഇത് ടൂൾ അനുസരിച്ച് കാണിക്കുന്നു.**
ഒരു യഥാർത്ഥ സെഷന്റെ ഒരു ടേൺ: $1.16-ന് 11.2 മിനിറ്റിൽ 11 ടൂളുകൾ. ഓരോ Bash
കോളിനും മോഡൽ കോളിനും ടൈംലൈനിൽ അതിന്റേതായ ബാർ ഉണ്ട്, അതിനാൽ 4.1 മിനിറ്റ് പ്രവർത്തിച്ച കമാൻഡും
226ms പ്രവർത്തിച്ചതും ഒറ്റനോട്ടത്തിൽ വേർതിരിച്ചറിയാൻ കഴിയും.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ഇത് ജോലിയെ ഗ്രേഡ് ചെയ്യുന്നു, ചെലവിനെ മാത്രമല്ല.**
ഈ ആഴ്ച ഒരു A: 54 ടാസ്കുകൾ ശുദ്ധമായി തിരികെ വന്നു, 2 ബുദ്ധിമുട്ടുള്ളവയ്ക്ക് $48.57 ചെലവായി, കൂടാതെ
വിലയിരുത്താൻ മതിയായ പ്രവർത്തനം ഇല്ലാത്ത റണ്ണുകൾ വിജയങ്ങളായി കണക്കാക്കുന്നതിന് പകരം ഗ്രേഡിൽ നിന്ന്
ഒഴിവാക്കിയിരിക്കുന്നു. ഓരോ ബുദ്ധിമുട്ടുള്ള റണ്ണും അതിന്റെ ട്രെയ്സിലേക്ക് ലിങ്ക് ചെയ്യുന്നു.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**കോൺടെക്സ്റ്റ് വിൻഡോ എന്തുകൊണ്ട് നിറഞ്ഞുകൊണ്ടേയിരിക്കുന്നു എന്ന് ഇത് കാണിക്കുന്നു.**
1M-ടോക്കൺ വിൻഡോയിൽ ഏറ്റവും പുതിയ ടേണിൽ 715K, 83.3% peak, ഓവർഫ്ലോയിലല്ല proactively ട്രിഗർ
ചെയ്ത 4 കോംപാക്ഷനുകൾ, കൂടാതെ അതിന് പിന്നിലുള്ള ഓരോ ടേണിന്റെയും ഉപയോഗം.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**നിങ്ങൾ ഒന്നും കോൺഫിഗർ ചെയ്യാതെ തന്നെ ഡിറ്റക്ഷൻ പ്രവർത്തിക്കുന്നു.**
ബിൽറ്റ്-ഇൻ ഡിറ്റക്ടറുകൾ ഇൻസ്റ്റാൾ ചെയ്ത ഉടൻ ഓണാണ്: ഏജന്റ് നിശബ്ദമായി, ടെലിമെട്രി ഫീഡ്
നിലച്ചു, കോസ്റ്റ് സ്പൈക്ക്, ടോക്കൺ ബർസ്റ്റ്, പിശകുകൾ കൂടിവരുന്നു, പിശക് സ്പൈക്ക്, ബജറ്റ്
പരിധി, ഭീഷണി സിഗ്നേച്ചർ പൊരുത്തപ്പെട്ടു, സെക്യൂരിറ്റി ടൂൾ കണ്ടെത്തൽ, സെക്യൂരിറ്റി പൊസ്ചർ
മാറി. നിങ്ങളുടെ സ്വന്തം നിയമങ്ങൾ അതിന് മുകളിൽ ഓപ്ഷണൽ ആണ്.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**അപകടസാധ്യതയുള്ള ഒരു കോൾ പിടിച്ചുനിർത്തുന്നത് ഓപ്റ്റ്-ഇൻ ആണ്, ഓഫ് ആയാണ് ഷിപ്പ് ചെയ്യുന്നത്.**
Recursive deletes, force pushes, sudo, secrets, package installs, outbound
calls എന്നിവയ്ക്ക് ഓരോന്നിനും നിങ്ങൾക്ക് ഓൺ ചെയ്യാവുന്ന ഒരു നിയമം ഉണ്ട്. നിങ്ങൾ അത് ചെയ്യുന്നത് വരെ, ClawMetry
നിരീക്ഷിക്കുന്നു, ഒന്നും മാറ്റുന്നില്ല. ഒന്ന് ഓൺ ആയാൽ, പൊരുത്തപ്പെടുന്ന കോളുകൾ ഇവിടെ (അല്ലെങ്കിൽ നിങ്ങളുടെ ഫോണിൽ)
ഒരു അപ്രൂവ് അല്ലെങ്കിൽ ഡിനൈക്കായി കാത്തിരിക്കുന്നു.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

കൂടുതൽ, ഓരോ റൺടൈമിനും: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
