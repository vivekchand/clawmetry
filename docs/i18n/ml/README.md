<!-- i18n-src:12b97259721e -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ഒരു ഏജന്റിന് പുരോഗതി ഒന്നും ഉണ്ടാക്കാതെ തന്നെ നൂറു ടൂൾ കോളുകൾ നടത്താൻ കഴിയും.** നിങ്ങളുടെ കോഡിംഗ് ഏജന്റുകൾ ഇതിനകം എഴുതുന്ന സെഷൻ ഫയലുകൾ ClawMetry വായിക്കുകയും, ടൈംലൈൻ, ടൂൾ കോളുകൾ, റൺടൈം വെളിപ്പെടുത്തുന്ന ടോക്കൺ, ചെലവ് ഡാറ്റ എന്നിവയെല്ലാം ഒരൊറ്റ വ്യൂവിൽ ഉൾപ്പെടുത്തുകയും ചെയ്യുന്നു — അതിനാൽ പ്രവർത്തിച്ചുകൊണ്ടിരിക്കുന്ന ഒരു ദീർഘമായ റണ്ണിനെ, കുടുങ്ങിപ്പോയ ഒന്നിൽ നിന്ന് വേർതിരിച്ചറിയാൻ നിങ്ങൾക്ക് കഴിയും.

**31 AI ഏജന്റ് റൺടൈമുകൾക്കൊപ്പം** പ്രവർത്തിക്കുന്നു — Claude Code, OpenAI Codex, Hermes, OpenClaw & മറ്റ് 27 എണ്ണം. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരു ഡാഷ്ബോർഡ്. ([പൂർണ്ണ ലിസ്റ്റ്](SUPPORTED_RUNTIMES.txt), കാറ്റലോഗിൽ നിന്ന് ജനറേറ്റ് ചെയ്തത്.)

> 🌐 **ഇത് ഇവിടെ വായിക്കുക:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ഒരു കമാൻഡ്. സീറോ കോൺഫിഗ്. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു. സീറോ കോൺഫിഗ്: നിങ്ങൾക്ക് ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകൾ ഇത് കണ്ടെത്തുന്നു, അവ read-only ആയി വായിക്കുന്നു, അവ എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്നതിൽ ഒന്നും മാറ്റുന്നില്ല.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ഇൻസ്റ്റാൾ ചെയ്യുന്നതിന് മുമ്പ്

| | |
|---|---|
| **ഇത് എന്ത് ചെയ്യുന്നു** | നിങ്ങളുടെ ഏജന്റുകൾ ഇതിനകം എഴുതുന്ന സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. SDK ഇല്ല, കോഡ് മാറ്റം ഇല്ല, നിങ്ങളുടെ ആപ്പിൽ instrumentation ഇല്ല. |
| **നിങ്ങൾ എന്ത് കാണുന്നു** | സെഷൻ ടൈംലൈൻ, ടൂൾ-ബൈ-ടൂൾ റീപ്ലേ, ടോക്കൺ, ചെലവ് ബ്രേക്ക്ഡൗൺ, ട്രാജക്ടറി സിഗ്നലുകൾ (looping, ആവർത്തിച്ചുള്ള പരാജയങ്ങൾ) — ഓരോ റൺടൈമിനും. |
| **എന്താണ് സൗജന്യം** | `pip install clawmetry` ഒരു അക്കൗണ്ടോ കീയോ നെറ്റ്‌വർക്ക് കോളോ ഇല്ലാതെ **OpenClaw, NVIDIA NemoClaw, Goose** എന്നിവ വായിക്കുന്നു. മറ്റ് 27 എണ്ണം — Claude Code, Codex, Cursor എന്നിവയും ബാക്കിയുള്ളവയും — ക്ലോസ്ഡ്-സോഴ്‌സ് `clawmetry-pro` കമ്പാനിയൻ വഴി വായിക്കപ്പെടുന്നു, ഇത് 7-ദിവസത്തെ ട്രയലിലോ ഒരു പ്ലാനിലോ ലഭ്യമാകുന്നു — കൃത്യമായ വിഭജനത്തിനായി [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) കാണുക. |
| **എങ്ങനെ തുടങ്ങാം** | `pip install clawmetry && clawmetry`, പിന്നെ localhost:8900 തുറക്കുക. ഈ മെഷീനിൽ ഇതുവരെ ഏജന്റുകൾ ഇല്ലേ? `clawmetry --sample` മൂന്ന് ലേബൽ ചെയ്ത സിന്തറ്റിക് സെഷനുകളിൽ തുറക്കുന്നു. |
| **നിങ്ങളുടെ മെഷീനിൽ നിന്ന് എന്ത് പുറത്തുപോകുന്നു** | നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ, സെഷൻ ഡാറ്റ ഒന്നും പുറത്തുപോകുന്നില്ല. ഡിഫോൾട്ടായി രണ്ട് കാര്യങ്ങൾ പ്രവർത്തിക്കുന്നു, രണ്ടും opt-out ചെയ്യാവുന്നവയാണ്, രണ്ടും സെഷൻ ഉള്ളടക്കം വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും ഒരു PyPI വേർഷൻ ചെക്കും. കമന്റുകൾ വായിക്കുന്നതിന് പകരം ഒരു വയർ ക്യാപ്ചറിൽ നിന്ന് പുനർനിർമ്മിച്ച, ഓരോ ഡെസ്റ്റിനേഷനും [docs/EGRESS.md](docs/EGRESS.md) ൽ ഇൻവെന്ററി ചെയ്തിരിക്കുന്നു. |

