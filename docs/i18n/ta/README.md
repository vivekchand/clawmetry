<!-- i18n-src:a855a14295b0 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ஒரு ஏஜென்ட் முன்னேற்றம் எதுவும் இல்லாமல் நூறு டூல் கால்களைச் செய்யக்கூடும்.** ClawMetry
உங்கள் கோடிங் ஏஜென்ட்கள் ஏற்கனவே எழுதும் செஷன் கோப்புகளைப் படித்து, டைம்லைன், டூல்
கால்கள் மற்றும் ரன்டைம் வெளிப்படுத்தும் டோக்கன் மற்றும் செலவு தரவு அனைத்தையும் ஒரே
காட்சியில் கொண்டுவருகிறது — இதனால் வேலை செய்யும் நீண்ட ரன்னையும், நிற்றுப்போன ஒன்றையும்
நீங்கள் வேறுபடுத்தி அறியலாம்.

**32 AI ஏஜென்ட் ரன்டைம்களுடன்** வேலை செய்கிறது — Claude Code, OpenAI Codex, Hermes, OpenClaw & மேலும் 28. உங்கள் முழு ஏஜென்ட் ஃப்ளீட்டிற்கும் ஒரே டாஷ்போர்டு. ([முழு பட்டியல்](SUPPORTED_RUNTIMES.txt), கேடலாக்கிலிருந்து உருவாக்கப்பட்டது.)

> 🌐 **இதை இதில் படியுங்கள்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். கட்டமைப்பு தேவையில்லை: நீங்கள் ஏற்கனவே வைத்திருக்கும்
ஏஜென்ட் ரன்டைம்களை இது கண்டறிந்து, அவற்றை படிக்க மட்டும் அணுகுகிறது, மேலும் அவை எப்படி
இயங்குகின்றன என்பதில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## நிறுவும் முன்

| | |
|---|---|
| **இது என்ன செய்கிறது** | உங்கள் ஏஜென்ட்கள் ஏற்கனவே எழுதும் செஷன் கோப்புகள் மற்றும் லாக்குகளைப் படிக்கிறது. SDK இல்லை, குறியீட்டு மாற்றம் இல்லை, உங்கள் ஆப்பில் இன்ஸ்ட்ரூமெண்டேஷன் இல்லை. |
| **நீங்கள் என்ன பார்ப்பீர்கள்** | செஷன் டைம்லைன், டூல்-பை-டூல் ரீப்ளே, டோக்கன் மற்றும் செலவு பிரிவு, மற்றும் ரன்டைம் அடிப்படையில் trajectory சிக்னல்கள் (லூப்பிங், மீண்டும் மீண்டும் தோல்விகள். |
| **இலவசமானது என்ன** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw மற்றும் Goose** ஐ கணக்கு, கீ அல்லது நெட்வொர்க் கால் எதுவும் இல்லாமல் படிக்கிறது. மற்ற 27 — Claude Code, Codex, Cursor மற்றும் மற்றவை — 7-நாள் டிரையல் அல்லது திட்டத்துடன் வரும் closed-source `clawmetry-pro` துணைப் பயன்பாட்டால் படிக்கப்படுகின்றன — சரியான பிரிவுக்கு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) பார்க்கவும். |
| **எப்படி தொடங்குவது** | `pip install clawmetry && clawmetry`, பின்னர் localhost:8900 ஐ திறக்கவும். இந்த மெஷினில் இன்னும் ஏஜென்ட்கள் இல்லையா? `clawmetry --sample` மூன்று லேபிள் செய்யப்பட்ட செயற்கை செஷன்களுடன் திறக்கும். |
| **உங்கள் மெஷினில் இருந்து என்ன வெளியேறுகிறது** | நீங்கள் `clawmetry connect` இயக்காத வரை செஷன் தரவு எதுவும் இல்லை. இயல்பாக இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும் opt-out செய்யக்கூடியவை, செஷன் உள்ளடக்கத்தை எதுவும் சுமக்காதவை: அநாமதேய நிறுவல் பிங் மற்றும் PyPI பதிப்பு சரிபார்ப்பு. ஒவ்வொரு இலக்கும் [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது, கருத்துகளைப் படிப்பதற்குப் பதிலாக ஒரு wire capture இலிருந்து மீண்டும் கட்டமைக்கப்பட்டது. |

நீங்கள் வெளியீட்டை மதிப்பிடும் முன் அறிந்து கொள்ள வேண்டிய இரண்டு வரம்புகள்: ரன்டைம்கள்
மிகவும் வேறுபட்ட தரவை வெளிப்படுத்துகின்றன (சில செலவை எதுவும் வெளியிடுவதில்லை —
[matrix](docs/compatibility.md) இல் எந்த ரன்டைம் என்பது தெரிகிறது), மேலும் ஒரு
செயலைக் கவனிப்பது என்பது அதைத் தடுக்க முடியும் என்பதற்கு சமமல்ல ([ஒவ்வொரு ரன்டைமிலும்
எந்த கட்டுப்பாடுகள் உண்மையானவை](docs/APPROVALS.md)).


## 32 ஏஜென்ட் ரன்டைம்களுடன் வேலை செய்கிறது

**ஓபன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**கட்டணத் திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமும் ஒரே டாஷ்போர்டைப் பெறுகிறது. பலவற்றை ஒரே நேரத்தில் இயக்கினால், ஹெடர்
சுவிட்சர் ஒவ்வொரு டேபையும் அவற்றில் ஒன்றுக்கு மறு-ஸ்கோப் செய்யும்.

SDK இல் உங்கள் சொந்த ஏஜென்டை உருவாக்கினீர்களா? இன்டர்செப்டர் அதன் LLM கால்களையும்
டிராக் செய்கிறது. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) பார்க்கவும்.

