<!-- i18n-src:d21bea5161e0 -->
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

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **30 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 26. உங்கள் முழு ஏஜென்ட் கடற்படைக்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை படிக்க:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. அமைப்பு தேவையில்லை. அனைத்தையும் தானாகக் கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். அமைப்பு தேவையில்லை: நீங்கள் ஏற்கனவே வைத்திருக்கும் ஏஜென்ட் ரன்டைம்களை இது கண்டறிந்து, அவற்றை படிக்க மட்டும் அணுகும், அவை எவ்வாறு இயங்குகின்றன என்பதில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

**ஓப்பன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**கட்டண திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமும் அதே டாஷ்போர்டைப் பெறுகிறது. பலவற்றை ஒரே நேரத்தில் இயக்கினால், தலைப்பு சுவிட்சர் ஒவ்வொரு தாவலையும் அவற்றில் ஒன்றுக்கு மறு-நோக்கம் செய்யும்.

SDK மூலம் உங்கள் சொந்த ஏஜென்டை உருவாக்கினீர்களா? இன்டர்செப்டர் அதன் LLM அழைப்புகளையும் கண்காணிக்கும். [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ஐப் பார்க்கவும்.

## நீங்கள் என்ன பெறுகிறீர்கள்

- **அமர்வுகள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, ஒவ்வொரு டர்னிலும், replay உடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், அமர்வு மற்றும் நாள் அடிப்படையில், அசாதாரண குறியீடுகளுடன்
- **ஃப்ளோ**: சேனல்கள், மாடல்கள் மற்றும் கருவிகள் வழியாக நகரும் செய்திகளின் நேரடி வரைபடம்
- **மூளை**: நடக்கும்போதே பகுத்தறிவு மற்றும் கருவி-அழைப்பு நிகழ்வு ஸ்ட்ரீம்
- **சூழல் வெடிப்பு (Context blowout)**: வழங்குனர் வாரியாக அளவிடப்பட்ட விண்டோ பயன்பாடு, compaction எதிராக கட்டாய overflow, மேலும் நாம் *பார்க்க முடியாதவற்றின்* ரன்டைம் வாரியான வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **நினைவகம் & திறன்கள்**: ஒவ்வொரு ரன்டைமும் உண்மையில் ஏற்றிய கோப்புகள் மற்றும் திறன்கள்
- **ஆரோக்கியம் & லாக்குகள்**: டிஸ்க், நினைவகம், பிழை விகிதங்கள், rate limits, நேரடி லாக் ஸ்ட்ரீம்
- **எச்சரிக்கைகள்**: பட்ஜெட் வரம்புகள், பிழை எழுச்சிகள், ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, மின்னஞ்சலுக்கு வழிமாற்றப்படும்
- **அனுமதிகள்**: அபாயகரமான கருவி அழைப்புகளை அவை இயங்கு*முன்* இடைநிறுத்தி, உங்கள் மொபைலிலிருந்து அனுமதிக்கவும் ([எப்படி](docs/APPROVALS.md))

## சூழல் வெடிப்பு, மற்றும் கண்காணிப்பதற்கான செலவு

எந்த ஏஜென்ட்-ஒப்பீட்டு கருவியையும் நம்புவதற்கு முன் பதில் அளிக்க வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்கள் முழுவதும் சூழல்-விண்டோ வெடிப்பை இது எப்படி கையாளுகிறது?**

பயன்பாட்டு சதவீதம் அது எதை வகுக்கிறதோ அதைப் பொறுத்தே நேர்மையானதாக இருக்கும். ClawMetry, [நீங்கள் படித்து PR செய்யக்கூடிய அட்டவணையிலிருந்து](clawmetry/context_windows.py) வழங்குனர் வாரியாக விண்டோவை அளவிடுகிறது, Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM ஆகியவற்றை உள்ளடக்கியது. இது 26 ரன்டைம்களையும் ஒரே வழங்குனரின் அளவுகோலால் அளவிடாது. இது முக்கியம்: Anthropic இன் 200K க்கு எதிராக மதிப்பிடப்படும் 300K GPT-5 டர்ன், GPT-5 இன் 400K இல் அது உண்மையில் 75% ஆக இருக்கும்போது ">100%, blown" எனக் காட்டும். அதே அளவுகோல் உண்மையில் overflow ஆன 130K DeepSeek டர்னை வசதியான 65% ஆக மறைக்கும்.

ஒவ்வொரு விண்டோவும் அதன் மூலத்துடன் வருகிறது: `model_table`, `explicit_marker`, `observed_floor`, அல்லது மாடல் தெரியாதபோது நேர்மையான `default`. ஒரு யூகத்தின் அடிப்படையில் கட்டப்பட்ட கேஜ், lookup ஒன்றின் அடிப்படையில் கட்டப்பட்டதைப் போன்ற அதே அதிகாரத்துடன் ஒருபோதும் காட்டப்படாது.

சில ரன்டைம்களில் மட்டுமே ClawMetry யால் compaction நிகழ்வுகளைப் பார்க்க முடியும். எனவே `GET /api/context-coverage`, ஒவ்வொரு ரன்டைம் வாரியாகவும், ஒரு **பூஜ்ஜியம் "சுத்தமாக ஓடியது" என்று அர்த்தமா அல்லது "நமக்குத் தெரியவில்லை" என்று அர்த்தமா** என்பதைப் புகார் செய்கிறது. உண்மையில் குருடாக இருப்பதைக் குறிக்கும் `0`, அதைத் தெளிவாகச் சொல்கிறது. [முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**கருவிமயமாக்கல் (instrumentation) என்ன செலவாகும்?**

| பாதை | உங்கள் ஏஜென்டுடன் சேர்க்கப்படுவது | இயல்புநிலையா? |
|---|---|---|
| அமர்வு-கோப்பு tailing (அனைத்து 30 ரன்டைம்களும்) | **0**. தனி செயல்முறை, உங்கள் ஏஜென்டில் ClawMetry கோட் இல்லை | ஆம் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒரு LLM அழைப்புக்கு **+0.44 ms**, அதாவது 5s அழைப்பில் 0.009% | இல்லை |
| Pre-tool hook gate (warm cache) | 36 ms interpreter floor க்கு மேல், gate செய்யப்பட்ட ஒவ்வொரு கருவி அழைப்புக்கும் **+44 ms** | இல்லை |
| Enforcement proxy | ஒரு LLM அழைப்புக்கு **+9.7 ms** | இல்லை |

டீமன் ஹோஸ்ட் செலவு: **2,762 நிகழ்வுகள்/வினாடி** ingest, டிஸ்கில் **710 bytes/நிகழ்வு** (100k நிகழ்வுகளுக்கு 67.7 MB), மற்றும் பரபரப்பான install ஒன்றில் நிலையான **~12% of one core**. அந்த கடைசி எண், நமது சொந்த 5-10% பட்ஜெட்டை மீறுகிறது, எனவே பக்கத்தில் விடுவதற்குப் பதிலாக, துரத்த வேண்டிய பிழையாக வெளியிடப்படுகிறது.

Apple M2 Pro இல் `benchmarks/overhead.py` மூலம் அளவிடப்பட்டது. ஹார்னஸ் ஒவ்வொரு நிலையையும் தனி செயல்முறையில் இயக்குகிறது, அவற்றின் வரிசையை மாற்றி மாற்றி இயக்குகிறது, மேலும் **சுற்றுகள் அதன் அடையாளத்தில் உடன்படாதபோது எண்ணைப் அச்சிட மறுக்கிறது**. இதை உங்கள் சொந்த மெஷினில் ஒரு நிமிடத்தில் இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook gates மற்றும் enforcement proxy உட்பட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது, மேலும் ஹார்னஸ் CI இல் Linux, macOS மற்றும் Windows இல் இயங்குகிறது. தெரிந்துகொள்ள வேண்டிய இரண்டு முடிவுகள்: Linux ஐ விட Windows இல் proxy சுமார் ஏழு மடங்கு அதிகமாக செலவாகிறது, மேலும் டீமன் தற்போது ஒரு core இன் சுமார் 12% ஐ நிலையாகப் பயன்படுத்துகிறது, நமது சொந்த 5-10% பட்ஜெட்டை மீறி. மூலத் தரவு (raw JSON), முறை, மற்றும் இன்னும் அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md) இல் உள்ளன.

## விலை நிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose, முழு டாஷ்போர்டு, லோக்கல் மட்டும் | $0 |
| **Starter** | மேலே உள்ள மற்ற அனைத்து ரன்டைம்களும், fleet பார்வை, cloud sync | node ஒன்றுக்கு / மாதம் $9 |
| **Pro** | Starter + கட்டுப்பாடு மற்றும் மதிப்பீடு: அனுமதிகள், tool-risk கொள்கைகள், evals, அசாதாரண கண்டறிதல், செலவு optimizer, OTel export, tamper-evident audit log | node ஒன்றுக்கு / மாதம் $19 |

ஆண்டு திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)** இல் உள்ளன. சுய-ஹோஸ்ட் செய்யப்பட்ட உரிமக் (license) விசைகள் cloud இல்லாமல் வேலை செய்யும் (`clawmetry license`). சரியான இலவச/கட்டண பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) இல் உள்ளது.