വിധി പറയുന്നതിന് മുമ്പ് അറിഞ്ഞിരിക്കേണ്ട രണ്ട് പരിമിതികൾ: റൺടൈമുകൾ വളരെ വ്യത്യസ്തമായ ഡാറ്റ വെളിപ്പെടുത്തുന്നു (ചിലത് ചെലവ് ഒട്ടും പ്രസിദ്ധീകരിക്കുന്നില്ല — ഏതെല്ലാം എന്ന് [മാട്രിക്സ്](docs/compatibility.md) പറയുന്നു, ഓരോ റൺടൈമിനും), കൂടാതെ ഒരു പ്രവർത്തനം നിരീക്ഷിക്കുന്നത് അത് തടയാൻ കഴിയുന്നതിന് തുല്യമല്ല ([ഏതെല്ലാം കൺട്രോളുകൾ യഥാർത്ഥമാണ്, ഓരോ റൺടൈമിനും](docs/APPROVALS.md)).


## 31 ഏജന്റ് റൺടൈമുകൾക്കൊപ്പം പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യം:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ഒരു പണമടച്ചുള്ള പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

എല്ലാ റൺടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കുന്നു. ഒരേ സമയം പലതും പ്രവർത്തിപ്പിക്കുക, ഹെഡർ സ്വിച്ചർ ഓരോ ടാബും അവയിലൊന്നിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യും.

ഒരു SDK ഉപയോഗിച്ച് സ്വന്തമായി ഒരു ഏജന്റ് നിർമ്മിച്ചോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) കാണുക.

## നിങ്ങൾക്ക് എന്ത് ലഭിക്കുന്നു

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും എന്ത് ചെയ്തു, ടേൺ ബൈ ടേൺ, റീപ്ലേ സഹിതം
- **ചെലവും ടോക്കണുകളും**: ഓരോ റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവയ്ക്കും, ആനോമലി ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന സന്ദേശങ്ങളുടെ ലൈവ് ഡയഗ്രം
- **ബ്രെയിൻ**: അത് സംഭവിക്കുന്ന സമയത്ത് തന്നെ, റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്**: ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ച് വലുപ്പം നിശ്ചയിച്ച വിൻഡോ ഉപയോഗം, compaction vs forced overflow, കൂടാതെ നമുക്ക് *കാണാൻ കഴിയാത്തത്* എന്താണെന്നതിന്റെ ഒരു per-runtime മാപ്പ് ([എങ്ങനെ](docs/CONTEXT_BLOWOUT.md))
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ഹെൽത്തും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, എറർ റേറ്റുകൾ, റേറ്റ് ലിമിറ്റുകൾ, ലൈവ് ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബജറ്റ് ക്യാപ്പുകൾ, എറർ സ്പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യപ്പെടുന്നു
- **അപ്രൂവലുകൾ**: അപകടകരമായ ടൂൾ കോളുകൾ *അവ പ്രവർത്തിക്കുന്നതിന് മുമ്പ്* പോസ് ചെയ്യുകയും നിങ്ങളുടെ ഫോണിൽ നിന്ന് അപ്രൂവ് ചെയ്യുകയും ചെയ്യുക ([എങ്ങനെ](docs/APPROVALS.md))

