<!-- i18n-src:61beb8393e2f -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ഒരു ഏജന്റിന് പുരോഗതി ഒന്നും കൈവരിക്കാതെ തന്നെ നൂറു ടൂൾ കോളുകൾ നടത്താൻ കഴിയും.** നിങ്ങളുടെ കോഡിംഗ് ഏജന്റുകൾ ഇതിനകം എഴുതുന്ന സെഷൻ ഫയലുകൾ ClawMetry വായിക്കുകയും, ടൈംലൈൻ, ടൂൾ കോളുകൾ, റൺടൈം വെളിപ്പെടുത്തുന്ന ടോക്കൺ, ചെലവ് ഡാറ്റ എന്നിവ ഒരൊറ്റ കാഴ്ചയിലേക്ക് കൊണ്ടുവരികയും ചെയ്യുന്നു — അതിനാൽ പ്രവർത്തിക്കുന്ന ഒരു ദീർഘ റണ്ണിനെയും കുടുങ്ങിക്കിടക്കുന്ന ഒന്നിനെയും വേർതിരിച്ചറിയാൻ നിങ്ങൾക്ക് കഴിയും.

**30 AI ഏജന്റ് റൺടൈമുകളുമായി** പ്രവർത്തിക്കുന്നു — Claude Code, OpenAI Codex, Hermes, OpenClaw & മറ്റ് 26 എണ്ണം. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരു ഡാഷ്ബോർഡ്. ([പൂർണ്ണ പട്ടിക](SUPPORTED_RUNTIMES.txt), കാറ്റലോഗിൽ നിന്ന് ജനറേറ്റ് ചെയ്തത്.)

> 🌐 **ഇത് ഇവിടെ വായിക്കുക:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരു കമാൻഡ്. കോൺഫിഗ് ഒന്നും വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു. കോൺഫിഗ് ഒന്നും വേണ്ട: നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകളെ ഇത് കണ്ടെത്തുന്നു, അവയെ റീഡ്-ഒൺലി ആയി വായിക്കുന്നു, അവ എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്നതിൽ യാതൊന്നും മാറ്റുന്നില്ല.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ഇൻസ്റ്റാൾ ചെയ്യുന്നതിന് മുൻപ്

