<!-- i18n-src:c99ac0512cae -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ഒരു ഏജന്റിന് പുരോഗതി ഒന്നും ഉണ്ടാക്കാതെ നൂറ് ടൂൾ കോളുകൾ നടത്താൻ കഴിയും.** ClawMetry നിങ്ങളുടെ കോഡിംഗ് ഏജന്റുകൾ ഇതിനകം എഴുതുന്ന സെഷൻ ഫയലുകൾ വായിച്ച്, ടൈംലൈൻ, ടൂൾ കോളുകൾ, റൺടൈം തുറന്നുകാണിക്കുന്ന ടോക്കൺ, കോസ്റ്റ് ഡേറ്റ എന്നിവ ഒരൊറ്റ വ്യൂവിൽ കൊണ്ടുവരുന്നു — അതിനാൽ പ്രവർത്തിക്കുന്ന ഒരു ദൈർഘ്യമുള്ള റണ്ണിനെയും കുടുങ്ങിയ ഒന്നിനെയും വേർതിരിച്ചറിയാൻ നിങ്ങൾക്ക് സാധിക്കും.

**33 AI ഏജന്റ് റൺടൈമുകളുമായി** പ്രവർത്തിക്കുന്നു — Claude Code, OpenAI Codex, Hermes, OpenClaw, കൂടാതെ 29 എണ്ണം കൂടി. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരു ഡാഷ്ബോർഡ്. ([പൂർണ്ണ ലിസ്റ്റ്](SUPPORTED_RUNTIMES.txt), കാറ്റലോഗിൽ നിന്ന് ജനറേറ്റ് ചെയ്തത്.)

> 🌐 **ഇത് ഇതിൽ വായിക്കുക:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ഒരു കമാൻഡ്. സീറോ കോൺഫിഗ്. എല്ലാം ഓട്ടോ-ഡിറ്റക്റ്റ് ചെയ്യുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു. സീറോ കോൺഫിഗ്: നിങ്ങളുടെ പക്കൽ ഇതിനകം ഉള്ള ഏജന്റ് റൺടൈമുകൾ അത് കണ്ടെത്തുന്നു, അവയെ റീഡ്-ഒൺലി ആയി വായിക്കുന്നു, അവ എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്നതിൽ ഒന്നും മാറ്റുന്നില്ല.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ഇൻസ്റ്റാൾ ചെയ്യുന്നതിന് മുൻപ്

| | |
|---|---|
| **ഇത് എന്ത് ചെയ്യുന്നു** | നിങ്ങളുടെ ഏജന്റുകൾ ഇതിനകം എഴുതുന്ന സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. SDK ഇല്ല, കോഡ് മാറ്റം ഇല്ല, നിങ്ങളുടെ ആപ്പിൽ ഇൻസ്ട്രുമെന്റേഷൻ ഇല്ല. |
| **നിങ്ങൾ കാണുന്നത്** | സെഷൻ ടൈംലൈൻ, ടൂൾ-ബൈ-ടൂൾ റീപ്ലേ, ടോക്കൺ, കോസ്റ്റ് ബ്രേക്ക്ഡൗൺ, ട്രജക്ടറി സിഗ്നലുകൾ (ലൂപ്പിംഗ്, ആവർത്തിച്ചുള്ള പരാജയങ്ങൾ) — ഓരോ റൺടൈമിനും. |
| **എന്താണ് ഫ്രീ** | `pip install clawmetry` എന്നത് **OpenClaw, NVIDIA NemoClaw, Goose, Qwen Code** എന്നിവ അക്കൗണ്ടോ കീയോ നെറ്റ്‌വർക്ക് കോളോ ഇല്ലാതെ വായിക്കുന്നു. മറ്റ് 28 എണ്ണം — Claude Code, Codex, Cursor തുടങ്ങിയവ — ക്ലോസ്ഡ്-സോഴ്സ് `clawmetry-pro` കമ്പാനിയൻ ആണ് വായിക്കുന്നത്, ഇത് 7 ദിവസത്തെ ട്രയലോ ഒരു പ്ലാനോ കൊണ്ട് ലഭിക്കും — കൃത്യമായ വിഭജനത്തിന് [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) കാണുക. |
| **എങ്ങനെ തുടങ്ങാം** | `pip install clawmetry && clawmetry`, പിന്നീട് localhost:8900 തുറക്കുക. ഈ മെഷീനിൽ ഇതുവരെ ഏജന്റുകൾ ഇല്ലേ? `clawmetry --sample` മൂന്ന് ലേബൽ ചെയ്ത സിന്തറ്റിക് സെഷനുകളിൽ തുറക്കുന്നു. |
| **നിങ്ങളുടെ മെഷീനിൽ നിന്ന് എന്ത് പോകുന്നു** | `clawmetry connect` റൺ ചെയ്തില്ലെങ്കിൽ സെഷൻ ഡേറ്റ ഒന്നും പോകുന്നില്ല. ഡിഫോൾട്ടായി രണ്ട് കാര്യങ്ങൾ റൺ ആകുന്നു, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ആണ്, രണ്ടും സെഷൻ ഉള്ളടക്കം വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI വേർഷൻ ചെക്കും. ഓരോ ലക്ഷ്യസ്ഥാനവും [docs/EGRESS.md](docs/EGRESS.md) ൽ ഇൻവെന്ററി ചെയ്തിരിക്കുന്നു, കമന്റുകൾ വായിക്കുന്നതിന് പകരം ഒരു വയർ ക്യാപ്‌ചറിൽ നിന്ന് വീണ്ടും നിർമ്മിച്ചത്. |