## കോൺടെക്സ്റ്റ് ബ്ലോഔട്ട്, നിരീക്ഷണത്തിന് എന്ത് ചെലവാകുന്നു

ഏതെങ്കിലും ഏജന്റ്-താരതമ്യ ടൂളിനെ വിശ്വസിക്കുന്നതിന് മുമ്പ് ഉത്തരം നൽകേണ്ട രണ്ട് ചോദ്യങ്ങൾ.

**റൺടൈമുകളിലുടനീളം കോൺടെക്സ്റ്റ്-വിൻഡോ ബ്ലോഔട്ട് ഇത് എങ്ങനെ കൈകാര്യം ചെയ്യുന്നു?**

ഒരു ഉപയോഗ ശതമാനം അത് ഏത് സംഖ്യ കൊണ്ട് ഹരിക്കുന്നു എന്നതു പോലെ മാത്രമേ സത്യസന്ധമായിരിക്കൂ. Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM എന്നിവ ഉൾക്കൊള്ളുന്ന, നിങ്ങൾക്ക് വായിക്കാനും PR ചെയ്യാനും കഴിയുന്ന [ഒരു ടേബിളിൽ](clawmetry/context_windows.py) നിന്ന് ClawMetry ഓരോ പ്രൊവൈഡറിനും അനുസരിച്ച് വിൻഡോയുടെ വലുപ്പം നിശ്ചയിക്കുന്നു. ഇത് ഒരു വെണ്ടറുടെ അളവുകോൽ ഉപയോഗിച്ച് 31 റൺടൈമുകളും അളക്കുന്നില്ല. അത് പ്രധാനമാണ്: Anthropic-ന്റെ 200K-ക്കെതിരെ സ്കോർ ചെയ്യുന്ന ഒരു 300K GPT-5 ടേൺ ">100%, ബ്ലോൺ" എന്ന് വായിക്കപ്പെടും, യഥാർത്ഥത്തിൽ അത് GPT-5-ന്റെ 400K-ന്റെ 75% ആണെങ്കിലും. അതേ അളവുകോൽ യഥാർത്ഥത്തിൽ ഓവർഫ്ലോ ആയ 130K DeepSeek ടേണിനെ സൗകര്യപ്രദമായ 65% ആയി മറയ്ക്കുന്നു.

ഓരോ വിൻഡോയും അതിന്റെ പ്രോവനൻസോടെയാണ് ഷിപ്പ് ചെയ്യുന്നത്: `model_table`, `explicit_marker`, `observed_floor`, അല്ലെങ്കിൽ മോഡൽ ഏതെന്ന് അറിയാത്തപ്പോൾ ഒരു സത്യസന്ധമായ `default`. ഒരു ഊഹത്തിന്മേൽ നിർമ്മിച്ച ഗേജ്, ഒരു ലുക്കപ്പിന്മേൽ നിർമ്മിച്ചതിന് തുല്യമായ അധികാരത്തോടെ ഒരിക്കലും റെൻഡർ ചെയ്യില്ല.

ചില റൺടൈമുകളിൽ മാത്രമേ ClawMetry-ക്ക് compaction ഇവന്റുകൾ കാണാൻ കഴിയൂ. അതിനാൽ `GET /api/context-coverage` ഓരോ റൺടൈമിനും, ഒരു സീറോ എന്നാൽ **"ക്ലീൻ ആയി റൺ ചെയ്തു" എന്നാണോ അതോ "ഞങ്ങൾക്ക് കാഴ്ചയില്ല" എന്നാണോ** എന്ന് റിപ്പോർട്ട് ചെയ്യുന്നു. യഥാർത്ഥത്തിൽ blind എന്നർത്ഥമുള്ള ഒരു `0` അത് പറയുന്നു.
[പൂർണ്ണ വിശദാംശം](docs/CONTEXT_BLOWOUT.md)

**instrumentation-ന് എന്ത് ചെലവാകുന്നു?**

