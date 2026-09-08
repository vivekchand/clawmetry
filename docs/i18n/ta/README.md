<!-- i18n-src:88be2deff5d5 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **30 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & மேலும் 26. உங்கள் முழு ஏஜென்ட் கடற்படைக்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இதில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாகக் கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். கட்டமைப்பு தேவையில்லை: நீங்கள் ஏற்கெனவே வைத்திருக்கும் ஏஜென்ட் ரன்டைம்களைக் கண்டறிந்து, அவற்றை படிப்பதற்கு மட்டுமே அணுகி, அவை இயங்கும் விதத்தில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

**ஓபன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**கட்டண திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமும் ஒரே டாஷ்போர்டைப் பெறுகிறது. பலவற்றை ஒரே நேரத்தில் இயக்கினால், தலைப்பு சுவிட்சர் ஒவ்வொரு டேபையும் அவற்றில் ஒன்றுக்கு மறு-நோக்கமாக்குகிறது.

SDK-யில் உங்கள் சொந்த ஏஜென்டை உருவாக்கினீர்களா? இன்டர்செப்டர் அதன் LLM அழைப்புகளையும் கண்காணிக்கிறது. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) பார்க்கவும்.

## நீங்கள் என்ன பெறுவீர்கள்

- **அமர்வுகள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, ஒவ்வொரு டர்னாக, ரீப்ளேயுடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், அமர்வு மற்றும் நாள் வாரியாக, ஏனோமலி கொடிகளுடன்
- **ஃப்ளோ**: சேனல்கள், மாடல்கள் மற்றும் டூல்கள் வழியாக நகரும் செய்திகளின் நேரடி வரைபடம்
- **பிரெயின்**: நிகழும் அப்போதே தர்க்கம் மற்றும் டூல்-அழைப்பு நிகழ்வு ஸ்ட்ரீம்
- **சூழல் அதிகச்செலவு**: வழங்குநர் வாரியாக அளவிடப்பட்ட விண்டோ பயன்பாடு, காம்பாக்ஷன் vs கட்டாய ஓவர்ஃப்ளோ, மேலும் நாம் *பார்க்க முடியாதவற்றின்* ரன்டைம்-வாரி வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **நினைவகம் & திறன்கள்**: ஒவ்வொரு ரன்டைமும் உண்மையில் ஏற்றிய கோப்புகள் மற்றும் திறன்கள்
- **ஆரோக்கியம் & பதிவுகள்**: வட்டு, நினைவகம், பிழை விகிதங்கள், விகித வரம்புகள், நேரடி பதிவு ஸ்ட்ரீம்
- **எச்சரிக்கைகள்**: பட்ஜெட் வரம்புகள், பிழை உயர்வுகள், ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, Email-க்கு அனுப்பப்படும்
- **அனுமதிகள்**: அபாயகரமான டூல் அழைப்புகளை அவை இயங்குவதற்கு *முன்* இடைநிறுத்தி, உங்கள் ஃபோனிலிருந்தே அனுமதிக்கவும் ([எப்படி](docs/APPROVALS.md))

## சூழல் அதிகச்செலவு, மற்றும் கண்காணிப்பதன் விலை

எந்த ஏஜென்ட்-ஒப்பீட்டு கருவியையும் நம்புவதற்கு முன் பதில் தெரிந்திருக்க வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்கள் முழுவதும் சூழல்-விண்டோ அதிகச்செலவை இது எப்படி கையாள்கிறது?**

ஒரு பயன்பாட்டு சதவீதம் அது எதை வகுக்கிறதோ அதனளவுக்கே நேர்மையானது. ClawMetry நீங்கள் படித்து PR செய்யக்கூடிய [ஒரு அட்டவணையிலிருந்து](clawmetry/context_windows.py) வழங்குநர் வாரியாக விண்டோவை அளவிடுகிறது, இது Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM ஐ உள்ளடக்குகிறது. இது 30 ரன்டைம்களையும் ஒரே வழங்குநரின் அளவுகோலால் அளவிடுவதில்லை. இது முக்கியமானது: Anthropic-இன் 200K-க்கு எதிராக மதிப்பிடப்படும் 300K GPT-5 டர்ன் ">100%, தகர்ந்தது" எனக் காட்டுகிறது, அது உண்மையில் GPT-5-இன் 400K-இல் 75%-ஆக இருக்கும்போது. அதே அளவுகோல் உண்மையில் அதிகச்செலவான 130K DeepSeek டர்னை வசதியான 65%-ஆக மறைக்கிறது.

