<!-- i18n-src:61beb8393e2f -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ஒரு ஏஜென்ட் முன்னேற்றம் எதுவும் இல்லாமலேயே நூறு டூல் கால்களைச் செய்யலாம்.** ClawMetry உங்கள் கோடிங் ஏஜென்ட்கள் ஏற்கனவே எழுதும் செஷன் கோப்புகளைப் படித்து, டைம்லைனையும், டூல் கால்களையும், ரன்டைம் வெளிப்படுத்தும் டோக்கன் மற்றும் செலவு தரவையும் ஒரே பார்வையில் கொண்டு வருகிறது — இதனால் வேலை செய்யும் நீண்ட ரன்னையும், முடங்கிப்போன ஒன்றையும் நீங்கள் வேறுபடுத்தி அறியலாம்.

**30 AI ஏஜென்ட் ரன்டைம்களுடன்** இயங்குகிறது — Claude Code, OpenAI Codex, Hermes, OpenClaw & மேலும் 26. உங்கள் முழு ஏஜென்ட் கடற்படைக்கும் ஒரே டாஷ்போர்டு. ([முழு பட்டியல்](SUPPORTED_RUNTIMES.txt), காட்டலாக் இலிருந்து உருவாக்கப்பட்டது.)

> 🌐 **இதை இதில் படியுங்கள்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. அனைத்தையும் தானாக கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கிறது. கட்டமைப்பு தேவையில்லை: ஏற்கனவே உங்களிடம் உள்ள ஏஜென்ட் ரன்டைம்களைக் கண்டறிந்து, அவற்றை படிப்பதற்கு மட்டுமே அணுகி, அவை எவ்வாறு இயங்குகின்றன என்பதில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## நிறுவுவதற்கு முன்