| പാത | നിങ്ങളുടെ ഏജന്റിലേക്ക് ചേർക്കപ്പെടുന്നത് | ഡിഫോൾട്ട്? |
|---|---|---|
| സെഷൻ-ഫയൽ ടെയിലിംഗ് (എല്ലാ 31 റൺടൈമുകളും) | **0**. പ്രത്യേക പ്രോസസ്സ്, നിങ്ങളുടെ ഏജന്റിൽ ClawMetry കോഡ് ഇല്ല | ഓൺ |
| HTTP ഇന്റർസെപ്റ്റർ (`CLAWMETRY_INTERCEPT=1`) | ഓരോ LLM കോളിനും **+0.44 ms**, അല്ലെങ്കിൽ ഒരു 5s കോളിന്റെ 0.009% | ഓഫ് |
| Pre-tool ഹുക്ക് ഗേറ്റ് (warm cache) | 36 ms ഇന്റർപ്രെട്ടർ ഫ്ലോറിന് മുകളിൽ, ഗേറ്റ് ചെയ്യപ്പെട്ട ഓരോ ടൂൾ കോളിനും **+44 ms** | ഓഫ് |
| Enforcement proxy | ഓരോ LLM കോളിനും **+9.7 ms** | ഓഫ് |

ഡെമൺ ഹോസ്റ്റ് ചെലവ്: ingest-ന് **2,762 events/sec**, ഡിസ്കിൽ **710 bytes/event** (100k ഇവന്റുകൾക്ക് 67.7 MB), കൂടാതെ തിരക്കുള്ള ഒരു ഇൻസ്റ്റാളിൽ **ഒരു കോറിന്റെ ~12%** സുസ്ഥിരമായി. ആ അവസാന സംഖ്യ ഞങ്ങളുടെ സ്വന്തം പ്രസ്താവിച്ച 5-10% ബജറ്റിന് മുകളിലാണ്, അതിനാൽ പേജിൽ നിന്ന് ഒഴിവാക്കുന്നതിന് പകരം പിന്തുടരേണ്ട ഒരു ബഗ് ആയി ഇത് പ്രസിദ്ധീകരിക്കുന്നു.

ഒരു Apple M2 Pro-യിൽ `benchmarks/overhead.py` ഉപയോഗിച്ച് അളന്നത്. ഹാർനെസ് ഓരോ കണ്ടീഷനും ഒരു പ്രത്യേക പ്രോസസ്സിൽ പ്രവർത്തിപ്പിക്കുന്നു, അവയുടെ ക്രമം മാറ്റിക്കൊണ്ടിരിക്കുന്നു, കൂടാതെ **റൗണ്ടുകൾ അതിന്റെ ചിഹ്നത്തിൽ വിയോജിക്കുമ്പോൾ ഒരു സംഖ്യ പ്രിന്റ് ചെയ്യാൻ വിസമ്മതിക്കുന്നു**. ഒരു മിനിറ്റിനുള്ളിൽ നിങ്ങളുടെ സ്വന്തം മെഷീനിൽ ഇത് പ്രവർത്തിപ്പിക്കുക:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ഹുക്ക് ഗേറ്റുകളും enforcement proxy-യും ഉൾപ്പെടെ എല്ലാ പാതയും അളക്കപ്പെടുന്നു, കൂടാതെ CI-യിൽ ഹാർനെസ് Linux, macOS, Windows എന്നിവയിൽ പ്രവർത്തിക്കുന്നു. അറിഞ്ഞിരിക്കേണ്ട രണ്ട് ഫലങ്ങൾ: Linux-നെ അപേക്ഷിച്ച് Windows-ൽ proxy ഏകദേശം ഏഴിരട്ടി കൂടുതൽ ചെലവാകുന്നു, കൂടാതെ ഡെമൺ നിലവിൽ ഏകദേശം ഒരു കോറിന്റെ 12% സുസ്ഥിരമായി നിലനിർത്തുന്നു, ഞങ്ങളുടെ സ്വന്തം 5-10% ബജറ്റിന് മുകളിൽ. റോ JSON, രീതി, ഇനിയും അളക്കാത്തത് എന്നിവ [docs/OVERHEAD.md](docs/OVERHEAD.md) ൽ ഉണ്ട്.

## വിലനിർണ്ണയം

| പ്ലാൻ | ഇത് എന്ത് ഉൾക്കൊള്ളുന്നു | വില |
|---|---|---|
| **സൗജന്യം** | OpenClaw + NVIDIA NemoClaw + Goose, പൂർണ്ണ ഡാഷ്ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **സ്റ്റാർട്ടർ** | മുകളിൽ പറഞ്ഞ മറ്റെല്ലാ റൺടൈമുകളും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | നോഡിന് $9 / മാസം |
| **Pro** | സ്റ്റാർട്ടർ + കൺട്രോളും ഇവാലുവേഷനും: അപ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, evals, ആനോമലി ഡിറ്റക്ഷൻ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel export, tamper-evident audit log | നോഡിന് $19 / മാസം |