ஒவ்வொரு விண்டோவும் அதன் தோற்றத்துடன் வருகிறது: `model_table`, `explicit_marker`, `observed_floor`, அல்லது மாடல் தெரியாதபோது நேர்மையான `default`. யூகத்தின் அடிப்படையில் கட்டப்பட்ட ஒரு கேஜ், தேடலின் அடிப்படையில் கட்டப்பட்டதைப் போன்ற அதிகாரத்துடன் ஒருபோதும் காட்சியளிக்காது.

சில ரன்டைம்களில் மட்டுமே ClawMetry-ஆல் காம்பாக்ஷன் நிகழ்வுகளைப் பார்க்க முடியும். எனவே `GET /api/context-coverage`, ஒவ்வொரு ரன்டைமிற்கும், **பூஜ்ஜியம் என்றால் "சுத்தமாக இயங்கியது" என்றா அல்லது "நமக்குத் தெரியவில்லை" என்றா** என்பதை அறிக்கை செய்கிறது. உண்மையில் தெரியாது என்று பொருள்படும் `0` அப்படியே கூறுகிறது.
[முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**கருவியமைப்பு (instrumentation) எவ்வளவு செலவாகும்?**

| பாதை | உங்கள் ஏஜென்டுக்கு சேர்க்கப்படுவது | இயல்புநிலையா? |
|---|---|---|
| அமர்வு-கோப்பு டெயிலிங் (30 ரன்டைம்களும்) | **0**. தனி செயல்முறை, உங்கள் ஏஜென்டில் ClawMetry கோட் இல்லை | ஆம் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒரு LLM அழைப்புக்கு **+0.44 ms**, அதாவது 5s அழைப்பில் 0.009% | இல்லை |
| முன்-டூல் ஹூக் கேட் (warm cache) | 36 ms இன்டர்ப்ரெட்டர் தளத்திற்கு மேல், ஒரு கேட் செய்யப்பட்ட டூல் அழைப்புக்கு **+44 ms** | இல்லை |
| அமலாக்க ப்ராக்ஸி | ஒரு LLM அழைப்புக்கு **+9.7 ms** | இல்லை |

டீமன் ஹோஸ்ட் செலவு: **2,762 நிகழ்வுகள்/வினாடி** உள்வாங்கல், நிகழ்வுக்கு வட்டில் **710 பைட்டுகள்** (100k நிகழ்வுகளுக்கு 67.7 MB), மற்றும் பரபரப்பான நிறுவலில் நிலையான **~12% ஒரு கோர்**. அந்த கடைசி எண் நமது சொந்த கூறப்பட்ட 5-10% பட்ஜெட்டை மீறுகிறது, எனவே அதை பக்கத்திலிருந்து விட்டுவிடாமல் துரத்தப்பட வேண்டிய பிழையாக வெளியிடப்படுகிறது.

Apple M2 Pro-இல் `benchmarks/overhead.py` மூலம் அளவிடப்பட்டது. ஹார்னஸ் ஒவ்வொரு நிலையையும் தனி செயல்முறையில் இயக்கி, அவற்றின் வரிசையை மாற்றி, **சுற்றுகள் அதன் அடையாளத்தில் உடன்படாதபோது எண்ணை அச்சிட மறுக்கிறது**. உங்கள் சொந்த கணினியில் ஒரு நிமிடத்தில் இதை இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ஹூக் கேட்கள் மற்றும் அமலாக்க ப்ராக்ஸி உட்பட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது, மேலும் ஹார்னஸ் CI-இல் Linux, macOS மற்றும் Windows-இல் இயங்குகிறது. தெரிந்திருக்க வேண்டிய இரண்டு முடிவுகள்: Linux-ஐ விட Windows-இல் ப்ராக்ஸி சுமார் ஏழு மடங்கு அதிகமாக செலவாகிறது, மேலும் டீமன் தற்போது ஒரு கோரின் சுமார் 12%-ஐ நிலைநிறுத்துகிறது, இது நமது சொந்த 5-10% பட்ஜெட்டை மீறுகிறது. மூல JSON, முறை, மற்றும் இன்னும் அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md)-இல் உள்ளன.

## விலை நிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்கியது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose, முழு டாஷ்போர்டு, லோக்கல் மட்டும் | $0 |
| **ஸ்டார்ட்டர்** | மேலே உள்ள மற்ற ஒவ்வொரு ரன்டைமும், ஃப்ளீட் வியூ, க்ளவுட் சின்க் | ஒரு நோடுக்கு மாதம் $9 |
| **Pro** | ஸ்டார்ட்டர் + கட்டுப்பாடு மற்றும் மதிப்பீடு: அனுமதிகள், டூல்-ரிஸ்க் கொள்கைகள், மதிப்பீடுகள், ஏனோமலி கண்டறிதல், செலவு உகப்பாக்கி, OTel எக்ஸ்போர்ட், டேம்பர்-எவிடென்ட் ஆடிட் லாக் | ஒரு நோடுக்கு மாதம் $19 |