| | |
|---|---|
| **ഇത് എന്ത് ചെയ്യുന്നു** | നിങ്ങളുടെ ഏജന്റുകൾ ഇതിനകം എഴുതുന്ന സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. SDK ഇല്ല, കോഡ് മാറ്റം ഇല്ല, നിങ്ങളുടെ ആപ്പിൽ ഇൻസ്ട്രുമെന്റേഷൻ ഇല്ല. |
| **നിങ്ങൾ കാണുന്നത്** | സെഷൻ ടൈംലൈൻ, ടൂൾ-ബൈ-ടൂൾ റീപ്ലേ, ടോക്കണും ചെലവും ബ്രേക്ക്ഡൗൺ, ട്രാജക്ടറി സിഗ്നലുകൾ (ലൂപ്പിംഗ്, ആവർത്തിച്ചുള്ള പരാജയങ്ങൾ) — ഓരോ റൺടൈമിനും. |
| **എന്താണ് സൗജന്യം** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw, Goose** എന്നിവ അക്കൗണ്ടോ കീയോ നെറ്റ്‌വർക്ക് കോളോ ഇല്ലാതെ വായിക്കുന്നു. മറ്റ് 27 എണ്ണം — Claude Code, Codex, Cursor, ബാക്കിയുള്ളവയും — 7 ദിവസത്തെ ട്രയലിനോടോ ഒരു പ്ലാനിനോടോ കൂടെ വരുന്ന ക്ലോസ്ഡ്-സോഴ്സ് `clawmetry-pro` കമ്പാനിയൻ വായിക്കുന്നു — കൃത്യമായ വിഭജനത്തിനായി [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) കാണുക. |
| **എങ്ങനെ തുടങ്ങാം** | `pip install clawmetry && clawmetry`, പിന്നീട് localhost:8900 തുറക്കുക. ഈ മെഷീനിൽ ഏജന്റുകൾ ഇതുവരെ ഇല്ലേ? `clawmetry --sample` മൂന്ന് ലേബൽ ചെയ്ത സിന്തറ്റിക് സെഷനുകളിൽ തുറക്കുന്നു. |
| **നിങ്ങളുടെ മെഷീനിൽ നിന്ന് പുറത്തുപോകുന്നത്** | `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ സെഷൻ ഡാറ്റ ഒന്നും പുറത്തുപോകില്ല. രണ്ട് കാര്യങ്ങൾ ഡിഫോൾട്ടായി പ്രവർത്തിക്കുന്നു, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ചെയ്യാവുന്നവയും ഒന്നും സെഷൻ ഉള്ളടക്കം വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI പതിപ്പ് പരിശോധനയും. ഓരോ ലക്ഷ്യസ്ഥാനവും [docs/EGRESS.md](docs/EGRESS.md) ൽ പട്ടികപ്പെടുത്തിയിരിക്കുന്നു, കമന്റുകൾ വായിക്കുന്നതിന് പകരം ഒരു വയർ ക്യാപ്ചറിൽ നിന്ന് പുനർനിർമ്മിച്ചത്. |

നിങ്ങൾ ഫലം വിലയിരുത്തുന്നതിന് മുൻപ് അറിഞ്ഞിരിക്കേണ്ട രണ്ട് പരിധികൾ: റൺടൈമുകൾ വളരെ വ്യത്യസ്തമായ ഡാറ്റയാണ് വെളിപ്പെടുത്തുന്നത് (ചിലത് ചെലവ് ഒട്ടും പ്രസിദ്ധീകരിക്കുന്നില്ല — [മാട്രിക്സ്](docs/compatibility.md) ഓരോ റൺടൈമിനും ഏതൊക്കെയാണെന്ന് പറയുന്നു), കൂടാതെ ഒരു പ്രവർത്തനം നിരീക്ഷിക്കുന്നത് അതിനെ തടയാൻ കഴിയുന്നത് പോലെയല്ല ([ഏത് നിയന്ത്രണങ്ങളാണ് യഥാർത്ഥം, ഓരോ റൺടൈമിനും](docs/APPROVALS.md)).


## 30 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**പണമടച്ചുള്ള പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ഓരോ റൺടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കുന്നു. ഒരേസമയം പലതും പ്രവർത്തിപ്പിക്കൂ, ഹെഡർ സ്വിച്ചർ ഓരോ ടാബിനെയും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

SDK ഉപയോഗിച്ച് സ്വന്തമായി ഒരു ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും എന്താണ് ചെയ്തത്, ഊഴം അനുസരിച്ച്, റീപ്ലേയോടെ
- **ചെലവും ടോക്കണുകളും**: റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം അനുസരിച്ച്, അനോമലി ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ ലൈവ് ഡയഗ്രം
- **ബ്രെയിൻ**: റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം സംഭവിക്കുന്ന സമയത്ത് തന്നെ
- **കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്**: ദാതാവിനെ അടിസ്ഥാനമാക്കി സൈസ് ചെയ്ത വിൻഡോ യൂട്ടിലൈസേഷൻ, കോംപാക്ഷൻ vs ഫോഴ്‌സ്ഡ് ഓവർഫ്ലോ, കൂടാതെ നമുക്ക് *കാണാൻ കഴിയാത്തതിന്റെ* ഒരു റൺടൈം-അധിഷ്ഠിത മാപ്പ് ([എങ്ങനെ](docs/CONTEXT_BLOWOUT.md))
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ഹെൽത്തും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, എറർ റേറ്റുകൾ, റേറ്റ് ലിമിറ്റുകൾ, ലൈവ് ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബഡ്ജറ്റ് പരിധികൾ, എറർ സ്പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, ഇമെയിൽ എന്നിവയിലേക്ക് റൂട്ട് ചെയ്തത്
- **അപ്രൂവലുകൾ**: അപകടകരമായ ടൂൾ കോളുകൾ *അവ പ്രവർത്തിക്കുന്നതിന് മുൻപ്* പോസ് ചെയ്ത്, നിങ്ങളുടെ ഫോണിൽ നിന്ന് അംഗീകരിക്കുക ([എങ്ങനെ](docs/APPROVALS.md))

## കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്, നിരീക്ഷിക്കുന്നതിന്റെ ചെലവും

ഏതൊരു ഏജന്റ്-താരതമ്യ ടൂളിനെയും വിശ്വസിക്കുന്നതിന് മുൻപ് ഉത്തരം കണ്ടെത്തേണ്ട രണ്ട് ചോദ്യങ്ങൾ.

**റൺടൈമുകളിലുടനീളം കോൺടെക്സ്റ്റ്-വിൻഡോ ബ്ലോഔട്ട് ഇത് എങ്ങനെ കൈകാര്യം ചെയ്യുന്നു?**

ഒരു യൂട്ടിലൈസേഷൻ ശതമാനം അത് ഏത് സംഖ്യ കൊണ്ട് ഹരിക്കുന്നു എന്നതു പോലെ മാത്രമേ സത്യസന്ധമായിരിക്കൂ. Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM എന്നിവ ഉൾപ്പെടെ, നിങ്ങൾക്ക് വായിക്കാനും PR ചെയ്യാനും കഴിയുന്ന [ഒരു ടേബിളിൽ](clawmetry/context_windows.py) നിന്ന് ClawMetry ദാതാവിനെ അടിസ്ഥാനമാക്കി വിൻഡോ സൈസ് ചെയ്യുന്നു. ഇത് 30 റൺടൈമുകളും ഒരു വെണ്ടറുടെ അളവുകോൽ കൊണ്ട് അളക്കുന്നില്ല. അത് പ്രധാനമാണ്: Anthropic-ന്റെ 200K-നെതിരെ സ്കോർ ചെയ്യപ്പെടുന്ന ഒരു 300K GPT-5 ഊഴം ">100%, ബ്ലോൺ" എന്ന് വായിക്കുന്നു, യഥാർത്ഥത്തിൽ GPT-5-ന്റെ 400K-യുടെ 75% ആയിരിക്കുമ്പോൾ. അതേ അളവുകോൽ യഥാർത്ഥത്തിൽ ഓവർഫ്ലോ ആയ 130K DeepSeek ഊഴത്തെ സൗകര്യപ്രദമായ 65% ആയി മറയ്ക്കുന്നു.

ഓരോ വിൻഡോയും അതിന്റെ ഉത്ഭവസ്ഥാനത്തോടെ വരുന്നു: `model_table`, `explicit_marker`, `observed_floor`, അല്ലെങ്കിൽ മോഡൽ അറിയാത്തപ്പോൾ സത്യസന്ധമായ ഒരു `default`. ഒരു ഊഹത്തിൽ നിർമ്മിച്ച ഗേജ് ഒരു ലുക്കപ്പിൽ നിർമ്മിച്ചതിനെപ്പോലെ അതേ അധികാരത്തോടെ ഒരിക്കലും റെൻഡർ ചെയ്യില്ല.

ചില റൺടൈമുകളിൽ മാത്രമേ ClawMetry-ക്ക് കോംപാക്ഷൻ ഇവന്റുകൾ കാണാൻ കഴിയൂ. അതിനാൽ `GET /api/context-coverage`, ഓരോ റൺടൈമിനും, **പൂജ്യം എന്നാൽ "ക്ലീൻ ആയി ഓടി" എന്നാണോ "നമ്മൾ അന്ധരാണ്" എന്നാണോ** എന്ന് റിപ്പോർട്ട് ചെയ്യുന്നു. യഥാർത്ഥത്തിൽ അന്ധത അർത്ഥമാക്കുന്ന ഒരു `0` അങ്ങനെ പറയുന്നു.
[പൂർണ്ണ വിവരണം](docs/CONTEXT_BLOWOUT.md)

**ഇൻസ്ട്രുമെന്റേഷന് എന്ത് ചെലവ് വരും?**

| പാത | നിങ്ങളുടെ ഏജന്റിലേക്ക് കൂട്ടിച്ചേർത്തത് | ഡിഫോൾട്ടോ? |
|---|---|---|
| സെഷൻ-ഫയൽ ടെയിലിംഗ് (എല്ലാ 30 റൺടൈമുകളും) | **0**. പ്രത്യേക പ്രോസസ്, നിങ്ങളുടെ ഏജന്റിൽ ClawMetry കോഡ് ഇല്ല | ഓൺ |
| HTTP ഇന്റർസെപ്റ്റർ (`CLAWMETRY_INTERCEPT=1`) | ഓരോ LLM കോളിനും **+0.44 ms**, അഥവാ 5s കോളിന്റെ 0.009% | ഓഫ് |
| പ്രീ-ടൂൾ ഹുക്ക് ഗേറ്റ് (വാം കാഷെ) | 36 ms ഇന്റർപ്രെറ്റർ ഫ്ലോറിന് മുകളിൽ, ഗേറ്റ് ചെയ്ത ഓരോ ടൂൾ കോളിനും **+44 ms** | ഓഫ് |
| എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സി | ഓരോ LLM കോളിനും **+9.7 ms** | ഓഫ് |

ഡെമൺ ഹോസ്റ്റ് ചെലവ്: **2,762 ഇവന്റുകൾ/സെക്കൻഡ്** ഇൻജസ്റ്റ്, ഡിസ്കിൽ **710 ബൈറ്റ്/ഇവന്റ്**
(100k ഇവന്റുകൾക്ക് 67.7 MB), ബിസി ഇൻസ്റ്റാളിൽ **ഒരു കോറിന്റെ ~12%** സ്ഥിരമായി. ആ അവസാന സംഖ്യ ഞങ്ങൾ പ്രസ്താവിച്ച 5-10% ബഡ്ജറ്റിന് മുകളിലാണ്, അതിനാൽ അത് പേജിൽ നിന്ന് ഒഴിവാക്കുന്നതിന് പകരം പിന്തുടരേണ്ട ഒരു ബഗ് ആയി പ്രസിദ്ധീകരിച്ചിരിക്കുന്നു.

Apple M2 Pro-യിൽ `benchmarks/overhead.py` ഉപയോഗിച്ച് അളന്നത്. ഹാർനെസ് ഓരോ അവസ്ഥയും വെവ്വേറെ പ്രോസസിൽ പ്രവർത്തിപ്പിക്കുന്നു, അവയുടെ ക്രമം മാറ്റിമറിക്കുന്നു, കൂടാതെ **റൗണ്ടുകൾ അതിന്റെ ചിഹ്നത്തിൽ വിയോജിക്കുമ്പോൾ ഒരു സംഖ്യ പ്രിന്റ് ചെയ്യാൻ വിസമ്മതിക്കുന്നു**. ഒരു മിനിറ്റിനുള്ളിൽ ഇത് നിങ്ങളുടെ സ്വന്തം മെഷീനിൽ പ്രവർത്തിപ്പിക്കുക:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ഹുക്ക് ഗേറ്റുകളും എൻഫോഴ്‌സ്‌മെന്റ് പ്രോക്സിയും ഉൾപ്പെടെ, ഓരോ പാതയും അളക്കപ്പെടുന്നു, കൂടാതെ ഹാർനെസ് CI-യിൽ Linux, macOS, Windows എന്നിവയിൽ പ്രവർത്തിക്കുന്നു. അറിഞ്ഞിരിക്കേണ്ട രണ്ട് ഫലങ്ങൾ: Linux-നെ അപേക്ഷിച്ച് Windows-ൽ പ്രോക്സിക്ക് ഏകദേശം ഏഴ് മടങ്ങ് കൂടുതൽ ചെലവ് വരും, കൂടാതെ ഡെമൺ നിലവിൽ ഒരു കോറിന്റെ ഏകദേശം 12% നിലനിർത്തുന്നു, ഞങ്ങളുടെ സ്വന്തം 5-10% ബഡ്ജറ്റിന് മുകളിൽ. റോ JSON, രീതി, ഇനിയും അളക്കാത്തത് എന്നിവ [docs/OVERHEAD.md](docs/OVERHEAD.md) ൽ ഉണ്ട്.

## വിലനിർണ്ണയം

| പ്ലാൻ | അതിൽ ഉൾപ്പെടുന്നത് | വില |
|---|---|---|
| **സൗജന്യം** | OpenClaw + NVIDIA NemoClaw + Goose, പൂർണ്ണ ഡാഷ്ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിലുള്ള മറ്റെല്ലാ റൺടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | $9 ഓരോ നോഡിനും / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + നിയന്ത്രണവും മൂല്യനിർണ്ണയവും: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, evals, അനോമലി കണ്ടെത്തൽ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel എക്സ്പോർട്ട്, ടാമ്പർ-എവിഡന്റ് ഓഡിറ്റ് ലോഗ് | $19 ഓരോ നോഡിനും / മാസം |

വാർഷിക പ്ലാനുകൾ, എന്റർപ്രൈസ്, നിലവിലെ സംഖ്യകൾ എന്നിവ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ഉണ്ട്. സെൽഫ്-ഹോസ്റ്റഡ് ലൈസൻസ്
കീകൾ ക്ലൗഡ് ഇല്ലാതെ പ്രവർത്തിക്കും (`clawmetry license`). കൃത്യമായ ഫ്രീ/പെയ്ഡ് വിഭജനം
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ ഉണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ തുടരുന്നു

ClawMetry പ്രാദേശിക സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. **നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ സെഷൻ ഡാറ്റ ഒന്നും നിങ്ങളുടെ ബോക്സിൽ നിന്ന് പുറത്തുപോകില്ല** — പ്രോംപ്റ്റുകൾ, റിപ്ലൈകൾ, ടൂൾ ആർഗ്യുമെന്റുകൾ, ഫയൽ ഉള്ളടക്കങ്ങൾ, ലോഗ് ലൈനുകൾ എന്നിവ ഒന്നും ഇല്ല. നിങ്ങൾ കണക്റ്റ് ചെയ്യുമ്പോൾ, ഒരിക്കലും നിങ്ങളുടെ മെഷീനിൽ നിന്ന് പുറത്തുപോകാത്ത ഒരു കീ ഉപയോഗിച്ച് സ്നാപ്ഷോട്ട് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു, കൂടാതെ നിങ്ങളുടെ ബ്രൗസറിൽ ഡീക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു. ഒരു നോഡിന് കീ ഇല്ലെങ്കിൽ, അപ്‌ലോഡ് വ്യക്തമായ ടെക്സ്റ്റിൽ അയക്കുന്നതിന് പകരം സ്കിപ്പ് ചെയ്യപ്പെടുന്നു, കൂടാതെ ഒരു സെർവർ പ്രതികരണത്തിനും അത് ഓഫ് ചെയ്യാൻ കഴിയില്ല.

നിങ്ങൾ കണക്റ്റ് ചെയ്യുന്നതിന് മുൻപ് രണ്ട് കാര്യങ്ങൾ ഡിഫോൾട്ടായി പ്രവർത്തിക്കുന്നു, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ചെയ്യാവുന്നവയും ഒന്നും സെഷൻ ഡാറ്റ വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI-ക്കെതിരായ ഒരു പതിപ്പ് പരിശോധനയും. ഒരു ഡിഫോൾട്ട് ഇൻസ്റ്റാൾ ഒരു സ്റ്റാർട്ടപ്പ് ബാനർ ലൈനിനായി നിങ്ങളുടെ പബ്ലിക് IP ഒരു തവണ ലുക്ക്അപ്പ് ചെയ്യുകയും ചെയ്യും. ഓരോ ലക്ഷ്യസ്ഥാനവും, അത് എന്ത് വഹിക്കുന്നു, അത് എങ്ങനെ ഓഫ് ചെയ്യാം എന്നത് [docs/EGRESS.md](docs/EGRESS.md) ൽ ലിസ്റ്റ് ചെയ്തിരിക്കുന്നു; സെൽഫ്-ഹോസ്റ്റഡ്, റീപോയിന്റഡ്, എയർ-ഗാപ്ഡ് ഇൻസ്റ്റാളുകൾ ഒരു ഓപ്ഷണൽ ഔട്ട്ബൗണ്ട് കോളും നടത്തുന്നില്ല.

ഡീക്രിപ്ഷൻ നിങ്ങളുടെ ബ്രൗസറിൽ, ഞങ്ങൾ നിങ്ങൾക്ക് നൽകുന്ന കോഡിൽ സംഭവിക്കുന്നു. അത് ഒരു വാഗ്ദാനം ആയിരുന്നു; ഇപ്പോൾ അത് നിങ്ങൾക്ക് പരിശോധിക്കാവുന്ന ഒന്നാണ്. നിങ്ങളുടെ കീയെ സ്പർശിക്കുന്ന ഓരോ ലൈനും ഒരു വായിക്കാവുന്ന ഫയലിലാണ്, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ഇത് വീലിനുള്ളിൽ ഷിപ്പ് ചെയ്യുകയും, ഒരു Subresource Integrity ഹാഷ് ഉപയോഗിച്ച് പിൻ ചെയ്ത്, അതേപടി സെർവ് ചെയ്യുകയും ചെയ്യുന്നു. ബ്രൗസർ ഞങ്ങൾ പ്രസിദ്ധീകരിച്ചത് തന്നെയാണ് പ്രവർത്തിപ്പിക്കുന്നത് എന്ന് സ്ഥിരീകരിക്കാൻ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

അത് തെളിയിക്കാത്തത്: ഫയൽ ലോഡ് ചെയ്യുന്ന പേജ് ഞങ്ങൾ സെർവ് ചെയ്യുന്നു, അതിനാൽ ഞങ്ങൾക്ക് വ്യത്യസ്തമായ ഒരു പേജ് സെർവ് ചെയ്യാൻ കഴിയും. ഇന്റഗ്രിറ്റി ഹാഷുകൾ നിങ്ങളെ ഒരു കോംപ്രമൈസ്ഡ് CDN-ൽ നിന്ന് സംരക്ഷിക്കുന്നു, വെണ്ടറിൽ നിന്നല്ല. നിങ്ങൾക്ക് ലഭിക്കുന്നത് എന്തെന്നാൽ, ഏതൊരു പകരംവയ്ക്കലും മനഃപൂർവ്വമായിരിക്കണം, പേജ് സോഴ്സിൽ ദൃശ്യമായിരിക്കണം, ആർക്കും ഫെച്ച് ചെയ്യാൻ കഴിയുന്ന PyPI-യിലെ ഒരു ആർട്ടിഫാക്റ്റിൽ നിന്ന് വ്യത്യസ്തമായിരിക്കണം. സെൽഫ്-ഹോസ്റ്റിംഗ് അല്ലെങ്കിൽ ലോക്കൽ-ഒൺലി ആയി തുടരുന്നത് ഈ ആശ്രിതത്വത്തെ പൂർണ്ണമായും നീക്കം ചെയ്യുന്നു.

## ഇൻസ്റ്റാൾ ചെയ്യുക

```bash
pip install clawmetry     # then: clawmetry
```

അല്ലെങ്കിൽ ഒരു ലൈൻ കമാൻഡ്: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux, Windows എന്നിവയിൽ Python 3.8+ ഉം അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമും വേണം. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

അല്ലെങ്കിൽ ഏജന്റിനെ നിങ്ങൾക്കായി അത് സെറ്റ് അപ്പ് ചെയ്യാൻ അനുവദിക്കുക. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
സ്കിൽ Claude Code, Codex, Cursor, Gemini CLI, Copilot അല്ലെങ്കിൽ OpenCode-നെ
ClawMetry ഇൻസ്റ്റാൾ ചെയ്യാനും, മെഷീനിലെ ഏജന്റുകൾ എന്ത് ചെയ്യുന്നു എന്താണ് ചെലവഴിക്കുന്നത് എന്ന് റിപ്പോർട്ട് ചെയ്യാനും,
അഭ്യർത്ഥനയിൽ ഒരു സെഷൻ നിർത്താനും, അപകടകരമായ ടൂൾ കോളുകൾ അപ്രൂവലിനായി പിടിച്ചുവയ്ക്കാനും
പഠിപ്പിക്കുന്നു:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ഡോക്സ്

| | |
|---|---|
| [റൺടൈം കോംപാറ്റിബിലിറ്റി](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും എന്താണ് വായിക്കുന്നത്, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്](docs/CONTEXT_BLOWOUT.md) | ദാതാവ്-അധിഷ്ഠിത വിൻഡോകൾ, കോംപാക്ഷൻ vs ഓവർഫ്ലോ, റൺടൈം-അധിഷ്ഠിത കവറേജ് |
| [ഓവർഹെഡ്](docs/OVERHEAD.md) | ഇൻസ്ട്രുമെന്റേഷന് എന്ത് ചെലവ് വരും, അളന്നത്, അത് പുനർനിർമ്മിക്കാനുള്ള ഹാർനെസോടെ |
| [എൻടൈറ്റിൽമെന്റുകൾ](docs/ENTITLEMENTS.md) | ഫ്രീ vs പെയ്ഡ്, ടയർ മാട്രിക്സ്, ലൈസൻസ് CLI |
| [അപ്രൂവലുകളും പോളിസികളും](docs/APPROVALS.md) | പ്രീ-എക്സിക്യൂഷൻ ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ട്രെയ്സുകൾ എവിടെയും എക്സ്പോർട്ട് ചെയ്യുക, എന്തിൽ നിന്നും OTLP ഇൻജസ്റ്റ് ചെയ്യുക |
| [നിങ്ങളുടെ സ്വന്തം ഏജന്റ് കൊണ്ടുവരിക](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain അറ്റത്ത് നിന്ന് അറ്റം വരെ, പ്രവർത്തിക്കാവുന്ന ഉദാഹരണങ്ങളോടെ |
| [SDK ട്രാക്കിംഗ്](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് അട്രിബ്യൂഷൻ |
| [ചാറ്റ് ചാനലുകൾ](docs/CHANNELS.md) | ഫ്ലോയിൽ കാണിച്ചിരിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | സാൻഡ്ബോക്സ്ഡ് NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, കമ്പോസ്, വോളിയം മൗണ്ടുകൾ |
| [ആർക്കിടെക്ചർ](ARCHITECTURE.md) · [ഡെവലപ്മെന്റ്](docs/DEVELOPMENT.md) | ഇത് അകത്ത് എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കൽ |
| [ടെലിമെട്രി](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

താഴെയുള്ള ഓരോ സംഖ്യയും ഒരു യഥാർത്ഥ മെഷീനിൽ നിന്നാണ്, റീഡ്-ഒൺലി, ഒന്നും സീഡ് ചെയ്യാതെ.

**എന്തെങ്കിലും തെറ്റാണെന്ന് ഇത് നിങ്ങളോട് പറയുന്നു, എന്താണ് സംഭവിച്ചത് എന്ന് മാത്രമല്ല.**
മുകളിൽ രണ്ട് അനോമലി ബാനറുകൾ: ചെലവ് ദൈനംദിന ശരാശരിയുടെ 7 മടങ്ങ് പ്രവർത്തിക്കുന്നു, കൂടാതെ 4.2x കോസ്റ്റ് സ്പൈക്ക്. അവയ്ക്ക് താഴെ, അടുത്തിടെയുള്ള 667 സെഷനുകളിൽ 324 എണ്ണം ഒരു വേസ്റ്റ് സിഗ്നൽ വഹിക്കുന്നു, കാരണം അനുസരിച്ച് ഇനംതിരിച്ചത്.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**പണം എവിടെ പോയി എന്ന് ഇത് നിങ്ങൾക്ക് കാണിക്കുന്നു, ഓരോ വിൻഡോയിലും.**
ഇന്ന് $252.47, ഈ ആഴ്ച $513.15, ഈ മാസം $1,312.92, ഓരോന്നിനും പിന്നിലുള്ള ടോക്കണുകളോടും നിങ്ങളുടെ സബ്സ്ക്രിപ്ഷൻ ഇതിനകം എത്ര കവർ ചെയ്യുന്നു എന്നതോടും കൂടെ. അതിന് താഴെ, ഏകദേശം $1,128/മാസം വീണ്ടെടുക്കാവുന്നതായി ഇനംതിരിച്ചത്, കൂടാതെ കാഷെ പുനരുപയോഗം വഴി ഇതിനകം ലാഭിച്ച $17,256/മാസം.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ഒരു സന്ദേശം ഒരു ഉത്തരമായി എങ്ങനെ മാറുന്നു എന്ന് ഇത് വരയ്ക്കുന്നു.**
ലൈവ് ഫ്ലോ ഡയഗ്രം: നിങ്ങൾ, അത് വന്ന ചാനൽ, ഗേറ്റ്‌വേ, ഇപ്പോൾ ഉത്തരം നൽകുന്ന മോഡൽ, അത് എത്തിപ്പിടിച്ച ഓരോ ടൂളും. ജോലി അവയിലൂടെ നീങ്ങുന്നതിനനുസരിച്ച് നോഡുകൾ പ്രകാശിക്കുന്നു.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**മെഷീനിലെ ഓരോ ഏജന്റും, ഒരു ടേബിളിൽ.**
അത് എന്താണ് പ്രവർത്തിപ്പിക്കുന്നത്, കഴിഞ്ഞ 24 മണിക്കൂറിലും അതിന്റെ ജീവിതകാലം മുഴുവനിലും അതിന് എന്ത് ചെലവ് വരുന്നു, അത് അവസാനമായി എപ്പോൾ കണ്ടു, ആരാണ് അതിന്റെ ഉടമ, ഒരു സബ്സ്ക്രിപ്ഷൻ ബില്ല് കവർ ചെയ്യുന്നുണ്ടോ. ഇവിടെ 14 ഏജന്റുകൾ, 3 സെഷനുകൾ പ്രവർത്തിക്കുന്നു, 13 നിശബ്ദം.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ഒരു ഊഴത്തിന്റെ സമയവും പണവും ടൂൾ ബൈ ടൂൾ എവിടെ പോയി എന്ന് ഇത് കാണിക്കുന്നു.**
ഒരു യഥാർത്ഥ സെഷന്റെ ഒരു ഊഴം: 11.2 മിനിറ്റിൽ 11 ടൂളുകൾ $1.16-ന്. ഓരോ Bash
കോളിനും മോഡൽ കോളിനും ടൈംലൈനിൽ അതിന്റേതായ ബാർ ലഭിക്കുന്നു, അതിനാൽ 4.1 മിനിറ്റ്
പ്രവർത്തിച്ച കമാൻഡും 226ms പ്രവർത്തിച്ചതും ഒറ്റനോട്ടത്തിൽ വേർതിരിച്ചറിയാം.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ഇത് ജോലിയെ വിലയിരുത്തുന്നു, ചെലവ് മാത്രമല്ല.**
ഈ ആഴ്ച ഒരു A: 54 ടാസ്കുകൾ ക്ലീൻ ആയി തിരികെ വന്നു, 2 പരുക്കൻ ടാസ്കുകൾക്ക് $48.57 ചെലവായി, കൂടാതെ വിലയിരുത്താൻ വേണ്ടത്ര പ്രവർത്തനം ഇല്ലാത്ത റണ്ണുകൾ വിജയമായി എണ്ണുന്നതിന് പകരം ഗ്രേഡിൽ നിന്ന് ഒഴിവാക്കിയിരിക്കുന്നു. ഓരോ പരുക്കൻ റണ്ണും അതിന്റെ ട്രെയ്സിലേക്ക് ലിങ്ക് ചെയ്യുന്നു.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**കോൺടെക്സ്റ്റ് വിൻഡോ എന്തുകൊണ്ട് നിറഞ്ഞുകൊണ്ടിരിക്കുന്നു എന്ന് ഇത് കാണിക്കുന്നു.**
ഏറ്റവും പുതിയ ഊഴത്തിൽ 1M-ടോക്കൺ വിൻഡോയുടെ 715K, 83.3% പീക്ക്, ഓവർഫ്ലോയിലല്ല മറിച്ച് പ്രോആക്ടീവായി മാത്രം ഫയർ ചെയ്ത 4 കോംപാക്ഷനുകൾ, കൂടാതെ അതിന് പിന്നിലുള്ള ഓരോ ഊഴത്തിന്റെയും യൂട്ടിലൈസേഷൻ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**നിങ്ങൾ ഒന്നും കോൺഫിഗർ ചെയ്യാതെ തന്നെ ഡിറ്റക്ഷൻ പ്രവർത്തിക്കുന്നു.**
ബിൽറ്റ്-ഇൻ ഡിറ്റക്ടറുകൾ ഇൻസ്റ്റാൾ ചെയ്യുമ്പോൾ മുതൽ ഓൺ ആണ്: ഏജന്റ് നിശബ്ദമായി, ടെലിമെട്രി ഫീഡ്
നിലച്ചു, കോസ്റ്റ് സ്പൈക്ക്, ടോക്കൺ ബർസ്റ്റ്, ഉയരുന്ന എറർസ്, എറർ സ്പൈക്ക്, ബഡ്ജറ്റ്
ത്രെഷോൾഡ്, ത്രെഡ് സിഗ്നേച്ചർ പൊരുത്തപ്പെട്ടു, സെക്യൂരിറ്റി ടൂൾ കണ്ടെത്തൽ, സെക്യൂരിറ്റി പോസ്ചർ
മാറി. നിങ്ങളുടെ സ്വന്തം നിയമങ്ങൾ അതിനുമുകളിൽ ഓപ്ഷണൽ ആണ്.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**അപകടകരമായ ഒരു കോൾ പിടിച്ചുവയ്ക്കുന്നത് ഓപ്റ്റ്-ഇൻ ആണ്, ഓഫ് ആയാണ് ഷിപ്പ് ചെയ്യുന്നത്.**
റിക്കേഴ്സീവ് ഡിലീറ്റുകൾ, ഫോഴ്‌സ് പുഷുകൾ, sudo, രഹസ്യങ്ങൾ, പാക്കേജ് ഇൻസ്റ്റാളുകൾ, ഔട്ട്ബൗണ്ട്
കോളുകൾ എന്നിവയ്ക്ക് ഓരോന്നിനും നിങ്ങൾക്ക് ഓൺ ചെയ്യാവുന്ന ഒരു നിയമം ലഭിക്കുന്നു. നിങ്ങൾ അത് ചെയ്യുന്നത് വരെ, ClawMetry നിരീക്ഷിക്കുന്നു, ഒന്നും മാറ്റുന്നില്ല. ഒന്ന് ഓൺ ആയാൽ, പൊരുത്തപ്പെടുന്ന കോളുകൾ ഇവിടെ (അല്ലെങ്കിൽ നിങ്ങളുടെ ഫോണിൽ) ഒരു അംഗീകാരത്തിനോ നിരാകരണത്തിനോ വേണ്ടി കാത്തിരിക്കുന്നു.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

കൂടുതൽ, ഓരോ റൺടൈമിനും: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## അംഗീകാരം

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## സ്റ്റാർ ഹിസ്റ്ററി

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