വാർഷിക പ്ലാനുകൾ, Enterprise, നിലവിലെ സംഖ്യകൾ എന്നിവ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ഉണ്ട്. Self-hosted ലൈസൻസ്
കീകൾ ക്ലൗഡ് ഇല്ലാതെ പ്രവർത്തിക്കുന്നു (`clawmetry license`). കൃത്യമായ സൗജന്യ/പണമടച്ച വിഭജനം
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ ഉണ്ട്.

## നിങ്ങളുടെ ഡാറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ നിലനിൽക്കുന്നു

ClawMetry ലോക്കൽ സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. **നിങ്ങൾ `clawmetry connect` പ്രവർത്തിപ്പിക്കുന്നില്ലെങ്കിൽ നിങ്ങളുടെ ബോക്സിൽ നിന്ന് സെഷൻ ഡാറ്റ ഒന്നും പുറത്തുപോകുന്നില്ല** — പ്രോംപ്റ്റുകൾ, റിപ്ലൈകൾ, ടൂൾ ആർഗ്യുമെന്റുകൾ, ഫയൽ ഉള്ളടക്കങ്ങൾ, ലോഗ് ലൈനുകൾ ഒന്നും ഇല്ല. നിങ്ങൾ കണക്റ്റ് ചെയ്യുമ്പോൾ, ഒരിക്കലും നിങ്ങളുടെ മെഷീൻ വിട്ടുപോകാത്ത ഒരു കീ ഉപയോഗിച്ച് സ്നാപ്ഷോട്ട് end-to-end എൻക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു, കൂടാതെ നിങ്ങളുടെ ബ്രൗസറിൽ ഡീക്രിപ്റ്റ് ചെയ്യപ്പെടുന്നു. ഒരു നോഡിന് കീ ഇല്ലെങ്കിൽ, അപ്‌ലോഡ് ക്ലിയർ ടെക്സ്റ്റിൽ അയക്കുന്നതിന് പകരം ഒഴിവാക്കപ്പെടുന്നു, ഒരു സെർവർ റെസ്പോൺസിനും അത് ഓഫ് ചെയ്യാൻ കഴിയില്ല.

നിങ്ങൾ കണക്റ്റ് ചെയ്യുന്നതിന് മുമ്പ് ഡിഫോൾട്ടായി രണ്ട് കാര്യങ്ങൾ പ്രവർത്തിക്കുന്നു, രണ്ടും opt-out ചെയ്യാവുന്നവയാണ്, രണ്ടും സെഷൻ ഡാറ്റ വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI-ക്കെതിരെ ഒരു വേർഷൻ ചെക്കും. ഒരു ഡിഫോൾട്ട് ഇൻസ്റ്റാൾ ഒരു സ്റ്റാർട്ടപ്പ് ബാനർ ലൈനിനായി നിങ്ങളുടെ പബ്ലിക് IP ഒരു തവണ ലുക്ക് അപ്പ് ചെയ്യുന്നു. ഓരോ ഡെസ്റ്റിനേഷനും, അത് എന്ത് വഹിക്കുന്നു, അത് എങ്ങനെ ഓഫ് ചെയ്യാം എന്നത്
[docs/EGRESS.md](docs/EGRESS.md) ൽ ലിസ്റ്റ് ചെയ്തിരിക്കുന്നു; self-hosted, repointed, air-gapped ഇൻസ്റ്റാളുകൾ യാതൊരു discretionary ഔട്ട്ബൗണ്ട് കോളുകളും നടത്തുന്നില്ല.