നിങ്ങൾ ഔട്ട്‌പുട്ട് വിധിക്കുന്നതിന് മുൻപ് അറിഞ്ഞിരിക്കേണ്ട രണ്ട് പരിധികൾ: റൺടൈമുകൾ വളരെ വ്യത്യസ്തമായ ഡേറ്റ തുറന്നുകാണിക്കുന്നു (ചിലത് ഒരു കോസ്റ്റ് പോലും പ്രസിദ്ധീകരിക്കുന്നില്ല — [the matrix](docs/compatibility.md) ഓരോ റൺടൈമിനും ഏതാണെന്ന് പറയുന്നു), കൂടാതെ ഒരു ആക്ഷൻ നിരീക്ഷിക്കുന്നത് അത് തടയാൻ കഴിയുന്നതിന് തുല്യമല്ല ([ഏത് കൺട്രോളുകൾ യഥാർത്ഥമാണ്, ഓരോ റൺടൈമിനും](docs/APPROVALS.md)).


## 33 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

**ഓപ്പൺ സോഴ്സ് ആപ്പിൽ ഫ്രീ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**ഒരു പെയ്ഡ് പ്ലാനിൽ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

എല്ലാ റൺടൈമിനും ഒരേ ഡാഷ്ബോർഡ് ലഭിക്കുന്നു. ഒന്നിലധികം ഒരേ സമയം റൺ ചെയ്യുക, ഹെഡർ സ്വിച്ചർ എല്ലാ ടാബുകളെയും അവയിൽ ഒന്നിലേക്ക് റീ-സ്കോപ്പ് ചെയ്യുന്നു.

ഒരു SDK ഉപയോഗിച്ച് നിങ്ങളുടെ സ്വന്തം ഏജന്റ് ഉണ്ടാക്കിയോ? ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകളും ട്രാക്ക് ചെയ്യുന്നു. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **സെഷനുകളും ട്രാൻസ്ക്രിപ്റ്റുകളും**: ഓരോ ഏജന്റും ചെയ്തത്, ടേൺ ബൈ ടേൺ, റീപ്ലേ സഹിതം
- **കോസ്റ്റും ടോക്കണുകളും**: ഓരോ റൺടൈം, മോഡൽ, സെഷൻ, ദിവസം എന്നിവ പ്രകാരം, അനോമലി ഫ്ലാഗുകളോടെ
- **ഫ്ലോ**: ചാനലുകൾ, മോഡലുകൾ, ടൂളുകൾ എന്നിവയിലൂടെ നീങ്ങുന്ന മെസേജുകളുടെ ലൈവ് ഡയഗ്രം
- **ബ്രെയിൻ**: സംഭവിക്കുന്ന സമയത്ത് റീസണിംഗ്, ടൂൾ-കോൾ ഇവന്റ് സ്ട്രീം
- **കോണ്ടെക്സ്റ്റ് ബ്ലോഔട്ട്**: ഓരോ പ്രൊവൈഡറിനും അനുയോജ്യമായ വിൻഡോ യൂട്ടിലൈസേഷൻ, കോംപാക്ഷൻ vs ഫോഴ്സ്ഡ് ഓവർഫ്ലോ, കൂടാതെ നമുക്ക് *കാണാൻ കഴിയാത്തത്* എന്താണെന്നതിന്റെ ഓരോ റൺടൈമിനുമുള്ള മാപ്പ് ([how](docs/CONTEXT_BLOWOUT.md))
- **മെമ്മറിയും സ്കില്ലുകളും**: ഓരോ റൺടൈമും യഥാർത്ഥത്തിൽ ലോഡ് ചെയ്ത ഫയലുകളും സ്കില്ലുകളും
- **ഹെൽത്തും ലോഗുകളും**: ഡിസ്ക്, മെമ്മറി, എറർ റേറ്റുകൾ, റേറ്റ് ലിമിറ്റുകൾ, ലൈവ് ലോഗ് സ്ട്രീം
- **അലേർട്ടുകൾ**: ബഡ്ജറ്റ് കാപ്പുകൾ, എറർ സ്പൈക്കുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ, Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്തവ
- **അപ്പ്രൂവലുകൾ**: റിസ്കുള്ള ടൂൾ കോളുകൾ *റൺ ചെയ്യുന്നതിന് മുൻപ്* പോസ് ചെയ്ത് നിങ്ങളുടെ ഫോണിൽ നിന്ന് അപ്പ്രൂവ് ചെയ്യുക ([how](docs/APPROVALS.md))