வருடாந்திர திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)**-இல் உள்ளன. சுய-ஹோஸ்ட் செய்யப்பட்ட உரிம விசைகள் க்ளவுட் இல்லாமலேயே வேலை செய்கின்றன (`clawmetry license`). சரியான இலவச/கட்டண பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-இல் உள்ளது.

## உங்கள் தரவு உங்கள் கணினியில் மட்டுமே இருக்கும்

ClawMetry உள்ளூர் அமர்வு கோப்புகள் மற்றும் பதிவுகளைப் படிக்கிறது. **நீங்கள் `clawmetry connect` இயக்காத வரை எந்த அமர்வு தரவும் உங்கள் கணினியிலிருந்து வெளியேறாது** — ப்ராம்ப்ட்கள், பதில்கள், டூல் ஆர்குமென்ட்கள், கோப்பு உள்ளடக்கங்கள் அல்லது பதிவு வரிகள் எதுவும் இல்லை. நீங்கள் இணைக்கும்போது, ஸ்னாப்ஷாட் உங்கள் கணினியை விட்டு ஒருபோதும் வெளியேறாத ஒரு விசையுடன் எண்ட்-டு-எண்ட் என்க்ரிப்ட் செய்யப்பட்டு, உங்கள் பிரவுசரில் டிக்ரிப்ட் செய்யப்படுகிறது. ஒரு நோடில் விசை இல்லையென்றால், அப்லோட் தெளிவாக அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படுகிறது, மேலும் எந்த சர்வர் பதிலும் அதை மாற்ற முடியாது.

நீங்கள் இணைப்பதற்கு முன் இயல்பாக இயங்கும் இரண்டு விஷயங்கள் உள்ளன, இரண்டும் ஆப்ட்-அவுட் செய்யக்கூடியவை மற்றும் இரண்டுமே அமர்வு தரவை சுமக்காதவை: ஒரு அநாமதேய நிறுவல் பிங் மற்றும் PyPI-க்கு எதிரான ஒரு பதிப்பு சரிபார்ப்பு. இயல்புநிலை நிறுவலும் தொடக்க பேனர் வரிக்காக உங்கள் பொது IP-ஐ ஒருமுறை தேடுகிறது. ஒவ்வொரு இலக்கிடமும், அது என்ன சுமக்கிறது, மற்றும் அதை எப்படி அணைப்பது என்பதும் [docs/EGRESS.md](docs/EGRESS.md)-இல் பட்டியலிடப்பட்டுள்ளது; சுய-ஹோஸ்ட், மறு-இலக்கிடப்பட்ட மற்றும் காற்று-துண்டிக்கப்பட்ட நிறுவல்கள் விருப்பப்படி வெளிச்செல்லும் அழைப்புகள் எதையும் செய்யாது.

டிக்ரிப்ஷன் உங்கள் பிரவுசரில், நாங்கள் உங்களுக்கு வழங்கும் கோடில் நடக்கிறது. இது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது நீங்கள் சரிபார்க்கக்கூடிய ஒன்று. உங்கள் விசையைத் தொடும் ஒவ்வொரு வரியும் ஒரே படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது வீலுக்குள் அனுப்பப்பட்டு அப்படியே வழங்கப்பட்டு, ஒரு Subresource Integrity ஹாஷுடன் பின் செய்யப்பட்டுள்ளது. பிரவுசர் நாங்கள் வெளியிட்டதையே இயக்குகிறது என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

அது என்ன நிரூபிக்காது: கோப்பை ஏற்றும் பக்கத்தை நாங்களே வழங்குகிறோம், எனவே நாங்கள் வேறு பக்கத்தை வழங்கியிருக்கலாம். இன்டெக்ரிட்டி ஹாஷ்கள் ஒரு சமரசம் செய்யப்பட்ட CDN-இலிருந்து உங்களைப் பாதுகாக்கின்றன, விற்பனையாளரிடமிருந்து அல்ல. நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றீடும் வேண்டுமென்றே, பக்க மூலத்தில் தெரியும் வகையில், யாரும் PyPI-இலிருந்து பெறக்கூடிய ஒரு கலைப்பொருளிலிருந்து வேறுபட்டதாக இருக்க வேண்டும் என்பதே. சுய-ஹோஸ்டிங் அல்லது உள்ளூர்-மட்டும் இருப்பது இந்த சார்பை முற்றிலும் நீக்குகிறது.