| | |
|---|---|
| **இது என்ன செய்கிறது** | உங்கள் ஏஜென்ட்கள் ஏற்கனவே எழுதும் செஷன் கோப்புகளையும் லாக்குகளையும் படிக்கிறது. SDK இல்லை, குறியீடு மாற்றம் இல்லை, உங்கள் ஆப்பில் இன்ஸ்ட்ரூமென்டேஷன் இல்லை. |
| **நீங்கள் என்ன பார்க்கிறீர்கள்** | செஷன் டைம்லைன், டூல்-பை-டூல் ரீப்ளே, டோக்கன் மற்றும் செலவு பிரிவு, மற்றும் பாதை சிக்னல்கள் (looping, மீண்டும் மீண்டும் தோல்விகள்) — ஒவ்வொரு ரன்டைமுக்கும். |
| **இலவசமானது என்ன** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw மற்றும் Goose** ஐ கணக்கு இல்லாமல், கீ இல்லாமல், நெட்வொர்க் அழைப்பு இல்லாமல் படிக்கிறது. மற்ற 27 — Claude Code, Codex, Cursor மற்றும் மற்றவை — closed-source `clawmetry-pro` துணைப் பயன்பாட்டால் படிக்கப்படுகின்றன, இது 7-நாள் சோதனையுடன் அல்லது ஒரு திட்டத்துடன் வருகிறது — சரியான பிரிவைக் காண [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ஐப் பார்க்கவும். |
| **எப்படித் தொடங்குவது** | `pip install clawmetry && clawmetry`, பின்னர் localhost:8900 ஐத் திறக்கவும். இந்த மெஷினில் இன்னும் ஏஜென்ட்கள் இல்லையா? `clawmetry --sample` மூன்று லேபிள் செய்யப்பட்ட செயற்கை செஷன்களில் திறக்கிறது. |
| **உங்கள் மெஷினில் இருந்து என்ன வெளியேறுகிறது** | நீங்கள் `clawmetry connect` இயக்கும் வரை செஷன் தரவு இல்லை. இயல்பாக இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும் ஆப்ட்-அவுட், எதுவும் செஷன் உள்ளடக்கத்தை சுமக்கவில்லை: ஒரு அநாமதேய இன்ஸ்டால் பிங் மற்றும் ஒரு PyPI பதிப்பு சோதனை. ஒவ்வொரு இலக்கும் [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது, கருத்துகளைப் படிப்பதை விட ஒரு வயர் கேப்சரிலிருந்து மீண்டும் கட்டமைக்கப்பட்டது. |

நீங்கள் வெளியீட்டை மதிப்பிடுவதற்கு முன் அறிந்து கொள்ள வேண்டிய இரண்டு வரம்புகள்: ரன்டைம்கள் மிகவும் வேறுபட்ட தரவை வெளிப்படுத்துகின்றன (சில எந்த செலவையும் வெளியிடுவதில்லை — [மேட்ரிக்ஸ்](docs/compatibility.md) ஒவ்வொரு ரன்டைமுக்கும் எது என்பதைக் கூறுகிறது), மேலும் ஒரு செயலைக் கவனிப்பது என்பது அதைத் தடுக்க முடியும் என்பதற்குச் சமமல்ல ([எந்த கட்டுப்பாடுகள் உண்மையானவை, ஒவ்வொரு ரன்டைமுக்கும்](docs/APPROVALS.md)).


## 30 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

**ஓபன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**கட்டணத் திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமுக்கும் அதே டாஷ்போர்டு கிடைக்கும். பலவற்றை ஒரே நேரத்தில் இயக்கினால், ஹெடர் ஸ்விட்சர் ஒவ்வொரு டேபையும் அவற்றில் ஒன்றுக்கு மறு-நோக்கம் செய்கிறது.

உங்கள் சொந்த ஏஜென்டை SDK இல் கட்டியிருக்கிறீர்களா? இன்டர்செப்டர் அதன் LLM கால்களையும் கண்காணிக்கும். [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ஐப் பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **செஷன்கள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, டர்ன் பை டர்ன், ரீப்ளேயுடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், செஷன் மற்றும் நாள் வாரியாக, அசாதாரண கொடிகளுடன்
- **ஃப்ளோ**: சேனல்கள், மாடல்கள் மற்றும் டூல்கள் வழியாக நகரும் செய்திகளின் நேரடி வரைபடம்
- **பிரெயின்**: நடக்கும்போது நடக்கும் தர்க்கம் மற்றும் டூல்-கால் நிகழ்வு ஸ்ட்ரீம்
- **கான்டெக்ஸ்ட் பிளோஅவுட்**: வழங்குநர் வாரியாக அளவிடப்பட்ட விண்டோ பயன்பாடு, காம்பாக்ஷன் vs வலுக்கட்டாய ஓவர்ஃப்ளோ, மற்றும் நாம் *பார்க்க முடியாதவற்றின்* ரன்டைம்-வாரியான வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **மெமரி & ஸ்கில்கள்**: ஒவ்வொரு ரன்டைமும் உண்மையில் ஏற்றிய கோப்புகள் மற்றும் ஸ்கில்கள்
- **ஆரோக்கியம் & லாக்குகள்**: டிஸ்க், மெமரி, பிழை விகிதங்கள், ரேட் லிமிட்கள், நேரடி லாக் ஸ்ட்ரீம்
- **அலர்ட்கள்**: பட்ஜெட் காப்கள், பிழை ஸ்பைக்குகள், ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, Email க்கு அனுப்பப்படும்
- **அப்ரூவல்கள்**: ஆபத்தான டூல் கால்களை *அவை இயங்குவதற்கு முன்* இடைநிறுத்தி, உங்கள் தொலைபேசியிலிருந்து அங்கீகரிக்கவும் ([எப்படி](docs/APPROVALS.md))

## கான்டெக்ஸ்ட் பிளோஅவுட், மற்றும் கண்காணிப்பதன் செலவு

எந்த ஏஜென்ட்-ஒப்பீட்டு டூலையும் நம்புவதற்கு முன் பதில் தெரிந்து கொள்ள வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்கள் முழுவதும் கான்டெக்ஸ்ட்-விண்டோ பிளோஅவுட்டை இது எப்படி கையாளுகிறது?**

ஒரு பயன்பாட்டு சதவீதம் அது எதைக் கொண்டு வகுக்கிறது என்பதைப் போலவே நேர்மையானது. ClawMetry [நீங்கள் படித்து PR செய்யக்கூடிய ஒரு அட்டவணையிலிருந்து](clawmetry/context_windows.py) வழங்குநர் வாரியாக விண்டோவை அளவிடுகிறது, இதில் Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM ஆகியவை உள்ளடங்கும். இது 30 ரன்டைம்களையும் ஒரே விற்பனையாளரின் அளவுகோலால் அளவிடுவதில்லை. அது முக்கியம்: Anthropic இன் 200K க்கு எதிராக மதிப்பிடப்பட்ட ஒரு 300K GPT-5 டர்ன் ">100%, blown" எனப் படிக்கிறது, உண்மையில் அது GPT-5 இன் 400K இல் 75% ஆக இருக்கும்போது. அதே அளவுகோல் உண்மையிலேயே overflow ஆன ஒரு 130K DeepSeek டர்னை வசதியான 65% ஆக மறைக்கிறது.

ஒவ்வொரு விண்டோவும் அதன் மூலத்துடன் வருகிறது: `model_table`, `explicit_marker`, `observed_floor`, அல்லது மாடல் தெரியாதபோது ஒரு நேர்மையான `default`. ஒரு யூகத்தின் மீது கட்டப்பட்ட ஒரு கேஜ் ஒரு லுக்அப்பின் மீது கட்டப்பட்ட ஒன்றின் அதே அதிகாரத்துடன் ஒருபோதும் காட்டப்படாது.

ClawMetry சில ரன்டைம்களில் மட்டுமே காம்பாக்ஷன் நிகழ்வுகளைப் பார்க்க முடியும். எனவே `GET /api/context-coverage` ஒவ்வொரு ரன்டைமுக்கும், **பூஜ்யம் என்பது "சுத்தமாக ஓடியது" எனப் பொருளா அல்லது "நாங்கள் குருடர்கள்" எனப் பொருளா** என்பதைப் புகாரளிக்கிறது. உண்மையில் குருடு என்று பொருள்படும் ஒரு `0` அப்படித்தான் கூறுகிறது. [முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**இன்ஸ்ட்ரூமென்டேஷன் எவ்வளவு செலவாகும்?**

| பாதை | உங்கள் ஏஜென்டுடன் சேர்க்கப்பட்டது | இயல்பானதா? |
|---|---|---|
| செஷன்-கோப்பு டெயிலிங் (அனைத்து 30 ரன்டைம்களும்) | **0**. தனி செயல்முறை, உங்கள் ஏஜென்டில் ClawMetry குறியீடு இல்லை | ஆன் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒரு LLM கால் ஒன்றுக்கு **+0.44 ms**, அல்லது 5s கால் ஒன்றின் 0.009% | ஆஃப் |
| Pre-tool ஹூக் கேட் (warm cache) | 36 ms இன்டர்ப்ரெட்டர் தளத்தின் மேல், கேட் செய்யப்பட்ட டூல் கால் ஒன்றுக்கு **+44 ms** | ஆஃப் |
| Enforcement ப்ராக்ஸி | ஒரு LLM கால் ஒன்றுக்கு **+9.7 ms** | ஆஃப் |

டீமன் ஹோஸ்ட் செலவு: **2,762 நிகழ்வுகள்/வினாடி** இன்ஜெஸ்ட், டிஸ்கில் **710 பைட்டுகள்/நிகழ்வு** (100k நிகழ்வுகளுக்கு 67.7 MB), மற்றும் பிஸியான இன்ஸ்டால் ஒன்றில் **ஒரு கோர் இன் ~12%** தொடர்ச்சியாக. அந்த கடைசி எண் எங்கள் சொந்த கூறப்பட்ட 5-10% பட்ஜெட்டை விட அதிகமாக உள்ளது, எனவே அது பக்கத்திலிருந்து விடப்படுவதற்குப் பதிலாக பின்தொடர வேண்டிய ஒரு பிழையாக வெளியிடப்படுகிறது.

Apple M2 Pro இல் `benchmarks/overhead.py` உடன் அளவிடப்பட்டது. ஹார்னஸ் ஒவ்வொரு நிலையையும் ஒரு தனி செயல்முறையில் இயக்குகிறது, அவற்றின் வரிசையை மாற்றி மாற்றி இயக்குகிறது, மேலும் **சுற்றுகள் அதன் அடையாளத்தில் உடன்படவில்லை என்றால் ஒரு எண்ணை அச்சிடுவதற்கு மறுக்கிறது**. அதை உங்கள் சொந்த மெஷினில் ஒரு நிமிடத்தில் இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ஹூக் கேட்கள் மற்றும் enforcement ப்ராக்ஸி உட்பட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது, மேலும் ஹார்னஸ் CI இல் Linux, macOS மற்றும் Windows இல் இயங்குகிறது. தெரிந்து கொள்ள வேண்டிய இரண்டு முடிவுகள்: Windows இல் ப்ராக்ஸி Linux ஐ விட சுமார் ஏழு மடங்கு அதிகமாக செலவாகிறது, மேலும் டீமன் தற்போது ஒரு கோரின் சுமார் 12% ஐ தொடர்ச்சியாகத் தாங்குகிறது, எங்கள் சொந்த 5-10% பட்ஜெட்டை விட அதிகமாக. மூல JSON, முறை, மற்றும் இன்னும் அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md) இல் உள்ளன.

## விலை நிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose, முழு டாஷ்போர்டு, லோக்கல் மட்டும் | $0 |
| **ஸ்டார்ட்டர்** | மேலே உள்ள மற்ற ஒவ்வொரு ரன்டைமும், ஃப்ளீட் வியூ, க்ளவுட் சிங்க் | ஒரு நோட் / மாதத்திற்கு $9 |
| **Pro** | ஸ்டார்ட்டர் + கட்டுப்பாடு மற்றும் மதிப்பீடு: அப்ரூவல்கள், டூல்-ரிஸ்க் பாலிசிகள், evals, அசாதாரண கண்டறிதல், செலவு ஆப்டிமைசர், OTel ஏற்றுமதி, tamper-evident audit log | ஒரு நோட் / மாதத்திற்கு $19 |

வருடாந்திர திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)** இல் உள்ளன. சுய-ஹோஸ்ட் செய்யப்பட்ட உரிமம் கீகள் க்ளவுட் இல்லாமல் வேலை செய்யும் (`clawmetry license`). சரியான இலவச/கட்டண பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) இல் உள்ளது.

## உங்கள் தரவு உங்கள் மெஷினில் தங்கியிருக்கும்

ClawMetry உள்ளூர் செஷன் கோப்புகளையும் லாக்குகளையும் படிக்கிறது. **நீங்கள் `clawmetry connect` இயக்காத வரை உங்கள் பெட்டியில் இருந்து செஷன் தரவு எதுவும் வெளியேறாது** — ப்ராம்ப்ட்கள், பதில்கள், டூல் ஆர்குமென்ட்கள், கோப்பு உள்ளடக்கங்கள் அல்லது லாக் வரிகள் இல்லை. நீங்கள் இணைக்கும்போது, ஸ்னாப்ஷாட் உங்கள் மெஷினை ஒருபோதும் விட்டு வெளியேறாத ஒரு கீயுடன் எண்ட்-டு-எண்ட் என்க்ரிப்ட் செய்யப்படுகிறது, மேலும் உங்கள் பிரௌசரில் டிக்ரிப்ட் செய்யப்படுகிறது. ஒரு நோடிற்கு கீ இல்லை என்றால், அப்லோட் தெளிவாக அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படுகிறது, மேலும் எந்த சர்வர் பதிலும் அதை அணைக்க முடியாது.

நீங்கள் இணைப்பதற்கு முன் இயல்பாக இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும் ஆப்ட்-அவுட், எதுவும் செஷன் தரவை சுமக்கவில்லை: ஒரு அநாமதேய இன்ஸ்டால் பிங் மற்றும் PyPI க்கு எதிரான ஒரு பதிப்பு சோதனை. ஒரு இயல்புநிலை இன்ஸ்டால் ஒரு ஸ்டார்ட்அப் பேனர் வரிக்காக உங்கள் பொது IP ஐ ஒரு முறை தேடும். ஒவ்வொரு இலக்கும், அது எதைச் சுமக்கிறது என்பதும், அதை எப்படி அணைப்பது என்பதும் [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளன; சுய-ஹோஸ்ட் செய்யப்பட்ட, மறு-இலக்கு வைக்கப்பட்ட மற்றும் காற்று-இடைவெளி நிறுவல்கள் எந்த விருப்பமான outbound கால்களும் செய்யாது.

டிக்ரிப்ஷன் உங்கள் பிரௌசரில், நாங்கள் உங்களுக்கு வழங்கும் குறியீட்டில் நடக்கிறது. அது ஒரு காலத்தில் ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள் சரிபார்க்கக்கூடிய ஒன்றாக உள்ளது. உங்கள் கீயைத் தொடும் ஒவ்வொரு வரியும் ஒரு படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது wheel க்குள் அனுப்பப்படுகிறது மற்றும் Subresource Integrity ஹாஷுடன் பின் செய்யப்பட்டு, அப்படியே வழங்கப்படுகிறது. பிரௌசர் நாங்கள் வெளியிட்டதை இயக்குகிறது என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

அது நிரூபிக்காதது என்ன: கோப்பை ஏற்றும் பக்கத்தை நாங்கள் வழங்குகிறோம், எனவே நாங்கள் வேறு ஒரு பக்கத்தை வழங்கலாம். Integrity ஹாஷ்கள் ஒரு சமரசம் செய்யப்பட்ட CDN இலிருந்து உங்களைப் பாதுகாக்கின்றன, விற்பனையாளரிடமிருந்து அல்ல. நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றீடும் வேண்டுமென்றே செய்யப்பட வேண்டும், பக்க மூலத்தில் தெரியும், மற்றும் யாரும் பெறக்கூடிய PyPI இல் உள்ள ஒரு கலைப்பொருளிலிருந்து வேறுபட்டதாக இருக்க வேண்டும். சுய-ஹோஸ்டிங் அல்லது உள்ளூரில் மட்டும் இருப்பது இந்த சார்பை முற்றிலும் நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பின்னர்: clawmetry
```

அல்லது ஒரு-லைனர்: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows இல் Python 3.8+ தேவை, மற்றும் அதே மெஷினில் குறைந்தது ஒரு ஏஜென்ட் ரன்டைம் தேவை. Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

அல்லது ஏஜென்டையே அதை உங்களுக்காக அமைக்க விடுங்கள். [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) ஸ்கில் Claude Code, Codex, Cursor, Gemini CLI, Copilot அல்லது OpenCode க்கு ClawMetry ஐ நிறுவவும், மெஷினில் உள்ள ஏஜென்ட்கள் என்ன செய்கின்றன, செலவு செய்கின்றன என்பதைப் புகாரளிக்கவும், கோரிக்கையின் பேரில் ஒரு செஷனை நிறுத்தவும், அங்கீகாரத்திற்காக ஆபத்தான டூல் கால்களை நிறுத்தி வைக்கவும் கற்றுக்கொடுக்கிறது:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ஆவணங்கள்

| | |
|---|---|
| [ரன்டைம் இணக்கத்தன்மை](docs/compatibility.md) | ஒவ்வொரு அடாப்டரும் என்ன படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [கான்டெக்ஸ்ட் பிளோஅவுட்](docs/CONTEXT_BLOWOUT.md) | வழங்குநர்-வாரியான விண்டோக்கள், காம்பாக்ஷன் vs ஓவர்ஃப்ளோ, ரன்டைம்-வாரியான கவரேஜ் |
| [ஓவர்ஹெட்](docs/OVERHEAD.md) | இன்ஸ்ட்ரூமென்டேஷன் எவ்வளவு செலவாகும், அளவிடப்பட்டது, மீண்டும் உருவாக்குவதற்கான ஹார்னஸுடன் |
| [Entitlements](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், tier மேட்ரிக்ஸ், license CLI |
| [அப்ரூவல்கள் & பாலிசிகள்](docs/APPROVALS.md) | Pre-execution gating, ரிஸ்க் ஸ்கோரிங், தொலைபேசி அப்ரூவல்கள் |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | எங்கும் ட்ரேசுகளை ஏற்றுமதி செய்யவும், எதிலிருந்தும் OTLP ஐ இன்ஜெஸ்ட் செய்யவும் |
| [உங்கள் சொந்த ஏஜென்டைக் கொண்டு வாருங்கள்](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain முழுவதுமாக, இயங்கக்கூடிய உதாரணங்களுடன் |
| [SDK கண்காணிப்பு](docs/SDK_TRACKING.md) | நீங்களே கட்டிய ஏஜென்ட்களுக்கான செலவு பண்புவகைப்படுத்தல் |
| [சாட் சேனல்கள்](docs/CHANNELS.md) | ஃப்ளோவில் காட்டப்படும் சாட் அடாப்டர்கள் |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | இமேஜ், compose, volume mounts |
| [கட்டமைப்பு](ARCHITECTURE.md) · [டெவலப்மென்ட்](docs/DEVELOPMENT.md) | உள்ளே இது எப்படி வேலை செய்கிறது; மூலத்திலிருந்து இயக்குதல் |
| [டெலிமெட்ரி](docs/TELEMETRY.md) | அநாமதேய இன்ஸ்டால் மற்றும் டெஸ்க்டாப்-ஓபன் பிங்குகள், மற்றும் அவற்றை எப்படி அணைப்பது |

## ஸ்கிரீன்ஷாட்டுகள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான மெஷினில் இருந்து, படிப்பதற்கு மட்டுமான அணுகல் மூலம், எதுவும் விதைக்கப்படாமல் பெறப்பட்டது.

**ஏதாவது தவறாக இருக்கும்போது இது உங்களுக்குச் சொல்கிறது, என்ன நடந்தது என்பதை மட்டும் அல்ல.**
மேலே இரண்டு அசாதாரண பேனர்கள்: செலவு தினசரி சராசரியை விட 7x இயங்குகிறது, மற்றும் 4.2x செலவு ஸ்பைக். அவற்றுக்குக் கீழே, சமீபத்திய 667 செஷன்களில் 324, காரணத்தால் பட்டியலிடப்பட்ட, ஒரு வீண் சிக்னலை சுமக்கின்றன.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கு சென்றது என்பதை இது ஒவ்வொரு விண்டோவிலும் உங்களுக்குக் காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றும் அதன் பின்னால் உள்ள டோக்கன்களுடனும், உங்கள் சந்தா ஏற்கனவே எவ்வளவு உள்ளடக்குகிறது என்பதுடனும். அதற்குக் கீழே, சுமார் $1,128/மாதம் மீட்கக்கூடியதாக பட்டியலிடப்பட்டு, ஏற்கனவே கேச் மறுபயன்பாட்டால் $17,256/மாதம் சேமிக்கப்பட்டுள்ளது.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு செய்தி எப்படி ஒரு பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
நேரடி ஃப்ளோ வரைபடம்: நீங்கள், அது வந்த சேனல், கேட்வே, தற்போது பதிலளிக்கும் மாடல், மற்றும் அது அணுகிய ஒவ்வொரு டூலும். வேலை அவற்றின் வழியாக நகரும்போது நோடுகள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**மெஷினில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே அட்டவணையில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் ஆயுட்காலம் முழுவதும் எவ்வளவு செலவாகிறது, அது கடைசியாக எப்போது பார்க்கப்பட்டது, யாருக்குச் சொந்தமானது, மற்றும் ஒரு சந்தா பில்லை ஈடுகட்டுகிறதா என்பது. இங்கே 14 ஏஜென்ட்கள், 3 செஷன்கள் வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கு சென்றது என்பதை இது டூல் வாரியாகக் காட்டுகிறது.**
ஒரு உண்மையான செஷனின் ஒரு டர்ன்: 11.2 நிமிடங்களில் $1.16 க்கு 11 டூல்கள். ஒவ்வொரு Bash கால் மற்றும் மாடல் கால்லும் டைம்லைனில் அதன் சொந்த பட்டியைப் பெறுகிறது, எனவே 4.1 நிமிடங்கள் இயங்கிய கட்டளையும் 226ms இயங்கியதும் ஒரு பார்வையில் வேறுபடுத்தப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பிடுகிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக திரும்பின, 2 கடினமானவை $48.57 செலவழித்தன, மேலும் மதிப்பிட போதுமான செயல்பாடு இல்லாத ரன்கள் வெற்றிகளாக கணக்கிடப்படுவதற்குப் பதிலாக தரத்திலிருந்து விடப்படுகின்றன. ஒவ்வொரு கடினமான ரன்னும் அதன் ட்ரேசுக்கு இணைக்கிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**கான்டெக்ஸ்ட் விண்டோ ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் விண்டோவில் 715K, 83.3% உச்சம், ஓவர்ஃப்ளோவில் அல்லாமல் proactive ஆக ஏற்பட்ட 4 காம்பாக்ஷன்கள், மேலும் அதற்குப் பின்னால் உள்ள ஒவ்வொரு டர்னின் பயன்பாடும்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
உள்ளமைந்த கண்டறிபவைகள் நிறுவலிலிருந்தே ஆனில் உள்ளன: ஏஜென்ட் அமைதியானது, டெலிமெட்ரி ஃபீட் நிறுத்தப்பட்டது, செலவு ஸ்பைக், டோக்கன் பர்ஸ்ட், பிழைகள் ஏறுகின்றன, பிழை ஸ்பைக், பட்ஜெட் threshold, threat signature பொருந்தியது, செக்யூரிட்டி டூல் கண்டுபிடிப்பு, செக்யூரிட்டி posture மாற்றம். உங்கள் சொந்த விதிகள் மேலதிகமாக விருப்பமானவை.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ஒரு ஆபத்தான கால்லை நிறுத்தி வைப்பது ஆப்ட்-இன், மேலும் ஆஃப் ஆக அனுப்பப்படுகிறது.**
Recursive deletes, force pushes, sudo, secrets, package installs மற்றும் outbound calls ஒவ்வொன்றும் நீங்கள் ஆன் செய்யக்கூடிய ஒரு விதியைப் பெறுகின்றன. நீங்கள் அதைச் செய்யும் வரை, ClawMetry கவனிக்கிறது, எதையும் மாற்றாது. ஒன்று ஆன் ஆனதும், பொருந்தும் கால்கள் இங்கே (அல்லது உங்கள் தொலைபேசியில்) ஒரு அங்கீகாரம் அல்லது மறுப்புக்காக காத்திருக்கும்.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

மேலும், ரன்டைம் வாரியாக: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## அங்கீகாரம்

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## நட்சத்திர வரலாறு

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## உரிமம்

MIT · [@vivekchand](https://github.com/vivekchand) ஆல் கட்டப்பட்டது · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
