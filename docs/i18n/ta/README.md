<!-- i18n-src:9767c8001c9c -->
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

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **30 AI ஏஜென்ட் ரன்டைம்களுக்கான** நேரடி (ரியல்-டைம்) கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 26. உங்கள் முழு ஏஜென்ட் கடற்படைக்கும் (fleet) ஒரே டாஷ்போர்டு.

> 🌐 **இதை இதில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. உள்ளமைவு (config) தேவையில்லை. அனைத்தையும் தானாகக் கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். உள்ளமைவு தேவையில்லை: உங்களிடம் ஏற்கனவே இருக்கும் ஏஜென்ட் ரன்டைம்களைக் கண்டறிந்து, அவற்றை read-only முறையில் படிக்கும், அவை இயங்கும் விதத்தில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ஏஜென்ட் ரன்டைம்களுடன் இயங்கும்

**ஓபன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**கட்டணச் செலுத்தும் திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமும் ஒரே டாஷ்போர்டைப் பெறுகிறது. ஒரே நேரத்தில் பலவற்றை இயக்கினால், மேலிருக்கும் ஸ்விட்சர் ஒவ்வொரு டேபையும் நீங்கள் தேர்ந்தெடுத்த ஒன்றுக்கு மறு-அளவீடு செய்யும்.