## കോണ്ടെക്സ്റ്റ് ബ്ലോഔട്ടും, നിരീക്ഷണത്തിന്റെ ചെലവും

ഏതൊരു ഏജന്റ്-കംപാരിസൺ ടൂളിനെയും വിശ്വസിക്കുന്നതിന് മുൻപ് ഉത്തരം ലഭിക്കേണ്ട രണ്ട് ചോദ്യങ്ങൾ.

**റൺടൈമുകളിലുടനീളം കോണ്ടെക്സ്റ്റ്-വിൻഡോ ബ്ലോഔട്ട് എങ്ങനെ കൈകാര്യം ചെയ്യുന്നു?**

ഒരു യൂട്ടിലൈസേഷൻ ശതമാനം അത് ഏതിനെ ഹരിക്കുന്നു എന്നതിന്റെ സത്യസന്ധത പോലെ മാത്രമേ സത്യസന്ധമാകൂ. ClawMetry [നിങ്ങൾക്ക് വായിക്കാനും PR ചെയ്യാനും കഴിയുന്ന ഒരു ടേബിളിൽ](clawmetry/context_windows.py) നിന്ന് ഓരോ പ്രൊവൈഡറിനുമുള്ള വിൻഡോ സൈസ് ചെയ്യുന്നു, Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, GLM എന്നിവ ഉൾപ്പെടെ. ഒരു വെണ്ടറുടെ അളവുകോൽ ഉപയോഗിച്ച് 33 റൺടൈമുകളും അളക്കുന്നില്ല. അത് പ്രധാനമാണ്: Anthropic ന്റെ 200K നെതിരെ സ്കോർ ചെയ്യുന്ന ഒരു 300K GPT-5 ടേൺ ">100%, ബ്ലോൺ" എന്ന് വായിക്കുന്നു, അത് യഥാർത്ഥത്തിൽ GPT-5 ന്റെ 400K ൽ 75% ആയിരിക്കെ. അതേ അളവുകോൽ ഒരു യഥാർത്ഥത്തിൽ ഓവർഫ്ലോ ആയ 130K DeepSeek ടേണിനെ സൗകര്യപ്രദമായ 65% ആയി മറയ്ക്കുന്നു.

ഓരോ വിൻഡോയും അതിന്റെ പ്രോവനൻസ് സഹിതം ഷിപ്പ് ചെയ്യുന്നു: `model_table`, `explicit_marker`, `observed_floor`, അല്ലെങ്കിൽ നമുക്ക് മോഡൽ അറിയാത്തപ്പോൾ ഒരു സത്യസന്ധമായ `default`. ഒരു ഊഹത്തിൽ നിർമ്മിച്ച ഗേജ് ഒരു ലുക്കപ്പിൽ നിർമ്മിച്ച ഒന്നിന്റെ അതേ അധികാരത്തോടെ ഒരിക്കലും റെൻഡർ ചെയ്യുന്നില്ല.

ClawMetry ക്ക് ചില റൺടൈമുകളിൽ മാത്രമേ കോംപാക്ഷൻ ഇവന്റുകൾ കാണാൻ കഴിയൂ. അതിനാൽ `GET /api/context-coverage` ഓരോ റൺടൈമിനും, **സീറോ "ക്ലീൻ ആയി റൺ ചെയ്തു" എന്നാണോ "നമ്മൾ ബ്ലൈൻഡ് ആണ്" എന്നാണോ അർത്ഥമാക്കുന്നത്** എന്ന് റിപ്പോർട്ട് ചെയ്യുന്നു. യഥാർത്ഥത്തിൽ ബ്ലൈൻഡ് എന്നാണ് അർത്ഥമാക്കുന്ന ഒരു `0` അത് പറയുന്നു.
[Full detail](docs/CONTEXT_BLOWOUT.md)

**ഇൻസ്ട്രുമെന്റേഷന് എന്ത് ചെലവ് വരുന്നു?**