ഡീക്രിപ്ഷൻ നടക്കുന്നത് നിങ്ങളുടെ ബ്രൗസറിൽ, ഞങ്ങൾ നിങ്ങൾക്ക് നൽകുന്ന കോഡിലാണ്. അത് മുമ്പ് ഒരു വാഗ്ദാനമായിരുന്നു; ഇപ്പോൾ അത് നിങ്ങൾക്ക് പരിശോധിക്കാവുന്ന ഒന്നാണ്. നിങ്ങളുടെ കീയെ സ്പർശിക്കുന്ന ഓരോ ലൈനും ഒരൊറ്റ വായിക്കാവുന്ന ഫയലിലാണ് ജീവിക്കുന്നത്, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ഇത് wheel-ന്റെ ഉള്ളിൽ ഷിപ്പ് ചെയ്യുകയും verbatim ആയി സെർവ് ചെയ്യപ്പെടുകയും ഒരു Subresource Integrity ഹാഷ് ഉപയോഗിച്ച് പിൻ ചെയ്യപ്പെടുകയും ചെയ്യുന്നു. ബ്രൗസർ ഞങ്ങൾ പ്രസിദ്ധീകരിച്ചത് തന്നെ പ്രവർത്തിപ്പിക്കുന്നു എന്ന് സ്ഥിരീകരിക്കാൻ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

അത് തെളിയിക്കാത്തത്: ഫയൽ ലോഡ് ചെയ്യുന്ന പേജ് ഞങ്ങൾ സെർവ് ചെയ്യുന്നു, അതിനാൽ ഞങ്ങൾക്ക് വ്യത്യസ്തമായ ഒരു പേജ് സെർവ് ചെയ്യാൻ കഴിയും. Integrity ഹാഷുകൾ നിങ്ങളെ ഒരു compromised CDN-ൽ നിന്ന് സംരക്ഷിക്കുന്നു, വെണ്ടറിൽ നിന്നല്ല. നിങ്ങൾക്ക് ലഭിക്കുന്നത് ഏതെങ്കിലും substitution ബോധപൂർവ്വമായതും, പേജ് സോഴ്‌സിൽ ദൃശ്യമായതും, ആർക്കും ഫെച്ച് ചെയ്യാവുന്ന PyPI-യിലെ ഒരു artifact-ൽ നിന്ന് വ്യത്യസ്തവുമായിരിക്കണം എന്നതാണ്. Self-hosting അല്ലെങ്കിൽ ലോക്കൽ-മാത്രം ആയി തുടരുന്നത് ഈ ആശ്രിതത്വത്തെ പൂർണ്ണമായും നീക്കം ചെയ്യുന്നു.

## ഇൻസ്റ്റാൾ

```bash
pip install clawmetry     # പിന്നെ: clawmetry
```

അല്ലെങ്കിൽ ഒറ്റ-ലൈൻ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux അല്ലെങ്കിൽ Windows-ൽ Python 3.8+ ആവശ്യമാണ്, കൂടാതെ അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമെങ്കിലും വേണം. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