நீங்கள் ஒரு SDK மூலம் உங்கள் சொந்த ஏஜென்டைக் கட்டமைத்தீர்களா? இன்டர்செப்டர் அதன் LLM அழைப்புகளையும் கண்காணிக்கும். [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **அமர்வுகள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, ஒவ்வொரு டர்னாக, ரீப்ளே உடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், அமர்வு மற்றும் நாள் வாரியாக, அசாதாரண (anomaly) குறியீடுகளுடன்
- **ஃப்ளோ**: சேனல்கள், மாடல்கள் மற்றும் டூல்கள் வழியாக செய்திகள் நகரும் நேரடி வரைபடம்
- **பிரெயின்**: நடக்கும் நேரத்திலேயே பகுத்தறிவு மற்றும் டூல்-அழைப்பு நிகழ்வு ஸ்ட்ரீம்
- **சூழல் (context) நிரம்பிவழிதல்**: வழங்குநர் வாரியாக அளவிடப்பட்ட விண்டோ பயன்பாடு, compaction எதிராக கட்டாய overflow, மேலும் நமக்கு *பார்க்க முடியாதவற்றின்* ரன்டைம் வாரியான வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **நினைவகம் & திறன்கள்**: ஒவ்வொரு ரன்டைமும் உண்மையில் ஏற்றிய கோப்புகள் மற்றும் திறன்கள்
- **ஆரோக்கியம் & லாக்குகள்**: வட்டு (disk), நினைவகம், பிழை விகிதங்கள், rate limits, நேரடி லாக் ஸ்ட்ரீம்
- **எச்சரிக்கைகள்**: பட்ஜெட் வரம்புகள், பிழை உயர்வுகள், ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, மின்னஞ்சலுக்கு அனுப்பப்படும்
- **அனுமதிகள் (Approvals)**: ஆபத்தான டூல் அழைப்புகளை அவை இயங்குவதற்கு *முன்* இடைநிறுத்தி, உங்கள் மொபைலிலிருந்தே அனுமதிக்கவும் ([எப்படி](docs/APPROVALS.md))

## சூழல் நிரம்பிவழிதல், மற்றும் கண்காணிப்பதற்கான செலவு

எந்த ஏஜென்ட்-ஒப்பீட்டு கருவியையும் நம்புவதற்கு முன் பதிலளிக்க வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்கள் முழுவதும் சூழல்-விண்டோ நிரம்பிவழிதலை இது எப்படி கையாளுகிறது?**

ஒரு பயன்பாட்டு சதவீதம் அது எதனால் வகுக்கப்படுகிறதோ அதைப் போலவே நேர்மையானதாக இருக்கும். ClawMetry, [நீங்கள் படித்து PR செய்யக்கூடிய ஒரு அட்டவணையில்](clawmetry/context_windows.py) இருந்து வழங்குநர் வாரியாக விண்டோவை அளவிடுகிறது, இது Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM ஐ உள்ளடக்கியது. இது எல்லா 26 ரன்டைம்களையும் ஒரே வழங்குநரின் அளவுகோலால் அளவிடுவதில்லை. இது முக்கியமானது: Anthropic-இன் 200K-க்கு எதிராக மதிப்பிடப்படும் 300K GPT-5 டர்ன், உண்மையில் GPT-5-இன் 400K-இல் 75% ஆக இருக்கும்போது ">100%, blown" எனக் காட்டும். அதே அளவுகோல், உண்மையில் overflow ஆன 130K DeepSeek டர்னை வசதியான 65% ஆக மறைக்கிறது.

ஒவ்வொரு விண்டோவும் அதன் தோற்றத்துடன் (`model_table`, `explicit_marker`, `observed_floor`, அல்லது மாடல் தெரியாதபோது நேர்மையான `default`) அனுப்பப்படுகிறது. ஒரு யூகத்தின் அடிப்படையில் கட்டப்பட்ட ஒரு கேஜ், ஒரு தேடலின் அடிப்படையில் கட்டப்பட்டதைப் போன்ற அதிகாரத்துடன் ஒருபோதும் காட்டப்படாது.

சில ரன்டைம்களில் மட்டுமே ClawMetry-க்கு compaction நிகழ்வுகளைப் பார்க்க முடியும். எனவே `GET /api/context-coverage`, ஒவ்வொரு ரன்டைமிற்கும், **ஒரு பூஜ்ஜியம் "சுத்தமாக ஓடியது" என்பதையா அல்லது "நமக்கு தெரியவில்லை" என்பதையா** குறிக்கிறது என்பதை அறிக்கை செய்கிறது. உண்மையில் தெரியாமல் இருப்பதைக் குறிக்கும் ஒரு `0`, அதையே தெரிவிக்கும். [முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**இன்ஸ்ட்ரூமென்டேஷனின் செலவு என்ன?**

| பாதை | உங்கள் ஏஜென்டுக்குச் சேர்க்கப்படுவது | இயல்புநிலையா? |
|---|---|---|
| அமர்வு-கோப்பு tailing (30 ரன்டைம்கள் அனைத்திலும்) | **0**. தனி செயல்முறை, உங்கள் ஏஜென்டில் ClawMetry கோட் இல்லை | ஆம் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒவ்வொரு LLM அழைப்புக்கும் **+0.44 ms**, அதாவது 5s அழைப்பில் 0.009% | இல்லை |
| Pre-tool hook gate (warm cache) | ஒவ்வொரு gated டூல் அழைப்புக்கும் **+44 ms**, 36 ms இன்டர்ப்ரெட்டர் floor-க்கு மேல் | இல்லை |
| Enforcement proxy | ஒவ்வொரு LLM அழைப்புக்கும் **+9.7 ms** | இல்லை |

டீமன் ஹோஸ்ட் செலவு: **2,762 நிகழ்வுகள்/வினாடி** ingest, வட்டில் **710 பைட்டுகள்/நிகழ்வு** (100,000 நிகழ்வுகளுக்கு 67.7 MB), மற்றும் பரபரப்பான நிறுவலில் தொடர்ந்து **ஒரு கோர்-இன் ~12%**. அந்த கடைசி எண், நமது சொந்த 5-10% பட்ஜெட்டைத் தாண்டியது, எனவே அது பக்கத்தில் இருந்து விடுவதற்குப் பதிலாக துரத்த வேண்டிய பிழையாக வெளியிடப்படுகிறது.

Apple M2 Pro-இல் `benchmarks/overhead.py` மூலம் அளவிடப்பட்டது. இந்த harness ஒவ்வொரு நிலைமையையும் தனித்தனி செயல்முறையில் இயக்கி, அவற்றின் வரிசையை மாற்றி, **சுற்றுகள் அதன் அடையாளத்தில் (sign) ஒத்துப்போகாதபோது எண்ணைப் அச்சிட மறுக்கிறது**. இதை உங்கள் சொந்த கணினியில் ஒரு நிமிடத்தில் இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook gates மற்றும் enforcement proxy உட்பட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது, மேலும் இந்த harness Linux, macOS மற்றும் Windows-இல் CI-இல் இயங்குகிறது. தெரிந்துகொள்ள வேண்டிய இரண்டு முடிவுகள்: Windows-இல் proxy, Linux-ஐ விட சுமார் ஏழு மடங்கு அதிகச் செலவாகிறது, மேலும் டீமன் தற்போது ஒரு கோர்-இன் சுமார் 12%-ஐ தொடர்ந்து பயன்படுத்துகிறது, இது நமது சொந்த 5-10% பட்ஜெட்டைத் தாண்டியது. மூல JSON, முறை, மற்றும் இன்னும் அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md) இல் உள்ளன.

## விலைநிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, முழு டாஷ்போர்டு, local மட்டும் | $0 |
| **Starter** | மேலே உள்ள மற்ற எல்லா ரன்டைம்களும், fleet view, cloud sync | node ஒன்றுக்கு / மாதம் $9 |
| **Pro** | Starter + கட்டுப்பாடு மற்றும் மதிப்பீடு: அனுமதிகள், டூல்-ரிஸ்க் கொள்கைகள், evals, அசாதாரண கண்டறிதல், cost optimizer, OTel export, tamper-evident audit log | node ஒன்றுக்கு / மாதம் $19 |

ஆண்டு திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)** இல் உள்ளன. Self-hosted லைசென்ஸ் கீகள் cloud இல்லாமல் வேலை செய்யும் (`clawmetry license`). துல்லியமான free/paid பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) இல் உள்ளது.