| പാത | നിങ്ങളുടെ ഏജന്റിലേക്ക് ചേർക്കുന്നത് | ഡിഫോൾട്ടോ? |
|---|---|---|
| സെഷൻ-ഫയൽ ടെയിലിംഗ് (33 റൺടൈമുകളും) | **0**. വേറിട്ട പ്രോസസ്, നിങ്ങളുടെ ഏജന്റിൽ ClawMetry കോഡ് ഇല്ല | ഓൺ |
| HTTP ഇന്റർസെപ്റ്റർ (`CLAWMETRY_INTERCEPT=1`) | ഒരു LLM കോളിന് **+0.44 ms**, അല്ലെങ്കിൽ 5സെക്കൻഡ് കോളിന്റെ 0.009% | ഓഫ് |
| പ്രീ-ടൂൾ ഹുക്ക് ഗേറ്റ് (വാം ക്യാഷ്) | 36 ms ഇന്റർപ്രെറ്റർ ഫ്ലോറിന് മുകളിൽ, ഒരു ഗേറ്റഡ് ടൂൾ കോളിന് **+44 ms** | ഓഫ് |
| എൻഫോഴ്സ്മെന്റ് പ്രോക്സി | ഒരു LLM കോളിന് **+9.7 ms** | ഓഫ് |

ഡീമൺ ഹോസ്റ്റ് ചെലവ്: **2,762 ഇവന്റുകൾ/സെക്കൻഡ്** ഇൻജസ്റ്റ്, ഡിസ്കിൽ **710 ബൈറ്റ്/ഇവന്റ്** (100k ഇവന്റുകൾക്ക് 67.7 MB), ഒരു തിരക്കുള്ള ഇൻസ്റ്റാളിൽ സസ്റ്റെയിൻഡ് ആയി **ഒരു കോറിന്റെ ~12%**. അവസാനത്തെ നമ്പർ നമ്മുടെ തന്നെ 5-10% ബഡ്ജറ്റിന് മുകളിലാണ്, അതിനാൽ അത് പേജിൽ നിന്ന് ഒഴിവാക്കുന്നതിന് പകരം പിന്തുടരേണ്ട ഒരു ബഗ് ആയി പ്രസിദ്ധീകരിക്കുന്നു.

ഒരു Apple M2 Pro യിൽ `benchmarks/overhead.py` ഉപയോഗിച്ച് അളന്നത്. ഹാർനെസ് ഓരോ കണ്ടീഷനും വേറിട്ട പ്രോസസിൽ റൺ ചെയ്യുന്നു, അവയുടെ ഓർഡർ ആൾട്ടർനേറ്റ് ചെയ്യുന്നു, **റൗണ്ടുകൾ അതിന്റെ ചിഹ്നത്തിൽ വിയോജിക്കുമ്പോൾ ഒരു നമ്പർ പ്രിന്റ് ചെയ്യാൻ വിസമ്മതിക്കുന്നു**. ഒരു മിനിറ്റിനുള്ളിൽ നിങ്ങളുടെ തന്നെ മെഷീനിൽ ഇത് റൺ ചെയ്യുക:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ഹുക്ക് ഗേറ്റുകളും എൻഫോഴ്സ്മെന്റ് പ്രോക്സിയും ഉൾപ്പെടെ എല്ലാ പാതയും അളന്നിരിക്കുന്നു, ഹാർനെസ് CI യിൽ Linux, macOS, Windows ൽ റൺ ചെയ്യുന്നു. അറിയേണ്ട രണ്ട് ഫലങ്ങൾ: Windows ൽ Linux നെ അപേക്ഷിച്ച് പ്രോക്സിക്ക് ഏഴ് ഇരട്ടി ചെലവ് വരുന്നു, നിലവിൽ ഡീമൺ ഒരു കോറിന്റെ ~12% സസ്റ്റെയിൻ ചെയ്യുന്നു, നമ്മുടെ തന്നെ 5-10% ബഡ്ജറ്റിന് മുകളിൽ. റോ JSON, രീതി, ഇപ്പോഴും അളക്കാത്തത് എന്നിവ [docs/OVERHEAD.md](docs/OVERHEAD.md) ൽ.

## പ്രൈസിംഗ്

| പ്ലാൻ | ഇത് കവർ ചെയ്യുന്നത് | വില |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, പൂർണ്ണ ഡാഷ്ബോർഡ്, ലോക്കൽ മാത്രം | $0 |
| **Starter** | മുകളിലുള്ള മറ്റെല്ലാ റൺടൈമും, ഫ്ലീറ്റ് വ്യൂ, ക്ലൗഡ് സിങ്ക് | $9 ഓരോ നോഡിനും / മാസം |
| **Pro** | Starter + കൺട്രോളും ഇവാലുവേഷനും: അപ്പ്രൂവലുകൾ, ടൂൾ-റിസ്ക് പോളിസികൾ, ഇവാലുകൾ, അനോമലി ഡിറ്റക്ഷൻ, കോസ്റ്റ് ഒപ്റ്റിമൈസർ, OTel എക്സ്പോർട്ട്, ടാംപർ-എവിഡന്റ് ഓഡിറ്റ് ലോഗ് | $19 ഓരോ നോഡിനും / മാസം |