## நிறுவுதல்

```bash
pip install clawmetry     # பிறகு: clawmetry
```

அல்லது ஒரே-வரி: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows-இல் Python 3.8+ தேவை, அதே கணினியில் குறைந்தது ஒரு ஏஜென்ட் ரன்டைம் இருக்க வேண்டும். Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

அல்லது ஏஜென்டே இதை உங்களுக்கு அமைக்கட்டும். [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) திறன், Claude Code, Codex, Cursor, Gemini CLI, Copilot அல்லது OpenCode-க்கு ClawMetry-ஐ நிறுவவும், கணினியில் உள்ள ஏஜென்ட்கள் என்ன செய்கின்றன மற்றும் செலவழிக்கின்றன என்பதை அறிக்கை செய்யவும், கோரிக்கையின் பேரில் ஒரு அமர்வை நிறுத்தவும், மற்றும் அபாயகரமான டூல் அழைப்புகளை அனுமதிக்காக நிறுத்தவும் கற்பிக்கிறது:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ஆவணங்கள்

| | |
|---|---|
| [ரன்டைம் இணக்கத்தன்மை](docs/compatibility.md) | ஒவ்வொரு அடாப்டரும் என்ன படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [சூழல் அதிகச்செலவு](docs/CONTEXT_BLOWOUT.md) | வழங்குநர்-வாரி விண்டோக்கள், காம்பாக்ஷன் vs ஓவர்ஃப்ளோ, ரன்டைம்-வாரி கவரேஜ் |
| [ஓவர்ஹெட்](docs/OVERHEAD.md) | கருவியமைப்பின் விலை, அளவிடப்பட்டது, அதை மறுஉருவாக்கம் செய்ய ஹார்னஸுடன் |
| [தகுதிகள்](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், டையர் மேட்ரிக்ஸ், உரிம CLI |
| [அனுமதிகள் & கொள்கைகள்](docs/APPROVALS.md) | இயங்குவதற்கு முந்தைய கேட்டிங், ரிஸ்க் ஸ்கோரிங், ஃபோன் அனுமதிகள் |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | டிரேஸ்களை எங்கு வேண்டுமானாலும் எக்ஸ்போர்ட் செய்யவும், எதிலிருந்தும் OTLP-ஐ உள்வாங்கவும் |
| [உங்கள் சொந்த ஏஜென்டைக் கொண்டு வாருங்கள்](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain முதலிலிருந்து இறுதி வரை, இயக்கக்கூடிய உதாரணங்களுடன் |
| [SDK கண்காணிப்பு](docs/SDK_TRACKING.md) | நீங்களே உருவாக்கிய ஏஜென்ட்களுக்கான செலவு அட்ரிபியூஷன் |
| [சாட் சேனல்கள்](docs/CHANNELS.md) | ஃப்ளோவில் காட்டப்படும் சாட் அடாப்டர்கள் |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | சாண்ட்பாக்ஸ் செய்யப்பட்ட NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | இமேஜ், காம்போஸ், வால்யூம் மவுன்ட்கள் |
| [கட்டமைப்பு](ARCHITECTURE.md) · [டெவலப்மென்ட்](docs/DEVELOPMENT.md) | இது உள்ளே எப்படி வேலை செய்கிறது; மூலத்திலிருந்து இயக்குதல் |
| [டெலிமெட்ரி](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் டெஸ்க்டாப்-ஓபன் பிங்குகள், மற்றும் அவற்றை எப்படி அணைப்பது |

## ஸ்க்ரீன்ஷாட்கள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான கணினியிலிருந்து, படிப்பதற்கு மட்டும் அணுகி, எதுவும் விதைக்காமல் பெறப்பட்டது.

**ஏதோ தவறாக இருக்கும்போது அது உங்களுக்குச் சொல்கிறது, என்ன நடந்தது என்பதை மட்டும் அல்ல.**
மேலே இரண்டு ஏனோமலி பேனர்கள்: தினசரி சராசரியை விட 7 மடங்கு அதிகமாக செலவு இயங்குகிறது, மற்றும் 4.2 மடங்கு செலவு உயர்வு. அவற்றுக்குக் கீழே, சமீபத்திய 667 அமர்வுகளில் 324, காரணம் வாரியாகப் பட்டியலிடப்பட்ட வீணடிப்பு சிக்னலைக் கொண்டுள்ளன.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கு சென்றது என்பதை, ஒவ்வொரு காலக்கட்டத்திலும் இது உங்களுக்குக் காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றுக்கும் பின்னால் உள்ள டோக்கன்களுடனும் உங்கள் சந்தா ஏற்கெனவே எவ்வளவு உள்ளடக்குகிறது என்பதுடனும். அதற்குக் கீழே, சுமார் $1,128/மாதம் மீட்டெடுக்கக்கூடியதாக பட்டியலிடப்பட்டு, மேலும் கேஷ் மறுபயன்பாட்டால் ஏற்கெனவே $17,256/மாதம் சேமிக்கப்பட்டுள்ளது.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு செய்தி எப்படி பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
நேரடி ஃப்ளோ வரைபடம்: நீங்கள், அது வந்த சேனல், கேட்வே, தற்போது பதிலளிக்கும் மாடல், மற்றும் அது அணுகிய ஒவ்வொரு டூலும். வேலை அவற்றின் வழியாக நகரும்போது நோட்கள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**கணினியில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே அட்டவணையில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் ஆயுட்காலம் முழுவதும் அது எவ்வளவு செலவாகிறது, அது கடைசியாக எப்போது காணப்பட்டது, யாருக்குச் சொந்தமானது, மற்றும் ஒரு சந்தா பில்லை உள்ளடக்குகிறதா. இங்கே 14 ஏஜென்ட்கள், 3 அமர்வுகள் வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கு சென்றது என்பதை, டூல் வாரியாக இது காட்டுகிறது.**
ஒரு உண்மையான அமர்வின் ஒரு டர்ன்: 11.2 நிமிடங்களில் 11 டூல்கள், $1.16-க்கு. ஒவ்வொரு Bash அழைப்பும் மாடல் அழைப்பும் காலவரிசையில் அதன் சொந்த பட்டியைப் பெறுகிறது, எனவே 4.1 நிமிடங்கள் இயங்கிய கட்டளையும் 226ms இயங்கிய கட்டளையும் ஒரே பார்வையில் வேறுபடுத்தப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பிடுகிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக முடிந்தன, 2 கடினமானவை $48.57 செலவாயின, மற்றும் மதிப்பிடுவதற்குப் போதுமான செயல்பாடு இல்லாத ரன்கள் வெற்றிகளாக எண்ணப்படுவதற்குப் பதிலாக மதிப்பீட்டிலிருந்து விடுபடுகின்றன. ஒவ்வொரு கடினமான ரன்னும் அதன் டிரேசுடன் இணைக்கப்படுகிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**சூழல் விண்டோ ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் விண்டோவில் 715K, 83.3% உச்சம், அனைத்தும் ஓவர்ஃப்ளோவில் அல்லாமல் முன்கூட்டியே தொடங்கிய 4 காம்பாக்ஷன்கள், மற்றும் அதற்குப் பின்னால் உள்ள ஒவ்வொரு டர்னின் பயன்பாடும்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
நிறுவலிலிருந்தே இயல்பான டிடெக்டர்கள் இயங்குகின்றன: ஏஜென்ட் அமைதியாகிவிட்டது, டெலிமெட்ரி ஃபீட் நின்றுவிட்டது, செலவு உயர்வு, டோக்கன் வெடிப்பு, ஏறும் பிழைகள், பிழை உயர்வு, பட்ஜெட் வரம்பு, அச்சுறுத்தல் கையொப்பம் பொருந்தியது, செக்யூரிட்டி டூல் கண்டுபிடிப்பு, செக்யூரிட்டி நிலைமை மாற்றம். உங்கள் சொந்த விதிகள் இதற்கு மேல் விருப்பமானவை.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**அபாயகரமான அழைப்பை நிறுத்துவது ஆப்ட்-இன், மற்றும் அணைந்த நிலையில் வெளியிடப்படுகிறது.**
ரிகர்சிவ் டிலீட்கள், ஃபோர்ஸ் புஷ்கள், sudo, இரகசியங்கள், பேக்கேஜ் நிறுவல்கள் மற்றும் வெளிச்செல்லும் அழைப்புகள் ஒவ்வொன்றும் நீங்கள் இயக்கக்கூடிய ஒரு விதியைப் பெறுகின்றன. நீங்கள் அதைச் செய்யும் வரை, ClawMetry கவனிக்கிறது, எதையும் மாற்றாது. ஒன்று இயக்கப்பட்டதும், பொருந்தும் அழைப்புகள் இங்கே (அல்லது உங்கள் ஃபோனில்) ஒரு அனுமதி அல்லது மறுப்புக்காக காத்திருக்கும்.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

மேலும், ரன்டைம் வாரியாக: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## நட்சத்திர வரலாறு

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## உரிமம்

MIT · உருவாக்கியவர் [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