## நீங்கள் என்ன பெறுவீர்கள்

- **செஷன்கள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, டர்ன் டர்னாக, ரீப்ளேயுடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், செஷன் மற்றும் நாள் வாரியாக, ஆனமலி கொடிகளுடன்
- **ஃப்ளோ**: சேனல்கள், மாடல்கள் மற்றும் டூல்கள் வழியாக நகரும் மெசேஜ்களின் நேரடி வரைபடம்
- **பிரெயின்**: நிகழும் போது reasoning மற்றும் tool-call இவென்ட் ஸ்ட்ரீம்
- **சூழல் வெடிப்பு**: வழங்குநர் வாரியாக அளவிடப்பட்ட விண்டோ பயன்பாடு, compaction vs கட்டாய overflow, மேலும் நாம் *பார்க்க முடியாதவற்றின்* ரன்டைம்-வாரியான வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **நினைவகம் & திறன்கள்**: ஒவ்வொரு ரன்டைமும் உண்மையில் லோட் செய்த கோப்புகள் மற்றும் திறன்கள்
- **ஆரோக்கியம் & லாக்குகள்**: டிஸ்க், நினைவகம், பிழை விகிதங்கள், ரேட் லிமிட்கள், நேரடி லாக் ஸ்ட்ரீம்
- **அலர்ட்கள்**: பட்ஜெட் வரம்புகள், பிழை ஸ்பைக்குகள், ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, Email க்கு அனுப்பப்படும்
- **அப்ரூவல்கள்**: ஆபத்தான டூல் கால்களை அவை இயங்கு*வதற்கு முன்* இடைநிறுத்தி, உங்கள் ஃபோனிலிருந்து அப்ரூவ் செய்யலாம் ([எப்படி](docs/APPROVALS.md))

## சூழல் வெடிப்பு, மற்றும் கண்காணிப்பதன் செலவு

எந்த ஏஜென்ட்-ஒப்பீட்டு கருவியையும் நம்புவதற்கு முன் பதிலளிக்க வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்கள் முழுவதும் சூழல்-விண்டோ வெடிப்பை இது எப்படி கையாளுகிறது?**

பயன்பாட்டு சதவீதம் அது எதை வகுக்கிறது என்பதைப் போலவே நேர்மையானது. ClawMetry
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM ஐ
உள்ளடக்கிய, நீங்கள் படித்து PR செய்யக்கூடிய [ஒரு டேபிளில்](clawmetry/context_windows.py)
இருந்து ஒவ்வொரு வழங்குநருக்கும் ஏற்ப விண்டோவை அளவிடுகிறது. இது 32 ரன்டைம்களையும் ஒரே
வெண்டரின் அளவுகோலால் அளவிடுவதில்லை. இது முக்கியமானது: Anthropic இன் 200K க்கு எதிராக
மதிப்பிடப்படும் ஒரு 300K GPT-5 டர்ன் ">100%, வெடித்துவிட்டது" என்று படிக்கும், ஆனால்
உண்மையில் அது GPT-5 இன் 400K இல் 75% தான். அதே அளவுகோல் உண்மையிலேயே overflow ஆன
130K DeepSeek டர்னை வசதியான 65% ஆக மறைக்கிறது.