വാർഷിക പ്ലാനുകൾ, Enterprise, നിലവിലെ നമ്പറുകൾ എന്നിവ **[clawmetry.com/pricing](https://clawmetry.com/pricing)** ൽ ഉണ്ട്. സെൽഫ്-ഹോസ്റ്റഡ് ലൈസൻസ് കീകൾ ക്ലൗഡ് ഇല്ലാതെ പ്രവർത്തിക്കുന്നു (`clawmetry license`). കൃത്യമായ ഫ്രീ/പെയ്ഡ് വിഭജനം [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ൽ.

## നിങ്ങളുടെ ഡേറ്റ നിങ്ങളുടെ മെഷീനിൽ തന്നെ നിൽക്കുന്നു

ClawMetry ലോക്കൽ സെഷൻ ഫയലുകളും ലോഗുകളും വായിക്കുന്നു. **നിങ്ങൾ `clawmetry connect` റൺ ചെയ്തില്ലെങ്കിൽ നിങ്ങളുടെ ബോക്സിൽ നിന്ന് സെഷൻ ഡേറ്റ ഒന്നും പോകുന്നില്ല** — പ്രോംപ്റ്റുകൾ, റിപ്ലൈകൾ, ടൂൾ ആർഗ്യുമെന്റുകൾ, ഫയൽ ഉള്ളടക്കം, ലോഗ് ലൈനുകൾ എന്നിവ ഒന്നും ഇല്ല. നിങ്ങൾ കണക്ട് ചെയ്യുമ്പോൾ, സ്നാപ്ഷോട്ട് ഒരിക്കലും നിങ്ങളുടെ മെഷീൻ വിടാത്ത ഒരു കീ ഉപയോഗിച്ച് എൻഡ്-ടു-എൻഡ് എൻക്രിപ്റ്റ് ചെയ്യുന്നു, നിങ്ങളുടെ ബ്രൗസറിൽ ഡിക്രിപ്റ്റ് ചെയ്യുന്നു. ഒരു നോഡിന് കീ ഇല്ലെങ്കിൽ, അപ്‌ലോഡ് അയയ്ക്കുന്നതിന് പകരം സ്കിപ്പ് ചെയ്യുന്നു, ഒരു സെർവർ റെസ്പോൺസിനും അത് ഓഫ് ചെയ്യാൻ കഴിയില്ല.

നിങ്ങൾ കണക്ട് ചെയ്യുന്നതിന് മുൻപ് ഡിഫോൾട്ടായി രണ്ട് കാര്യങ്ങൾ റൺ ആകുന്നു, രണ്ടും ഓപ്റ്റ്-ഔട്ട് ആണ്, രണ്ടും സെഷൻ ഡേറ്റ വഹിക്കുന്നില്ല: ഒരു അജ്ഞാത ഇൻസ്റ്റാൾ പിംഗും PyPI ക്കെതിരെയുള്ള ഒരു വേർഷൻ ചെക്കും. ഒരു ഡിഫോൾട്ട് ഇൻസ്റ്റാൾ ഒരു സ്റ്റാർട്ടപ്പ് ബാനർ ലൈനിനായി നിങ്ങളുടെ പബ്ലിക് IP ഒരു തവണ ലുക്ക്അപ്പ് ചെയ്യുന്നു. ഓരോ ലക്ഷ്യസ്ഥാനവും, അത് എന്ത് വഹിക്കുന്നു, അത് എങ്ങനെ ഓഫ് ചെയ്യാം എന്നിവ [docs/EGRESS.md](docs/EGRESS.md) ൽ ലിസ്റ്റ് ചെയ്തിരിക്കുന്നു; സെൽഫ്-ഹോസ്റ്റഡ്, റീപോയിന്റഡ്, എയർ-ഗ്യാപ്പ്ഡ് ഇൻസ്റ്റാളുകൾ ഒരു discretionary ഔട്ട്ബൗണ്ട് കോളും ചെയ്യുന്നില്ല.

ഡിക്രിപ്ഷൻ നിങ്ങളുടെ ബ്രൗസറിൽ, ഞങ്ങൾ നിങ്ങൾക്ക് സേവ് ചെയ്യുന്ന കോഡിൽ നടക്കുന്നു. അത് മുൻപ് ഒരു വാഗ്ദാനം ആയിരുന്നു; ഇപ്പോൾ അത് നിങ്ങൾക്ക് പരിശോധിക്കാൻ കഴിയുന്ന ഒന്നാണ്. നിങ്ങളുടെ കീയെ തൊടുന്ന എല്ലാ ലൈനും ഒരു വായിക്കാവുന്ന ഫയലിൽ ജീവിക്കുന്നു, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ഇത് വീലിനുള്ളിൽ ഷിപ്പ് ചെയ്യുന്നു, വേർബറ്റിം സേവ് ചെയ്യുന്നു, ഒരു Subresource Integrity ഹാഷ് കൊണ്ട് പിൻ ചെയ്തിരിക്കുന്നു. ബ്രൗസർ ഞങ്ങൾ പബ്ലിഷ് ചെയ്തത് തന്നെ റൺ ചെയ്യുന്നു എന്ന് സ്ഥിരീകരിക്കാൻ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

അത് തെളിയിക്കാത്തത്: ഫയൽ ലോഡ് ചെയ്യുന്ന പേജ് ഞങ്ങൾ സേവ് ചെയ്യുന്നു, അതിനാൽ ഞങ്ങൾക്ക് വ്യത്യസ്തമായ ഒരു പേജ് സേവ് ചെയ്യാൻ കഴിയും. ഇന്റഗ്രിറ്റി ഹാഷുകൾ നിങ്ങളെ ഒരു കോംപ്രമൈസ്ഡ് CDN ൽ നിന്ന് സംരക്ഷിക്കുന്നു, വെണ്ടറിൽ നിന്നല്ല. നിങ്ങൾക്ക് ലഭിക്കുന്നത് എന്തെന്നാൽ ഏതൊരു സബ്സ്റ്റിറ്റ്യൂഷനും മനപ്പൂർവമായിരിക്കണം, പേജ് സോഴ്സിൽ ദൃശ്യമാകണം, ആർക്കും ഫെച്ച് ചെയ്യാവുന്ന PyPI യിലെ ഒരു ആർട്ടിഫാക്റ്റിൽ നിന്ന് വ്യത്യസ്തമായിരിക്കണം. സെൽഫ്-ഹോസ്റ്റിംഗ് അല്ലെങ്കിൽ ലോക്കൽ-ഒൺലി ആയി തുടരുന്നത് ഈ ഡിപെൻഡൻസിയെ പൂർണ്ണമായി ഒഴിവാക്കുന്നു.

## ഇൻസ്റ്റാൾ

```bash
pip install clawmetry     # then: clawmetry
```

അല്ലെങ്കിൽ ഒറ്റ-ലൈനർ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux, Windows ൽ Python 3.8+ വേണം, അതേ മെഷീനിൽ കുറഞ്ഞത് ഒരു ഏജന്റ് റൺടൈമും വേണം. Docker നിർദ്ദേശങ്ങൾ: [docs/DOCKER.md](docs/DOCKER.md).

അല്ലെങ്കിൽ ഏജന്റിനെ തന്നെ നിങ്ങൾക്കായി സെറ്റ് അപ്പ് ചെയ്യാൻ അനുവദിക്കുക. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) സ്കിൽ Claude Code, Codex, Cursor, Gemini CLI, Copilot അല്ലെങ്കിൽ OpenCode നെ ClawMetry ഇൻസ്റ്റാൾ ചെയ്യാനും, മെഷീനിലെ ഏജന്റുകൾ എന്ത് ചെയ്യുന്നു എന്തൊക്കെ ചെലവഴിക്കുന്നു എന്ന് റിപ്പോർട്ട് ചെയ്യാനും, ആവശ്യപ്പെടുമ്പോൾ ഒരു സെഷൻ നിർത്താനും, അപ്പ്രൂവലിനായി റിസ്കുള്ള ടൂൾ കോളുകൾ പിടിച്ചുനിർത്താനും പഠിപ്പിക്കുന്നു:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ഡോക്സ്

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ഓരോ അഡാപ്റ്ററും എന്ത് വായിക്കുന്നു, ഒരു റൺടൈം എങ്ങനെ ചേർക്കാം |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ഓരോ പ്രൊവൈഡറിനുമുള്ള വിൻഡോകൾ, കോംപാക്ഷൻ vs ഓവർഫ്ലോ, ഓരോ റൺടൈമിനുമുള്ള കവറേജ് |
| [Overhead](docs/OVERHEAD.md) | ഇൻസ്ട്രുമെന്റേഷന് എന്ത് ചെലവ് വരുന്നു, അളന്നത്, അത് പുനരുൽപ്പാദിപ്പിക്കാനുള്ള ഹാർനെസ് സഹിതം |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, ടയർ മാട്രിക്സ്, ലൈസൻസ് CLI |
| [Approvals & policies](docs/APPROVALS.md) | പ്രീ-എക്സിക്യൂഷൻ ഗേറ്റിംഗ്, റിസ്ക് സ്കോറിംഗ്, ഫോൺ അപ്പ്രൂവലുകൾ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ട്രെയ്സുകൾ എവിടെയും എക്സ്പോർട്ട് ചെയ്യുക, എന്തിൽ നിന്നും OTLP ഇൻജസ്റ്റ് ചെയ്യുക |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, റൺ ചെയ്യാവുന്ന ഉദാഹരണങ്ങൾ സഹിതം |
| [SDK tracking](docs/SDK_TRACKING.md) | നിങ്ങൾ തന്നെ നിർമ്മിച്ച ഏജന്റുകൾക്കുള്ള കോസ്റ്റ് ആട്രിബ്യൂഷൻ |
| [Chat channels](docs/CHANNELS.md) | Flow ൽ കാണിച്ചിരിക്കുന്ന ചാറ്റ് അഡാപ്റ്ററുകൾ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | സാൻഡ്ബോക്സ്ഡ് NVIDIA NemoClaw സെറ്റപ്പുകൾ |
| [Docker](docs/DOCKER.md) | ഇമേജ്, കമ്പോസ്, വോളിയം മൗണ്ടുകൾ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ഇത് അകത്ത് എങ്ങനെ പ്രവർത്തിക്കുന്നു; സോഴ്സിൽ നിന്ന് റൺ ചെയ്യുന്നത് |
| [Telemetry](docs/TELEMETRY.md) | അജ്ഞാത ഇൻസ്റ്റാൾ, ഡെസ്ക്ടോപ്പ്-ഓപ്പൺ പിംഗുകൾ, അവ എങ്ങനെ ഓഫ് ചെയ്യാം |