അല്ലെങ്കിൽ ഏജന്റിനെ തന്നെ അത് നിങ്ങൾക്കായി സെറ്റപ്പ് ചെയ്യാൻ അനുവദിക്കുക. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
സ്കിൽ Claude Code, Codex, Cursor, Gemini CLI, Copilot അല്ലെങ്കിൽ OpenCode-നെ ClawMetry ഇൻസ്റ്റാൾ ചെയ്യാനും, മെഷീനിലെ ഏജന്റുകൾ എന്ത് ചെയ്യുന്നു, എന്ത് ചെലവാക്കുന്നു എന്ന് റിപ്പോർട്ട് ചെയ്യാനും, അഭ്യർത്ഥനയിൽ ഒരു സെഷൻ നിർത്താനും, അപ്രൂവലിനായി അപകടകരമായ ടൂൾ കോളുകൾ പിടിച്ചുവയ്ക്കാനും പഠിപ്പിക്കുന്നു:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ഡോക്സ്

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും എന്ത് വായിക്കുന്നു, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Per-provider വിൻഡോകൾ, compaction vs overflow, per-runtime coverage |
| [Overhead](docs/OVERHEAD.md) | instrumentation-ന് എന്ത് ചെലവാകുന്നു, അളന്നത്, പുനർനിർമ്മിക്കാനുള്ള ഹാർനെസ് സഹിതം |
| [Entitlements](docs/ENTITLEMENTS.md) | സൗജന്യം vs പണമടച്ചത്, ടയർ മാട്രിക്സ്, ലൈസൻസ് CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ട്രെയ്സുകൾ എവിടെയും export ചെയ്യുക, എവിടെ നിന്നും OTLP ingest ചെയ്യുക |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, പ്രവർത്തിപ്പിക്കാവുന്ന ഉദാഹരണങ്ങളോടെ |
| [SDK tracking](docs/SDK_TRACKING.md) | നിങ്ങൾ സ്വയം നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് ആട്രിബ്യൂഷൻ |
| [Chat channels](docs/CHANNELS.md) | ഫ്ലോയിൽ കാണിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ഇത് ഉള്ളിൽ എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്‌സിൽ നിന്ന് പ്രവർത്തിപ്പിക്കൽ |
| [Telemetry](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

താഴെയുള്ള ഓരോ സംഖ്യയും ഒരു യഥാർത്ഥ മെഷീനിൽ നിന്നുള്ളതാണ്, read-only ആയി, ഒന്നും seed ചെയ്യാതെ.

**എന്തോ തെറ്റാണെന്ന് ഇത് നിങ്ങളോട് പറയുന്നു, എന്ത് സംഭവിച്ചു എന്ന് മാത്രമല്ല.**
മുകളിൽ രണ്ട് ആനോമലി ബാനറുകൾ: ദിവസേനയുള്ള ശരാശരിയുടെ 7 ഇരട്ടി ചെലവ്, ഒരു
4.2x കോസ്റ്റ് സ്പൈക്ക്. അവയ്ക്ക് താഴെ, അടുത്തിടെയുള്ള 667 സെഷനുകളിൽ 324 എണ്ണം ഒരു waste
സിഗ്നൽ വഹിക്കുന്നു, കാരണം അനുസരിച്ച് ഇനംതിരിച്ചത്.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**പണം എവിടെ പോയി എന്ന് ഇത് നിങ്ങൾക്ക് കാണിക്കുന്നു, എല്ലാ വിൻഡോയിലും.**
ഇന്ന് $252.47, ഈ ആഴ്ച $513.15, ഈ മാസം $1,312.92, ഓരോന്നിനും പിന്നിലുള്ള ടോക്കണുകളും
നിങ്ങളുടെ സബ്സ്ക്രിപ്ഷൻ ഇതിനകം എത്രത്തോളം ഉൾക്കൊള്ളുന്നു എന്നതും സഹിതം. അതിനു താഴെ,
recoverable ആയി ഏകദേശം $1,128/മാസം ഇനംതിരിച്ചത്, കൂടാതെ cache reuse വഴി ഇതിനകം
$17,256/മാസം ലാഭിച്ചത്.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ഒരു സന്ദേശം എങ്ങനെ ഒരു ഉത്തരമായി മാറുന്നു എന്ന് ഇത് വരയ്ക്കുന്നു.**
ലൈവ് ഫ്ലോ ഡയഗ്രം: നിങ്ങൾ, അത് വന്ന ചാനൽ, ഗേറ്റ്‌വേ, ഇപ്പോൾ ഉത്തരം നൽകുന്ന
മോഡൽ, കൂടാതെ അത് ഉപയോഗിച്ച ഓരോ ടൂളും. ജോലി അവയിലൂടെ നീങ്ങുമ്പോൾ നോഡുകൾ പ്രകാശിക്കുന്നു.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**മെഷീനിലെ ഓരോ ഏജന്റും, ഒരൊറ്റ ടേബിളിൽ.**
അത് എന്ത് പ്രവർത്തിപ്പിക്കുന്നു, കഴിഞ്ഞ 24 മണിക്കൂറിലും അതിന്റെ ജീവിതകാലത്തും അതിന് എന്ത് ചെലവാകുന്നു, അത്
അവസാനമായി എപ്പോൾ കണ്ടു, ആരാണ് ഉടമ, ഒരു സബ്സ്ക്രിപ്ഷൻ ബില്ല് കവർ ചെയ്യുന്നുണ്ടോ. ഇവിടെ 14 ഏജന്റുകൾ, 3
സെഷനുകൾ ജോലി ചെയ്യുന്നു, 13 നിശ്ശബ്ദം.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ഒരു ടേണിന്റെ സമയവും പണവും എവിടെ പോയി എന്ന് ഇത് ടൂൾ ബൈ ടൂൾ കാണിക്കുന്നു.**
ഒരു യഥാർത്ഥ സെഷന്റെ ഒരു ടേൺ: $1.16-ന് 11.2 മിനിറ്റിൽ 11 ടൂളുകൾ. ഓരോ Bash
കോളിനും മോഡൽ കോളിനും ടൈംലൈനിൽ അതിന്റേതായ ബാർ ലഭിക്കുന്നു, അതിനാൽ 4.1 മിനിറ്റ്
പ്രവർത്തിച്ച കമാൻഡും 226ms പ്രവർത്തിച്ചതും ഒറ്റനോട്ടത്തിൽ വേർതിരിച്ചറിയാം.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ഇത് ജോലിയെ ഗ്രേഡ് ചെയ്യുന്നു, ചെലവ് മാത്രമല്ല.**
ഈ ആഴ്ച ഒരു A: 54 ടാസ്‌ക്കുകൾ ക്ലീനായി തിരികെ വന്നു, 2 പരുക്കൻ ജോലികൾക്ക് $48.57
ചെലവായി, കൂടാതെ വിലയിരുത്താൻ പര്യാപ്തമായ പ്രവർത്തനം ഇല്ലാത്ത റണ്ണുകൾ, വിജയങ്ങളായി
കണക്കാക്കപ്പെടുന്നതിന് പകരം ഗ്രേഡിൽ നിന്ന് ഒഴിവാക്കപ്പെടുന്നു. ഓരോ പരുക്കൻ റണ്ണും അതിന്റെ ട്രെയ്സിലേക്ക് ലിങ്ക് ചെയ്യുന്നു.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**കോൺടെക്സ്റ്റ് വിൻഡോ എന്തുകൊണ്ട് നിറഞ്ഞുകൊണ്ടിരിക്കുന്നു എന്ന് ഇത് കാണിക്കുന്നു.**
ഏറ്റവും പുതിയ ടേണിൽ 1M-ടോക്കൺ വിൻഡോയിൽ 715K, 83.3% പീക്ക്, overflow-ൽ അല്ല,
proactively ആയി ട്രിഗർ ചെയ്ത 4 compactions, കൂടാതെ അതിനു പിന്നിലുള്ള ഓരോ ടേണിന്റെയും ഉപയോഗം.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**നിങ്ങൾ ഒന്നും കോൺഫിഗർ ചെയ്യാതെ തന്നെ ഡിറ്റക്ഷൻ പ്രവർത്തിക്കുന്നു.**
ബിൽറ്റ്-ഇൻ ഡിറ്റക്ടറുകൾ ഇൻസ്റ്റാൾ ചെയ്തതു മുതൽ ഓണാണ്: ഏജന്റ് നിശ്ശബ്ദമായി, telemetry ഫീഡ്
നിലച്ചു, കോസ്റ്റ് സ്പൈക്ക്, ടോക്കൺ ബർസ്റ്റ്, എററുകൾ ഉയരുന്നു, എറർ സ്പൈക്ക്, ബജറ്റ്
ത്രെഷോൾഡ്, ത്രെട്ട് സിഗ്നേച്ചർ പൊരുത്തപ്പെട്ടു, സെക്യൂരിറ്റി ടൂൾ കണ്ടെത്തൽ, സെക്യൂരിറ്റി പൊസ്ചർ
മാറി. നിങ്ങളുടെ സ്വന്തം നിയമങ്ങൾ ഇവയ്‌ക്ക് മുകളിൽ ഓപ്ഷണൽ ആണ്.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**അപകടകരമായ ഒരു കോൾ പിടിച്ചുവയ്ക്കുന്നത് opt-in ആണ്, കൂടാതെ ഓഫ് ആയാണ് ഷിപ്പ് ചെയ്യുന്നത്.**
Recursive deletes, force pushes, sudo, secrets, package installs, ഔട്ട്ബൗണ്ട്
കോളുകൾ എന്നിവ ഓരോന്നിനും നിങ്ങൾക്ക് ഓണാക്കാവുന്ന ഒരു നിയമം ലഭിക്കുന്നു. നിങ്ങൾ അത് ചെയ്യുന്നതുവരെ, ClawMetry നിരീക്ഷിക്കുന്നു,
ഒന്നും മാറ്റുന്നില്ല. ഒരെണ്ണം ഓണായാൽ, പൊരുത്തപ്പെടുന്ന കോളുകൾ ഇവിടെ (അല്ലെങ്കിൽ നിങ്ങളുടെ ഫോണിൽ)
ഒരു അപ്രൂവിനോ ഡിനൈക്കോ വേണ്ടി കാത്തിരിക്കുന്നു.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

കൂടുതൽ, ഓരോ റൺടൈമിനും: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## അംഗീകാരം

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