ஒவ்வொரு விண்டோவும் அதன் provenance உடன் வருகிறது: `model_table`, `explicit_marker`,
`observed_floor`, அல்லது மாடல் நமக்குத் தெரியாதபோது நேர்மையான `default`. யூகத்தின்
அடிப்படையில் கட்டப்பட்ட ஒரு கேஜ் ஒருபோதும் lookup இன் அடிப்படையில் கட்டப்பட்ட ஒன்றைப்
போன்ற அதிகாரத்துடன் காட்டப்படாது.

ClawMetry சில ரன்டைம்களில் மட்டுமே compaction இவென்ட்களைப் பார்க்க முடியும். எனவே
`GET /api/context-coverage` ஒவ்வொரு ரன்டைமுக்கும், **ஒரு பூஜ்ஜியம் "சுத்தமாக ஓடியது"
என்று அர்த்தமா அல்லது "நாம் குருடர்" என்று அர்த்தமா** என்பதைப் புகாரளிக்கிறது.
உண்மையில் குருடு என்று அர்த்தமுள்ள ஒரு `0` அப்படித்தான் சொல்கிறது.
[முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**இன்ஸ்ட்ரூமெண்டேஷனின் செலவு என்ன?**

| பாதை | உங்கள் ஏஜென்டில் சேர்க்கப்பட்டது | இயல்பாக? |
|---|---|---|
| செஷன்-கோப்பு டெய்லிங் (எல்லா 32 ரன்டைம்களும்) | **0**. தனி செயல்முறை, உங்கள் ஏஜென்டில் ClawMetry குறியீடு இல்லை | ஆன் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒரு LLM கால் ஒன்றுக்கு **+0.44 ms**, அல்லது 5s கால் ஒன்றின் 0.009% | ஆஃப் |
| Pre-tool ஹுக் கேட் (warm cache) | gate செய்யப்பட்ட ஒரு டூல் கால் ஒன்றுக்கு **+44 ms**, 36 ms interpreter floor க்கு மேல் | ஆஃப் |
| Enforcement ப்ராக்ஸி | ஒரு LLM கால் ஒன்றுக்கு **+9.7 ms** | ஆஃப் |

Daemon ஹோஸ்ட் செலவு: **2,762 events/sec** ingest, **710 bytes/event** டிஸ்க்கில்
(100k events க்கு 67.7 MB), மற்றும் பிசியான நிறுவலில் நிலையான **~12% of one core**.
அந்த கடைசி எண் நாங்கள் குறிப்பிட்ட 5-10% பட்ஜெட்டை மீறியுள்ளது, எனவே அது பக்கத்தில்
விட்டுவிடுவதற்குப் பதிலாக விரட்டப்பட வேண்டிய ஒரு பிழையாக வெளியிடப்படுகிறது.

Apple M2 Pro இல் `benchmarks/overhead.py` உடன் அளவிடப்பட்டது. Harness ஒவ்வொரு
நிலையையும் தனி செயல்முறையில் இயக்குகிறது, அவற்றின் வரிசையை மாற்றுகிறது, மேலும்
**சுற்றுகள் அதன் அடையாளத்தில் உடன்படாதபோது ஒரு எண்ணை அச்சிட மறுக்கிறது**. அதை உங்கள்
சொந்த மெஷினில் ஒரு நிமிடத்தில் இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ஹுக் கேட்கள் மற்றும் enforcement ப்ராக்ஸி உட்பட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது,
மேலும் harness Linux, macOS மற்றும் Windows இல் CI இல் இயங்குகிறது. அறிந்து கொள்ள
வேண்டிய இரண்டு முடிவுகள்: ப்ராக்ஸி Windows இல் Linux ஐ விட சுமார் ஏழு மடங்கு அதிக
செலவாகும், மேலும் daemon தற்போது ஒரு core இன் சுமார் 12% ஐ நிலையாகப் பராமரிக்கிறது,
இது நாங்கள் குறிப்பிட்ட 5-10% பட்ஜெட்டை மீறியது. மூல JSON, முறை, மற்றும் இன்னும்
அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md) இல் உள்ளன.