## உங்கள் தரவு உங்கள் மெஷினிலேயே இருக்கும்

ClawMetry லோக்கல் அமர்வு கோப்புகள் மற்றும் லாக்குகளை படிக்கிறது. **நீங்கள் `clawmetry connect` இயக்காத வரை உங்கள் பெட்டியிலிருந்து எந்த அமர்வு தரவும் வெளியேறாது** — prompts, replies, tool arguments, file contents அல்லது log lines எதுவும் இல்லை. நீங்கள் connect செய்யும்போது, snapshot உங்கள் மெஷினை விட்டு ஒருபோதும் வெளியேறாத ஒரு விசையுடன் end-to-end encrypt செய்யப்பட்டு, உங்கள் browser இல் decrypt செய்யப்படுகிறது. ஒரு node இல் விசை இல்லையென்றால், upload வெளிப்படையாக அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படுகிறது, மேலும் எந்த சேவையக பதிலும் அதை மாற்ற முடியாது.

நீங்கள் connect செய்வதற்கு முன், இரண்டு விஷயங்கள் இயல்புநிலையில் இயங்கும், இரண்டும் opt-out ஆகவும், எதுவும் அமர்வு தரவைக் கொண்டு செல்லாமலும்: ஒரு அநாமதேய install ping மற்றும் PyPI க்கு எதிராக version check. ஒரு இயல்பு நிறுவல் startup banner வரிக்காக உங்கள் பொது IP ஐ ஒருமுறை lookup செய்யும். ஒவ்வொரு destination, அது என்ன கொண்டு செல்கிறது, மேலும் அதை எப்படி அணைப்பது என்பது [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது; சுய-ஹோஸ்ட், மறு-நோக்கப்பட்ட (repointed) மற்றும் air-gapped நிறுவல்கள் எந்த discretionary outbound அழைப்புகளையும் செய்யாது.

Decryption உங்கள் browser இல், நாங்கள் உங்களுக்கு வழங்கும் கோட்டில் நடக்கிறது. அது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள் சரிபார்க்கக்கூடிய ஒன்று. உங்கள் விசையைத் தொடும் ஒவ்வொரு வரியும் ஒரே படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது wheel உள்ளே அனுப்பப்பட்டு, verbatim ஆக serve செய்யப்பட்டு, Subresource Integrity hash உடன் pin செய்யப்பட்டுள்ளது. browser நாங்கள் வெளியிட்டதையே இயக்குகிறதா என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

இது என்ன நிரூபிக்கவில்லை: இந்த கோப்பை ஏற்றும் பக்கத்தை நாங்கள்தான் serve செய்கிறோம், எனவே நாங்கள் வேறு பக்கத்தையும் serve செய்யலாம். Integrity hashes உங்களை ஒரு சமரசம் செய்யப்பட்ட CDN இலிருந்து பாதுகாக்கும், விற்பனையாளரிடமிருந்து அல்ல. நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றீடும் வேண்டுமென்றே செய்யப்பட வேண்டும், page source இல் தெரியும், மேலும் யாரும் fetch செய்யக்கூடிய PyPI artifact இலிருந்து வேறுபட்டதாக இருக்க வேண்டும். Self-hosting அல்லது local-only ஆக இருப்பது இந்த சார்பை முழுவதுமாக நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பின்னர்: clawmetry
```

அல்லது ஒரு-வரி கட்டளை: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows இல் Python 3.8+ தேவை, மேலும் அதே மெஷினில் குறைந்தது ஒரு ஏஜென்ட் ரன்டைம் இருக்க வேண்டும். Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

## ஆவணங்கள்

| | |
|---|---|
| [ரன்டைம் இணக்கத்தன்மை](docs/compatibility.md) | ஒவ்வொரு அடாப்டரும் எதைப் படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [சூழல் வெடிப்பு](docs/CONTEXT_BLOWOUT.md) | வழங்குனர் வாரியான விண்டோக்கள், compaction எதிராக overflow, ரன்டைம் வாரியான coverage |
| [Overhead](docs/OVERHEAD.md) | கருவிமயமாக்கல் என்ன செலவாகும், அளவிடப்பட்டது, அதை மறுஉருவாக்கம் செய்யும் ஹார்னஸுடன் |
| [உரிமங்கள் (Entitlements)](docs/ENTITLEMENTS.md) | இலவசம் எதிராக கட்டணம், tier matrix, license CLI |
| [அனுமதிகள் & கொள்கைகள்](docs/APPROVALS.md) | Pre-execution gating, risk scoring, மொபைல் அனுமதிகள் |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | traces களை எங்கு வேண்டுமானாலும் export செய்யுங்கள், எதிலிருந்தும் OTLP ingest செய்யுங்கள் |
| [SDK கண்காணிப்பு](docs/SDK_TRACKING.md) | நீங்களே உருவாக்கிய ஏஜென்ட்களுக்கான செலவு பகிர்வு |
| [சாட் சேனல்கள்](docs/CHANNELS.md) | Flow இல் காட்டப்படும் chat adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [கட்டமைப்பு (Architecture)](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | இது உள்ளே எப்படி வேலை செய்கிறது; மூலத்திலிருந்து இயக்குதல் |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் desktop-open pings, மற்றும் அவற்றை எப்படி அணைப்பது |

## திரைக்காட்சிகள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான மெஷினிலிருந்து, படிக்க-மட்டும், எதுவும் seed செய்யப்படாமல்.

**எதுவோ தவறாக இருக்கும்போது இது உங்களுக்குச் சொல்கிறது, என்ன நடந்தது என்பதை மட்டும் அல்ல.**
மேலே இரண்டு அசாதாரண பேனர்கள்: தினசரி சராசரியை விட 7 மடங்கு அதிகமான செலவு, மற்றும் 4.2 மடங்கு செலவு எழுச்சி. அவற்றுக்குக் கீழே, சமீபத்திய 667 அமர்வுகளில் 324, ஒரு வீண் சிக்னலைக் கொண்டவை, காரணம் வாரியாக பட்டியலிடப்பட்டுள்ளன.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கு சென்றது என்பதை இது ஒவ்வொரு விண்டோவிலும் காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றும் அதன் பின்னணியில் உள்ள டோக்கன்களுடனும், உங்கள் subscription ஏற்கனவே எவ்வளவு உள்ளடக்குகிறது என்பதுடனும். அதற்குக் கீழே, மாதம் ~$1,128 recoverable எனப் பட்டியலிடப்பட்டு, cache reuse மூலம் ஏற்கனவே மாதம் $17,256 சேமிக்கப்பட்டுள்ளது.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு செய்தி எப்படி பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
நேரடி flow வரைபடம்: நீங்கள், அது வந்த சேனல், gateway, இப்போது பதிலளிக்கும் மாடல், மற்றும் அது அணுகிய ஒவ்வொரு கருவியும். வேலை அவற்றின் வழியாக நகரும்போது node கள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**மெஷினில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே அட்டவணையில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் வாழ்நாள் முழுவதும் அது என்ன செலவாகிறது, அது கடைசியாக எப்போது காணப்பட்டது, யாருக்குச் சொந்தமானது, மற்றும் ஒரு subscription பில்லை உள்ளடக்குகிறதா. இங்கே 14 ஏஜென்ட்கள், 3 அமர்வுகள் வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கு சென்றது என்பதை, கருவி வாரியாக இது காட்டுகிறது.**
ஒரு உண்மையான அமர்வின் ஒரு டர்ன்: 11.2 நிமிடங்களில் 11 கருவிகள், $1.16 க்கு. ஒவ்வொரு Bash அழைப்புக்கும் மாடல் அழைப்புக்கும் அதன் சொந்த பட்டி timeline இல் உள்ளது, எனவே 4.1 நிமிடங்கள் இயங்கிய கட்டளையையும் 226ms இயங்கிய கட்டளையையும் ஒரே பார்வையில் வேறுபடுத்தி அறியலாம்.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பிடுகிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக முடிந்தன, 2 கடினமானவை $48.57 செலவாகின, மேலும் மதிப்பிட போதுமான செயல்பாடு இல்லாத ரன்கள் வெற்றிகளாக எண்ணப்படாமல் தரப்படிப்பில் இருந்து விடுபடுகின்றன. ஒவ்வொரு கடினமான ரன்னும் அதன் trace உடன் இணைக்கப்பட்டுள்ளது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**சூழல் விண்டோ ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் விண்டோவில் 715K, 83.3% உச்சம், overflow இல் அல்லாமல் proactively மட்டுமே fire ஆன 4 compactions, மேலும் அதற்குப் பின்னால் உள்ள ஒவ்வொரு டர்னின் பயன்பாடும்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
நிறுவலிலிருந்தே built-in detectors இயங்குகின்றன: ஏஜென்ட் அமைதியானது, telemetry feed நின்றது, செலவு எழுச்சி, டோக்கன் burst, பிழைகள் அதிகரிப்பு, பிழை எழுச்சி, பட்ஜெட் வரம்பு, threat signature பொருந்தியது, security tool கண்டுபிடிப்பு, security posture மாற்றம். உங்கள் சொந்த விதிகள் அதற்கு மேல் விருப்பமானவை.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**அபாயகரமான அழைப்பை நிறுத்தி வைப்பது opt-in, மற்றும் அணைந்த நிலையில் ship ஆகிறது.**
Recursive deletes, force pushes, sudo, secrets, package installs மற்றும் outbound calls ஒவ்வொன்றும் நீங்கள் இயக்கக்கூடிய ஒரு விதியைப் பெறுகின்றன. நீங்கள் அதைச் செய்யும் வரை, ClawMetry கவனிக்கிறது, எதையும் மாற்றாது. ஒன்று இயக்கப்பட்டதும், பொருந்தும் அழைப்புகள் இங்கே (அல்லது உங்கள் மொபைலில்) approve அல்லது deny க்காக காத்திருக்கும்.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

மேலும், ரன்டைம் வாரியாக: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

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