## സ്ക്രീൻഷോട്ടുകൾ

താഴെയുള്ള ഓരോ നമ്പറും ഒരു യഥാർത്ഥ മെഷീനിൽ നിന്നുള്ളതാണ്, റീഡ്-ഒൺലി ആയി, ഒന്നും സീഡ് ചെയ്യാതെ.

**എന്തെങ്കിലും തെറ്റാണെന്ന് ഇത് നിങ്ങളോട് പറയുന്നു, വെറും എന്ത് സംഭവിച്ചു എന്നല്ല.**
മുകളിൽ രണ്ട് അനോമലി ബാനറുകൾ: ദൈനിക ശരാശരിയുടെ 7 ഇരട്ടി ചെലവഴിക്കൽ, ഒരു 4.2x കോസ്റ്റ് സ്പൈക്ക്. അവയ്ക്ക് താഴെ, 667 സമീപകാല സെഷനുകളിൽ 324 എണ്ണം ഒരു വേസ്റ്റ് സിഗ്നൽ വഹിക്കുന്നു, കാരണം അനുസരിച്ച് ഇനം തിരിച്ചത്.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**പണം എവിടെ പോയി എന്ന് ഇത് നിങ്ങളെ ഓരോ വിൻഡോയിലും കാണിക്കുന്നു.**
ഇന്ന് $252.47, ഈ ആഴ്ച $513.15, ഈ മാസം $1,312.92, ഓരോന്നിനും അതിന് പിന്നിലെ ടോക്കണുകളും നിങ്ങളുടെ സബ്സ്ക്രിപ്ഷൻ ഇതിനകം കവർ ചെയ്യുന്ന അളവും സഹിതം. അതിന് താഴെ, ഏകദേശം $1,128/മാസം റിക്കവറബിൾ ആയി ഇനം തിരിച്ചത്, കാഷ് റീയൂസ് മൂലം ഇതിനകം $17,256/മാസം ലാഭിച്ചത്.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ഒരു മെസേജ് എങ്ങനെ ഒരു ഉത്തരമായി മാറുന്നു എന്ന് ഇത് വരച്ചുകാണിക്കുന്നു.**
ലൈവ് ഫ്ലോ ഡയഗ്രം: നിങ്ങൾ, അത് വന്ന ചാനൽ, ഗേറ്റ്‌വേ, ഇപ്പോൾ ഉത്തരം നൽകുന്ന മോഡൽ, അത് ഉപയോഗിച്ച എല്ലാ ടൂളും. ജോലി അവയിലൂടെ നീങ്ങുമ്പോൾ നോഡുകൾ തെളിയുന്നു.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**മെഷീനിലെ എല്ലാ ഏജന്റും, ഒരൊറ്റ ടേബിളിൽ.**
അത് എന്ത് റൺ ചെയ്യുന്നു, കഴിഞ്ഞ 24 മണിക്കൂറിലും ലൈഫ്ടൈമിലും അതിന് എന്ത് ചെലവ് വരുന്നു, അത് അവസാനം എപ്പോൾ കണ്ടു, അത് ആരുടേതാണ്, ഒരു സബ്സ്ക്രിപ്ഷൻ ബിൽ കവർ ചെയ്യുന്നുണ്ടോ. ഇവിടെ 14 ഏജന്റുകൾ, 3 സെഷനുകൾ പ്രവർത്തിക്കുന്നു, 13 നിശ്ചലം.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ഒരു ടേണിന്റെ സമയവും പണവും എവിടെ പോയി എന്ന് ഇത് കാണിക്കുന്നു, ടൂൾ ബൈ ടൂൾ.**
ഒരു യഥാർത്ഥ സെഷന്റെ ഒരു ടേൺ: $1.16 ന് 11.2 മിനിറ്റിൽ 11 ടൂളുകൾ. ഓരോ Bash കോളിനും മോഡൽ കോളിനും ടൈംലൈനിൽ അതിന്റേതായ ബാർ ലഭിക്കുന്നു, അതിനാൽ 4.1 മിനിറ്റ് റൺ ചെയ്ത കമാൻഡും 226ms റൺ ചെയ്തതും ഒരു നോട്ടത്തിൽ വേർതിരിച്ചറിയാം.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ഇത് ജോലിയെ ഗ്രേഡ് ചെയ്യുന്നു, വെറും ചെലവ് മാത്രമല്ല.**
ഈ ആഴ്ച ഒരു A: 54 ടാസ്ക്കുകൾ വൃത്തിയായി തിരിച്ചുവന്നു, 2 കഠിനമായവയ്ക്ക് $48.57 ചെലവായി, വിധിക്കാൻ കഴിയാത്തത്ര കുറച്ച് ആക്റ്റിവിറ്റിയുള്ള റണ്ണുകൾ വിജയങ്ങളായി കൗണ്ട് ചെയ്യുന്നതിന് പകരം ഗ്രേഡിൽ നിന്ന് ഒഴിവാക്കിയിരിക്കുന്നു. ഓരോ കഠിനമായ റണ്ണും അതിന്റെ ട്രെയ്സിലേക്ക് ലിങ്ക് ചെയ്യുന്നു.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**കോണ്ടെക്സ്റ്റ് വിൻഡോ എന്തുകൊണ്ട് നിറഞ്ഞുകൊണ്ടിരിക്കുന്നു എന്ന് ഇത് കാണിക്കുന്നു.**
ഏറ്റവും പുതിയ ടേണിൽ 1M-ടോക്കൺ വിൻഡോയിൽ 715K, ഒരു 83.3% പീക്ക്, ഓവർഫ്ലോയിൽ അല്ല, എല്ലാം പ്രോആക്റ്റീവ് ആയി ഫയർ ചെയ്ത 4 കോംപാക്ഷനുകൾ, അതിന് പിന്നിലെ ഓരോ ടേണിന്റെയും യൂട്ടിലൈസേഷൻ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**നിങ്ങൾ ഒന്നും കോൺഫിഗർ ചെയ്യാതെ ഡിറ്റക്ഷൻ പ്രവർത്തിക്കുന്നു.**
ബിൽറ്റ്-ഇൻ ഡിറ്റക്ടറുകൾ ഇൻസ്റ്റാൾ മുതൽ ഓൺ ആണ്: ഏജന്റ് നിശ്ചലമായി, ടെലിമെട്രി ഫീഡ് നിർത്തി, കോസ്റ്റ് സ്പൈക്ക്, ടോക്കൺ ബർസ്റ്റ്, എറർകൾ ഉയരുന്നു, എറർ സ്പൈക്ക്, ബഡ്ജറ്റ് ത്രെഷോൾഡ്, ത്രെട്ട് സിഗ്നേച്ചർ പൊരുത്തപ്പെട്ടു, സെക്യൂരിറ്റി ടൂൾ ഫൈൻഡിംഗ്, സെക്യൂരിറ്റി പോസ്ച്ചർ മാറി. അതിന് മുകളിൽ നിങ്ങളുടെ തന്നെ നിയമങ്ങൾ ഓപ്ഷണൽ ആണ്.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**റിസ്കുള്ള ഒരു കോൾ പിടിച്ചുനിർത്തുന്നത് ഓപ്റ്റ്-ഇൻ ആണ്, ഓഫ് ആയി ഷിപ്പ് ചെയ്യുന്നു.**
റിക്കർസീവ് ഡിലീറ്റുകൾ, ഫോഴ്സ് പുഷുകൾ, sudo, സീക്രട്ടുകൾ, പാക്കേജ് ഇൻസ്റ്റാളുകൾ, ഔട്ട്ബൗണ്ട് കോളുകൾ എന്നിവ ഓരോന്നിനും നിങ്ങൾക്ക് ഓൺ ചെയ്യാവുന്ന ഒരു നിയമം ലഭിക്കുന്നു. നിങ്ങൾ അത് ചെയ്യുന്നതുവരെ, ClawMetry നിരീക്ഷിക്കുന്നു, ഒന്നും മാറ്റുന്നില്ല. ഒന്ന് ഓൺ ആയാൽ, പൊരുത്തപ്പെടുന്ന കോളുകൾ ഇവിടെ (അല്ലെങ്കിൽ നിങ്ങളുടെ ഫോണിൽ) ഒരു അപ്പ്രൂവോ ഡിനൈയോ കിട്ടാൻ കാത്തിരിക്കുന്നു.

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

MIT · [@vivekchand](https://github.com/vivekchand) നിർമ്മിച്ചത് · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