## விலை நிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose, முழு டாஷ்போர்டு, லோக்கல் மட்டும் | $0 |
| **ஸ்டார்ட்டர்** | மேலே உள்ள மற்ற ஒவ்வொரு ரன்டைமும், ஃப்ளீட் வியூ, க்ளவுட் சிங்க் | ஒரு நோட்டுக்கு $9 / மாதம் |
| **Pro** | ஸ்டார்ட்டர் + கட்டுப்பாடு மற்றும் மதிப்பீடு: அப்ரூவல்கள், டூல்-ரிஸ்க் கொள்கைகள், evals, ஆனமலி கண்டறிதல், செலவு ஆப்டிமைசர், OTel எக்ஸ்போர்ட், tamper-evident ஆடிட் லாக் | ஒரு நோட்டுக்கு $19 / மாதம் |

வருடாந்திர திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள்
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** இல் உள்ளன. Self-hosted
லைசென்ஸ் கீகள் க்ளவுட் இல்லாமல் வேலை செய்கின்றன (`clawmetry license`). சரியான
இலவச/கட்டண பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) இல் உள்ளது.

## உங்கள் தரவு உங்கள் மெஷினில் மட்டுமே இருக்கும்

ClawMetry லோக்கல் செஷன் கோப்புகள் மற்றும் லாக்குகளைப் படிக்கிறது. **நீங்கள்
`clawmetry connect` இயக்காத வரை உங்கள் பெட்டியிலிருந்து செஷன் தரவு எதுவும்
வெளியேறாது** — ப்ராம்ப்ட்கள், பதில்கள், டூல் ஆர்குமெண்ட்கள், கோப்பு உள்ளடக்கங்கள்
அல்லது லாக் வரிகள் இல்லை. நீங்கள் இணைக்கும்போது, ஸ்னாப்ஷாட் உங்கள் மெஷினை ஒருபோதும்
விட்டு வெளியேறாத கீ மூலம் end-to-end encrypt செய்யப்பட்டு, உங்கள் பிரவுசரில்
decrypt செய்யப்படுகிறது. ஒரு நோட்டுக்கு கீ இல்லையென்றால், அப்லோட் clear ஆக
அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படும், மேலும் எந்த சர்வர் பதிலும் அதை
ஆஃப் செய்ய முடியாது.