## உங்கள் தரவு உங்கள் கணினியிலேயே இருக்கும்

ClawMetry உள்ளூர் அமர்வு கோப்புகளையும் லாக்குகளையும் படிக்கிறது. **நீங்கள் `clawmetry connect` இயக்காத வரை உங்கள் கணினியிலிருந்து எந்த அமர்வுத் தரவும் வெளியேறாது** — prompts, பதில்கள், டூல் ஆர்குமெண்ட்கள், கோப்பு உள்ளடக்கங்கள் அல்லது லாக் வரிகள் எதுவும் இல்லை. நீங்கள் connect செய்யும்போது, ஸ்னாப்ஷாட் உங்கள் கணினியை விட்டு ஒருபோதும் வெளியேறாத ஒரு கீ மூலம் end-to-end குறியாக்கம் செய்யப்பட்டு, உங்கள் பிரௌசரில் decrypt செய்யப்படுகிறது. ஒரு நோட்-க்கு கீ இல்லையென்றால், அப்லோட் தெளிவாக அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படுகிறது, மேலும் எந்த சர்வர் பதிலும் அதை மாற்ற முடியாது.

நீங்கள் connect செய்வதற்கு முன், இரண்டு விஷயங்கள் இயல்பாகவே இயங்கும், இரண்டும் opt-out செய்யக்கூடியவை, இரண்டுமே அமர்வுத் தரவைச் சுமக்காதவை: ஒரு அநாமதேய நிறுவல் பிங் மற்றும் PyPI-க்கு எதிரான ஒரு பதிப்பு சோதனை. இயல்புநிலை நிறுவல் ஒரு தொடக்க பேனர் வரிக்காக உங்கள் பொது IP-ஐ ஒருமுறை தேடும். ஒவ்வொரு இலக்கும், அது என்ன சுமக்கிறது, மற்றும் அதை எப்படி அணைப்பது என்பதும் [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது; self-hosted, repointed மற்றும் air-gapped நிறுவல்கள் விருப்பப்படி வெளிச்செல்லும் அழைப்புகள் எதையும் செய்வதில்லை.

Decryption உங்கள் பிரௌசரில், நாங்கள் உங்களுக்கு வழங்கும் கோடில் நடக்கிறது. இது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள் சரிபார்க்கக்கூடிய ஒன்று. உங்கள் கீயைத் தொடும் ஒவ்வொரு வரியும் ஒரே படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது wheel-க்குள் அனுப்பப்பட்டு, அப்படியே வழங்கப்பட்டு, ஒரு Subresource Integrity ஹாஷுடன் பின் செய்யப்பட்டுள்ளது. பிரௌசர் நாங்கள் வெளியிட்டதையே இயக்குகிறது என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

இது என்ன நிரூபிக்கவில்லை: கோப்பை ஏற்றும் பக்கத்தை நாங்களே வழங்குகிறோம், எனவே நாங்கள் வேறு பக்கத்தை வழங்கலாம். Integrity ஹாஷ்கள் ஒரு சமரசம் செய்யப்பட்ட CDN-இலிருந்து உங்களைப் பாதுகாக்கின்றன, விற்பனையாளரிடமிருந்து அல்ல. நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றீடும் வேண்டுமென்றே செய்யப்பட வேண்டும், பக்க மூலத்தில் தெரியும்படி இருக்க வேண்டும், மேலும் யாரும் பெறக்கூடிய PyPI-இல் உள்ள ஒரு artifact-ஐ விட வேறுபட்டதாக இருக்க வேண்டும். Self-hosting செய்வது அல்லது local-only ஆக இருப்பது இந்தச் சார்பை முழுவதுமாக நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பிறகு: clawmetry
```

அல்லது ஒரே-வரி கட்டளை: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows-இல் Python 3.8+ தேவை, அதே கணினியில் குறைந்தது ஒரு ஏஜென்ட் ரன்டைமும் தேவை. Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

## ஆவணங்கள்

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ஒவ்வொரு adapter-ம் எதைப் படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படிச் சேர்ப்பது |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | வழங்குநர்-வாரியான விண்டோக்கள், compaction எதிராக overflow, ரன்டைம்-வாரியான கவரேஜ் |
| [Overhead](docs/OVERHEAD.md) | இன்ஸ்ட்ரூமென்டேஷன் என்ன செலவாகிறது, அளவிடப்பட்டது, அதை மீண்டும் உருவாக்கும் harness உடன் |
| [Entitlements](docs/ENTITLEMENTS.md) | Free எதிராக paid, tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, ரிஸ்க் ஸ்கோரிங், மொபைல் அனுமதிகள் |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | எங்கு வேண்டுமானாலும் traces-ஐ export செய்யவும், எதிலிருந்தும் OTLP-ஐ ingest செய்யவும் |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain முழுவதுமாக, இயக்கக்கூடிய உதாரணங்களுடன் |
| [SDK tracking](docs/SDK_TRACKING.md) | நீங்களே உருவாக்கிய ஏஜென்ட்களுக்கான செலவு அட்ரிபியூஷன் |
| [Chat channels](docs/CHANNELS.md) | Flow-இல் காட்டப்படும் chat adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | இது உள்ளே எப்படி வேலை செய்கிறது; மூலத்திலிருந்து இயக்குவது |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் desktop-open பிங்குகள், மற்றும் அவற்றை எப்படி அணைப்பது |

## ஸ்கிரீன்ஷாட்கள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான கணினியிலிருந்து, read-only முறையில், எதுவும் விதைக்கப்படாமல் எடுக்கப்பட்டது.

**ஏதோ தவறு நடக்கும்போது இது உங்களுக்குச் சொல்கிறது, வெறும் என்ன நடந்தது என்பதை மட்டுமல்ல.**
மேலே இரண்டு அசாதாரண பேனர்கள்: தினசரி சராசரியை விட 7 மடங்கு அதிகமாக ஓடும் செலவு, மற்றும் 4.2x செலவு உயர்வு. அவற்றுக்குக் கீழே, சமீபத்திய 667 அமர்வுகளில் 324, ஒரு வீண்-செலவு சிக்னலைக் கொண்டு, காரணம் வாரியாகப் பட்டியலிடப்பட்டுள்ளது.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கு சென்றது என்பதை, ஒவ்வொரு காலக்கட்டத்திலும் இது காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றுக்கும் அதன் பின்னால் இருக்கும் டோக்கன்களுடனும், உங்கள் சந்தா ஏற்கனவே எவ்வளவு உள்ளடக்குகிறது என்பதுடனும். அதற்குக் கீழே, சுமார் $1,128/மாதம் மீட்டெடுக்கக்கூடியதாக பட்டியலிடப்பட்டு, cache மறுபயன்பாட்டால் ஏற்கனவே $17,256/மாதம் சேமிக்கப்பட்டுள்ளது.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு செய்தி எப்படி ஒரு பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
நேரடி ஃப்ளோ வரைபடம்: நீங்கள், அது வந்த சேனல், gateway, தற்போது பதிலளிக்கும் மாடல், மற்றும் அது பயன்படுத்திய ஒவ்வொரு டூலும். வேலை அவற்றின் வழியாக நகரும்போது நோடுகள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**கணினியில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே அட்டவணையில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் வாழ்நாள் முழுவதிலும் அதன் செலவு என்ன, அது கடைசியாக எப்போது பார்க்கப்பட்டது, யாருக்குச் சொந்தமானது, மற்றும் ஒரு சந்தா பில்லை ஈடுசெய்கிறதா என்பது. இங்கு 14 ஏஜென்ட்கள், 3 அமர்வுகள் வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கு சென்றது என்பதை, டூல் வாரியாக இது காட்டுகிறது.**
ஒரு உண்மையான அமர்வின் ஒரு டர்ன்: $1.16-க்கு 11.2 நிமிடங்களில் 11 டூல்கள். ஒவ்வொரு Bash அழைப்பும் மாடல் அழைப்பும் காலவரிசையில் அதன் சொந்த பட்டியை (bar) பெறுகிறது, எனவே 4.1 நிமிடங்கள் ஓடிய கட்டளையும் 226ms ஓடிய கட்டளையும் ஒரே பார்வையில் வேறுபடுத்தப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பீடு செய்கிறது, வெறும் செலவை மட்டுமல்ல.**
இந்த வாரம் ஒரு A தரம்: 54 பணிகள் சுத்தமாக முடிந்தன, 2 கடினமானவை $48.57 செலவாயின, மேலும் மதிப்பீடு செய்ய முடியாத அளவு குறைவான செயல்பாட்டைக் கொண்ட ரன்கள் வெற்றிகளாக எண்ணப்படுவதற்குப் பதிலாக தரத்திலிருந்து விடுபடுத்தப்படுகின்றன. ஒவ்வொரு கடினமான ரன்னும் அதன் trace-க்கு இணைக்கிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**சூழல் விண்டோ ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் விண்டோவில் 715K, 83.3% உச்சம், அனைத்தும் overflow-இல் அல்லாமல் proactive-ஆக ஏற்பட்ட 4 compactions, மேலும் அதற்குப் பின்னால் இருக்கும் ஒவ்வொரு டர்னின் பயன்பாடும்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**எதையும் நீங்கள் உள்ளமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
நிறுவலிலிருந்தே இயங்கும் உள்ளமைக்கப்பட்ட கண்டறிபவைகள்: ஏஜென்ட் அமைதியானது, டெலிமெட்ரி ஃபீட் நின்றது, செலவு உயர்வு, டோக்கன் வெடிப்பு, பிழைகள் உயர்வது, பிழை உயர்வு, பட்ஜெட் வரம்பு, அச்சுறுத்தல் கையொப்பம் பொருந்தியது, பாதுகாப்பு கருவி கண்டுபிடிப்பு, பாதுகாப்பு நிலை மாற்றம். உங்கள் சொந்த விதிகள் அதற்கு மேல் விருப்பத்தேர்வு.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ஆபத்தான அழைப்பை இடைநிறுத்துவது opt-in, மேலும் அணைக்கப்பட்ட நிலையில் அனுப்பப்படுகிறது.**
Recursive deletes, force pushes, sudo, secrets, package installs மற்றும் வெளிச்செல்லும் அழைப்புகள் ஒவ்வொன்றும் நீங்கள் இயக்கக்கூடிய ஒரு விதியைப் பெறுகின்றன. நீங்கள் அதைச் செய்யும் வரை, ClawMetry கவனிக்கிறது, எதையும் மாற்றாது. ஒன்று இயக்கப்பட்டவுடன், பொருந்தும் அழைப்புகள் ஒரு approve அல்லது deny-க்காக இங்கே (அல்லது உங்கள் மொபைலில்) காத்திருக்கும்.

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

MIT · [@vivekchand](https://github.com/vivekchand) ஆல் உருவாக்கப்பட்டது · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