நீங்கள் இணைக்கும் முன் இயல்பாக இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும் opt-out
செய்யக்கூடியவை, செஷன் தரவை சுமக்காதவை: அநாமதேய நிறுவல் பிங் மற்றும் PyPI க்கு
எதிரான பதிப்பு சரிபார்ப்பு. இயல்புநிலை நிறுவலும் தொடக்க பேனர் வரிக்காக உங்கள்
பொது IP ஐ ஒருமுறை பார்க்கிறது. ஒவ்வொரு இலக்கும், அது என்ன சுமக்கிறது மற்றும் அதை
எப்படி ஆஃப் செய்வது என்பது [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது;
self-hosted, repointed மற்றும் air-gapped நிறுவல்கள் விருப்பமான வெளிச்செல்லும்
கால்கள் எதையும் செய்யாது.

Decryption உங்கள் பிரவுசரில், நாங்கள் உங்களுக்கு வழங்கும் குறியீட்டில்
நிகழ்கிறது. அது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள்
சரிபார்க்கக்கூடிய ஒன்றாக உள்ளது. உங்கள் கீயைத் தொடும் ஒவ்வொரு வரியும் ஒரே
படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
இது wheel க்குள் ஷிப் செய்யப்பட்டு, verbatim ஆக வழங்கப்பட்டு, ஒரு Subresource
Integrity ஹாஷுடன் பின் செய்யப்பட்டுள்ளது. பிரவுசர் நாங்கள் வெளியிட்டதை
இயக்குகிறதா என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

இது எதை நிரூபிக்கவில்லை: கோப்பை லோட் செய்யும் பக்கத்தை நாங்கள் வழங்குகிறோம்,
எனவே நாங்கள் வேறு பக்கத்தை வழங்கக்கூடும். Integrity ஹாஷ்கள் ஒரு
compromised CDN இலிருந்து உங்களைப் பாதுகாக்கும், விற்பனையாளரிடமிருந்து அல்ல.
நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றீடும் வேண்டுமென்றே செய்யப்பட்டதாகவும்,
பக்க மூலத்தில் தெரியும்படியும், யாரும் பெறக்கூடிய PyPI இல் உள்ள ஒரு
கலைப்பொருளிலிருந்து வேறுபட்டதாகவும் இருக்க வேண்டும். Self-hosting அல்லது
local-only ஆக இருப்பது இந்த சார்பை முழுவதுமாக நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பின்னர்: clawmetry
```

அல்லது ஒரு-லைனர்: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows இல் Python 3.8+ மற்றும் அதே மெஷினில் குறைந்தது ஒரு
ஏஜென்ட் ரன்டைம் தேவை. Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

அல்லது ஏஜென்ட் அதை உங்களுக்காக அமைக்கட்டும். [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
திறன் Claude Code, Codex, Cursor, Gemini CLI, Copilot அல்லது OpenCode க்கு
ClawMetry ஐ நிறுவவும், மெஷினில் உள்ள ஏஜென்ட்கள் என்ன செய்கின்றன மற்றும் என்ன
செலவழிக்கின்றன என்பதைப் புகாரளிக்கவும், கோரிக்கையின் பேரில் ஒரு செஷனை நிறுத்தவும்,
மற்றும் ஆபத்தான டூல் கால்களை அப்ரூவலுக்காக பிடித்து வைக்கவும் கற்றுக்கொடுக்கிறது:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ஆவணங்கள்

| | |
|---|---|
| [ரன்டைம் இணக்கத்தன்மை](docs/compatibility.md) | ஒவ்வொரு அடாப்டரும் என்ன படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [சூழல் வெடிப்பு](docs/CONTEXT_BLOWOUT.md) | வழங்குநர்-வாரியான விண்டோக்கள், compaction vs overflow, ரன்டைம்-வாரியான கவரேஜ் |
| [Overhead](docs/OVERHEAD.md) | இன்ஸ்ட்ரூமெண்டேஷன் என்ன செலவாகும், அளவிடப்பட்டது, மறு உருவாக்கம் செய்ய harness உடன் |
| [Entitlements](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், tier matrix, license CLI |
| [அப்ரூவல்கள் & கொள்கைகள்](docs/APPROVALS.md) | Pre-execution gating, risk scoring, ஃபோன் அப்ரூவல்கள் |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces ஐ எங்கும் எக்ஸ்போர்ட் செய்யவும், எதிலிருந்தும் OTLP ஐ ingest செய்யவும் |
| [உங்கள் சொந்த ஏஜென்டைக் கொண்டு வாருங்கள்](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, இயங்கக்கூடிய உதாரணங்களுடன் |
| [SDK டிராக்கிங்](docs/SDK_TRACKING.md) | நீங்களே உருவாக்கிய ஏஜென்ட்களுக்கான செலவு attribution |
| [சாட் சேனல்கள்](docs/CHANNELS.md) | Flow இல் காட்டப்படும் சாட் அடாப்டர்கள் |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | இமேஜ், compose, volume mounts |
| [கட்டமைப்பு](ARCHITECTURE.md) · [டெவலப்மென்ட்](docs/DEVELOPMENT.md) | இது உள்ளே எப்படி வேலை செய்கிறது; சோர்ஸிலிருந்து இயக்குதல் |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் டெஸ்க்டாப்-ஓப்பன் பிங்குகள், மற்றும் அவற்றை எப்படி ஆஃப் செய்வது |

## ஸ்கிரீன்ஷாட்கள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான மெஷினில் இருந்து, படிக்க மட்டும், எதுவும்
seed செய்யாமல் எடுக்கப்பட்டது.

**எது நடந்தது என்பதை மட்டும் அல்ல, எப்போது எதோ தவறாக இருக்கிறது என்பதையும் இது உங்களுக்குச் சொல்கிறது.**
மேலே இரண்டு ஆனமலி பேனர்கள்: செலவு தினசரி சராசரியை விட 7x ஓடுகிறது, மற்றும் 4.2x
செலவு ஸ்பைக். அவற்றுக்குக் கீழே, சமீபத்திய 667 செஷன்களில் 324, ஒரு waste
சிக்னலைச் சுமந்து, காரணத்தால் வகைப்படுத்தப்பட்டுள்ளது.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கு போனது என்பதை இது ஒவ்வொரு விண்டோவிலும் காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றும் அதன் பின்னால்
உள்ள டோக்கன்களுடனும் உங்கள் சப்ஸ்கிரிப்ஷன் ஏற்கனவே எவ்வளவு கவர் செய்கிறது என்பதுடனும்.
அதற்குக் கீழே, சுமார் $1,128/மாதம் recoverable என்று வகைப்படுத்தப்பட்டு, cache
reuse மூலம் ஏற்கனவே $17,256/மாதம் சேமிக்கப்பட்டுள்ளது.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு மெசேஜ் எப்படி பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
நேரடி ஃப்ளோ வரைபடம்: நீங்கள், அது வந்த சேனல், gateway, தற்போது பதிலளிக்கும்
மாடல், மற்றும் அது அணுகிய ஒவ்வொரு டூலும். வேலை அவற்றின் வழியாக நகரும்போது
நோடுகள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**மெஷினில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே டேபிளில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் வாழ்நாள் முழுவதும் அது
என்ன செலவாகிறது, அது கடைசியாக எப்போது பார்க்கப்பட்டது, யாருக்குச் சொந்தமானது,
மற்றும் ஒரு சப்ஸ்கிரிப்ஷன் பில்லை கவர் செய்கிறதா. இங்கே 14 ஏஜென்ட்கள், 3 செஷன்கள்
வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கு போனது என்பதை, டூல் வாரியாக இது காட்டுகிறது.**
ஒரு உண்மையான செஷனின் ஒரு டர்ன்: 11.2 நிமிடங்களில் 11 டூல்கள் $1.16 க்கு. ஒவ்வொரு
Bash கால் மற்றும் மாடல் காலும் டைம்லைனில் அதன் சொந்த பட்டியைப் பெறுகிறது, எனவே
4.1 நிமிடங்கள் ஓடிய கட்டளையும் 226ms ஓடியதும் ஒரே பார்வையில் வேறுபடுத்தப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பிடுகிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக திரும்பின, 2 கடினமானவை $48.57 செலவாயின,
மேலும் மதிப்பிடுவதற்குப் போதுமான செயல்பாடு இல்லாத ரன்கள் வெற்றிகளாகக்
கணக்கிடப்படுவதற்குப் பதிலாக கிரேடிலிருந்து விடுபடுகின்றன. ஒவ்வொரு கடினமான
ரன்னும் அதன் trace க்கு இணைக்கிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**சூழல் விண்டோ ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் விண்டோவில் 715K, 83.3% உச்சம், 4 compactions
அனைத்தும் overflow இல் அல்லாமல் proactively fire ஆயின, மேலும் அதற்குப் பின்னால்
உள்ள ஒவ்வொரு டர்னின் பயன்பாடும்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் நடக்கிறது.**
Built-in டிடெக்டர்கள் நிறுவலிலிருந்தே ஆனில் உள்ளன: ஏஜென்ட் அமைதியாகிவிட்டது,
டெலிமெட்ரி ஃபீட் நின்றுவிட்டது, செலவு ஸ்பைக், டோக்கன் burst, பிழைகள் ஏறுகின்றன,
பிழை ஸ்பைக், பட்ஜெட் threshold, threat signature பொருந்தியது, security tool
கண்டுபிடிப்பு, security posture மாறியது. உங்கள் சொந்த விதிகள் அதற்கு மேல்
விருப்பமானவை.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ஆபத்தான காலைப் பிடித்து வைப்பது opt-in, மேலும் ஆஃப் ஆக ஷிப் செய்யப்படுகிறது.**
Recursive deletes, force pushes, sudo, secrets, package installs மற்றும்
outbound calls ஒவ்வொன்றும் நீங்கள் ஆன் செய்யக்கூடிய ஒரு விதியைப் பெறுகிறது.
நீங்கள் அதைச் செய்யும் வரை, ClawMetry கவனிக்கிறது, எதையும் மாற்றாது. ஒன்று
ஆன் செய்யப்பட்டதும், பொருந்தும் கால்கள் இங்கே (அல்லது உங்கள் ஃபோனில்) அப்ரூவ்
அல்லது டெனை காக்கும்.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

மேலும், ரன்டைம் வாரியாக: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## அங்கீகாரம்

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## உரிமம்

MIT · [@vivekchand](https://github.com/vivekchand) ஆல் உருவாக்கப்பட்டது · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
