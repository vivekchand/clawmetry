<!-- i18n-src:12b97259721e -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ஒரு ஏஜென்ட், முன்னேற்றம் இல்லாமலேயே நூறு டூல் அழைப்புகளை செய்யலாம்.** ClawMetry, உங்கள் கோடிங் ஏஜென்ட்கள் ஏற்கனவே எழுதும் செஷன் கோப்புகளைப் படித்து, டைம்லைனையும், டூல் அழைப்புகளையும், ரன்டைம் வெளிப்படுத்தும் டோக்கன் மற்றும் செலவு தரவையும் ஒரே பார்வையில் கொண்டு வருகிறது — இதனால் வேலை செய்யும் நீண்ட ரன் ஒன்றை, தேங்கி நிற்கும் ஒன்றிலிருந்து வேறுபடுத்திச் சொல்ல முடியும்.

**31 AI ஏஜென்ட் ரன்டைம்களுடன்** வேலை செய்கிறது — Claude Code, OpenAI Codex, Hermes, OpenClaw மற்றும் இன்னும் 27. உங்கள் முழு ஏஜென்ட் கடற்படைக்கும் ஒரே டாஷ்போர்டு. ([முழு பட்டியல்](SUPPORTED_RUNTIMES.txt), காடலாக்கிலிருந்து உருவாக்கப்பட்டது.)

> 🌐 **இதை படிக்க:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். கட்டமைப்பு தேவையில்லை: நீங்கள் ஏற்கனவே வைத்திருக்கும் ஏஜென்ட் ரன்டைம்களை இது கண்டறிந்து, அவற்றை read-only ஆக படித்து, அவை இயங்கும் விதத்தில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## நிறுவுவதற்கு முன்

| | |
|---|---|
| **இது என்ன செய்கிறது** | உங்கள் ஏஜென்ட்கள் ஏற்கனவே எழுதும் செஷன் கோப்புகளையும் லாக்குகளையும் படிக்கிறது. SDK இல்லை, குறியீட்டு மாற்றம் இல்லை, உங்கள் ஆப்பில் இன்ஸ்ட்ரூமென்டேஷன் இல்லை. |
| **நீங்கள் என்ன பார்க்கிறீர்கள்** | செஷன் டைம்லைன், டூல்-வாரியான ரீபிளே, டோக்கன் மற்றும் செலவு விவரம், மற்றும் ட்ரஜெக்டரி சிக்னல்கள் (லூப்பிங், மீண்டும் மீண்டும் தோல்விகள்) — ஒவ்வொரு ரன்டைமுக்கும். |
| **இலவசமாக என்ன கிடைக்கும்** | `pip install clawmetry` எந்த கணக்கும், கீயும், நெட்வொர்க் அழைப்பும் இல்லாமல் **OpenClaw, NVIDIA NemoClaw மற்றும் Goose** ஐ படிக்கும். மற்ற 27 — Claude Code, Codex, Cursor மற்றும் மற்றவை — closed-source `clawmetry-pro` துணை நிரலால் படிக்கப்படுகின்றன, இது 7-நாள் டிரையலுடன் அல்லது ஒரு திட்டத்துடன் வருகிறது — சரியான பிரிவினைக்கு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) பார்க்கவும். |
| **எப்படி தொடங்குவது** | `pip install clawmetry && clawmetry`, பிறகு localhost:8900 ஐ திறக்கவும். இந்த மெஷினில் இன்னும் ஏஜென்ட்கள் இல்லையா? `clawmetry --sample` மூன்று லேபிள் செய்யப்பட்ட செயற்கை செஷன்களுடன் திறக்கும். |
| **உங்கள் மெஷினை விட்டு என்ன வெளியேறுகிறது** | `clawmetry connect` ஐ இயக்காத வரை, செஷன் தரவு எதுவும் வெளியேறாது. இயல்பாக இரண்டு விஷயங்கள் மட்டும் இயங்குகின்றன, இரண்டும் opt-out செய்யக்கூடியவை, செஷன் உள்ளடக்கத்தை கொண்டு செல்வதில்லை: அநாமதேய நிறுவல் பிங் மற்றும் PyPI பதிப்பு சரிபார்ப்பு. ஒவ்வொரு இலக்கும் [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது, கருத்துகளைப் படிப்பதைவிட வயர் captureலிருந்து மறு-கட்டமைக்கப்பட்டது. |

நீங்கள் வெளியீட்டை மதிப்பிடுவதற்கு முன் தெரிந்திருக்க வேண்டிய இரண்டு வரம்புகள்: ரன்டைம்கள் மிகவும் வேறுபட்ட தரவை வெளிப்படுத்துகின்றன (சில எந்த செலவையும் வெளியிடுவதில்லை — [மேட்ரிக்ஸ்](docs/compatibility.md) எந்த ரன்டைமுக்கு என்ன என்பதை சொல்கிறது), மற்றும் ஒரு செயலைக் கவனிப்பது என்பது அதைத் தடுக்க முடியும் என்பதைப் போன்றது அல்ல ([ஒவ்வொரு ரன்டைமுக்கும் எந்த கட்டுப்பாடுகள் உண்மையானவை](docs/APPROVALS.md)).


## 31 ஏஜென்ட் ரன்டைம்களுடன் வேலை செய்கிறது

**ஓப்பன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**கட்டண திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமுக்கும் ஒரே டாஷ்போர்டு கிடைக்கும். ஒரே நேரத்தில் பலவற்றை இயக்கினால், தலைப்பு ஸ்விட்சர் ஒவ்வொரு டேபையும் அவற்றில் ஒன்றுக்கு மறு-ஸ்கோப் செய்யும்.

ஒரு SDK மீது உங்கள் சொந்த ஏஜென்டை உருவாக்கினீர்களா? இன்டர்செப்டர் அதன் LLM அழைப்புகளையும் கண்காணிக்கும். [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) பார்க்கவும்.

## உங்களுக்கு என்ன கிடைக்கும்

- **செஷன்கள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, டர்ன் டர்னாக, ரீபிளேயுடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், செஷன் மற்றும் நாள் வாரியாக, ஏனோமலி கொடிகளுடன்
- **ஃப்ளோ**: சேனல்கள், மாடல்கள் மற்றும் டூல்கள் வழியாக செல்லும் மெசேஜ்களின் லைவ் வரைபடம்
- **பிரெயின்**: நிகழும் போதே reasoning மற்றும் tool-call event ஸ்ட்ரீம்
- **கான்டெக்ஸ்ட் பிளோஅவுட்**: provider வாரியாக அளவிடப்பட்ட விண்டோ யூட்டிலைசேஷன், compaction vs வலுக்கட்டாயமான overflow, மேலும் நமக்கு *பார்க்க முடியாதது* என்ன என்பதன் ரன்டைம்-வாரி வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **மெமரி & ஸ்கில்ஸ்**: ஒவ்வொரு ரன்டைமும் உண்மையில் லோட் செய்த கோப்புகள் மற்றும் ஸ்கில்கள்
- **ஹெல்த் & லாக்ஸ்**: டிஸ்க், மெமரி, error rates, rate limits, லைவ் லாக் ஸ்ட்ரீம்
- **அலர்ட்ஸ்**: பட்ஜெட் காப்கள், error spikes, agent-offline, Slack, Discord, PagerDuty, Telegram, Email க்கு ரூட் செய்யப்படும்
- **அப்ரூவல்ஸ்**: ரிஸ்க் உள்ள டூல் அழைப்புகளை அவை *இயங்குவதற்கு முன்* இடைநிறுத்தி, உங்கள் ஃபோனிலிருந்தே அப்ரூவ் செய்யவும் ([எப்படி](docs/APPROVALS.md))

## கான்டெக்ஸ்ட் பிளோஅவுட், மற்றும் கவனிப்பதன் விலை

எந்த ஏஜென்ட்-ஒப்பீட்டு கருவியையும் நம்புவதற்கு முன் பதில் சொல்ல வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்கள் முழுவதும் கான்டெக்ஸ்ட்-விண்டோ பிளோஅவுட்டை இது எப்படி கையாளுகிறது?**

ஒரு யூட்டிலைசேஷன் சதவீதம், அது எதைப் பிரிக்கிறதோ அந்த அளவுக்குத்தான் நேர்மையானது. ClawMetry, [நீங்கள் படித்து PR செய்யக்கூடிய அட்டவணையிலிருந்து](clawmetry/context_windows.py) provider வாரியாக விண்டோவை அளவிடுகிறது, இது Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM ஐ உள்ளடக்குகிறது. இது 31 ரன்டைம்களையும் ஒரே vendor-இன் அளவுகோலால் அளவிடுவதில்லை. இது முக்கியம்: Anthropic-இன் 200K க்கு எதிராக மதிப்பிடப்படும் 300K GPT-5 டர்ன் ">100%, blown" எனப் படிக்கப்படும், ஆனால் உண்மையில் அது GPT-5-இன் 400K இல் 75% ஆகும். அதே அளவுகோல், உண்மையில் overflow ஆன 130K DeepSeek டர்னை வசதியான 65% ஆக மறைக்கிறது.

ஒவ்வொரு விண்டோவும் அதன் provenance-உடன் வருகிறது: `model_table`, `explicit_marker`, `observed_floor`, அல்லது மாடல் தெரியாதபோது நேர்மையான `default`. ஒரு ஊகத்தின் அடிப்படையில் கட்டப்பட்ட கேஜ், ஒரு lookup-இன் அடிப்படையில் கட்டப்பட்டதைப் போன்ற அதிகாரத்துடன் ஒருபோதும் காட்சியளிக்காது.

சில ரன்டைம்களில் மட்டுமே ClawMetry-க்கு compaction events பார்க்க முடியும். எனவே `GET /api/context-coverage`, ஒவ்வொரு ரன்டைமுக்கும், ஒரு பூஜ்ஜியம் **"தூய்மையாக இயங்கியது" என்பதையா அல்லது "நமக்குத் தெரியாது" என்பதையா குறிக்கிறது** என்பதை அறிக்கை செய்கிறது. உண்மையில் "தெரியாது" என்று பொருள்படும் ஒரு `0`, அதையே சொல்கிறது. [முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**இன்ஸ்ட்ரூமென்டேஷனின் விலை என்ன?**

| பாதை | உங்கள் ஏஜென்டுக்குச் சேர்க்கப்பட்டது | இயல்பாக? |
|---|---|---|
| செஷன்-கோப்பு டெயிலிங் (எல்லா 31 ரன்டைம்களும்) | **0**. தனி process, உங்கள் ஏஜென்டில் ClawMetry குறியீடு இல்லை | ஆன் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒவ்வொரு LLM அழைப்புக்கும் **+0.44 ms**, அதாவது 5s அழைப்பில் 0.009% | ஆஃப் |
| Pre-tool hook gate (warm cache) | 36 ms interpreter floor மேல், gate செய்யப்பட்ட ஒவ்வொரு tool call-க்கும் **+44 ms** | ஆஃப் |
| Enforcement proxy | ஒவ்வொரு LLM அழைப்புக்கும் **+9.7 ms** | ஆஃப் |

Daemon host செலவு: **2,762 events/sec** ingest, டிஸ்கில் **710 bytes/event** (100k events-க்கு 67.7 MB), மற்றும் busy install ஒன்றில் தொடர்ச்சியாக **ஒரு core-இன் ~12%**. அந்த கடைசி எண், நாமே கூறிய 5-10% பட்ஜெட்டை மீறுகிறது, எனவே அதை பக்கத்தில் இருந்து விட்டுவிடாமல், துரத்த வேண்டிய பிழையாக வெளியிடப்பட்டுள்ளது.

Apple M2 Pro-இல் `benchmarks/overhead.py` மூலம் அளவிடப்பட்டது. இந்த harness ஒவ்வொரு condition-ஐயும் தனி process-இல் இயக்கி, அவற்றின் வரிசையை மாற்றி, **rounds தங்கள் sign-ஐப் பற்றி உடன்படாதபோது எண் அச்சிட மறுக்கிறது**. உங்கள் சொந்த மெஷினில் ஒரு நிமிடத்தில் இதை இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook gates மற்றும் enforcement proxy உட்பட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது, மேலும் இந்த harness CI-இல் Linux, macOS மற்றும் Windows-இல் இயங்குகிறது. தெரிந்திருக்க வேண்டிய இரண்டு முடிவுகள்: proxy, Linux-ஐ விட Windows-இல் சுமார் ஏழு மடங்கு அதிகம் செலவாகிறது, மேலும் daemon தற்போது ஒரு core-இன் சுமார் 12%-ஐ தொடர்ச்சியாகப் பயன்படுத்துகிறது, இது நாமே கூறிய 5-10% பட்ஜெட்டை மீறுகிறது. மூல JSON, முறை, மற்றும் இன்னும் அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md) இல் உள்ளன.

## விலை நிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose, முழு டாஷ்போர்டு, லோக்கல் மட்டும் | $0 |
| **ஸ்டார்ட்டர்** | மேலே உள்ள மற்ற ஒவ்வொரு ரன்டைமும், ஃப்ளீட் வியூ, க்ளவுட் சிங்க் | ஒரு node க்கு $9 / மாதம் |
| **Pro** | ஸ்டார்ட்டர் + கட்டுப்பாடு மற்றும் மதிப்பீடு: அப்ரூவல்ஸ், tool-risk கொள்கைகள், evals, ஏனோமலி டிடெக்ஷன், cost optimizer, OTel export, tamper-evident audit log | ஒரு node க்கு $19 / மாதம் |

வருடாந்திர திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)** இல் உள்ளன. Self-hosted license keys, க்ளவுட் இல்லாமலேயே வேலை செய்யும் (`clawmetry license`). துல்லியமான இலவச/கட்டண பிரிவினை [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) இல் உள்ளது.

## உங்கள் தரவு உங்கள் மெஷினிலேயே இருக்கும்

ClawMetry, லோக்கல் செஷன் கோப்புகள் மற்றும் லாக்குகளைப் படிக்கிறது. **நீங்கள் `clawmetry connect` இயக்காத வரை, உங்கள் box-இலிருந்து எந்த செஷன் தரவும் வெளியேறாது** — prompts, replies, tool arguments, file contents அல்லது log lines எதுவும் இல்லை. நீங்கள் connect செய்தால், உங்கள் மெஷினை விட்டு ஒருபோதும் வெளியேறாத ஒரு key மூலம் snapshot end-to-end encrypt செய்யப்பட்டு, உங்கள் browser-இல் decrypt செய்யப்படுகிறது. ஒரு node-க்கு key இல்லையென்றால், தெளிவாக அனுப்பப்படுவதற்குப் பதிலாக upload தவிர்க்கப்படும், மேலும் எந்த server response-ஆலும் அதை அணைக்க முடியாது.

நீங்கள் connect செய்வதற்கு முன் இயல்பாக இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும் opt-out செய்யக்கூடியவை, செஷன் தரவை கொண்டு செல்வதில்லை: அநாமதேய நிறுவல் பிங் மற்றும் PyPI-க்கு எதிரான பதிப்பு சரிபார்ப்பு. இயல்பான நிறுவல் ஒன்று, தொடக்க பேனர் வரிக்காக உங்கள் பொது IP-ஐயும் ஒருமுறை தேடும். ஒவ்வொரு இலக்கும், அது என்ன கொண்டு செல்கிறது, அதை எப்படி அணைப்பது என்பதும் [docs/EGRESS.md](docs/EGRESS.md) இல் பட்டியலிடப்பட்டுள்ளது; self-hosted, திசைமாற்றப்பட்ட மற்றும் air-gapped நிறுவல்கள் விருப்பப்படி வெளிச்செல்லும் அழைப்புகள் எதையும் செய்யாது.

decryption உங்கள் browser-இல், நாங்கள் உங்களுக்கு வழங்கும் குறியீட்டில் நடக்கிறது. அது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள் சரிபார்க்கக்கூடிய ஒன்று. உங்கள் key-ஐத் தொடும் ஒவ்வொரு வரியும் ஒரே படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது wheel-இனுள் அனுப்பப்பட்டு, Subresource Integrity hash-உடன் pin செய்யப்பட்டு அப்படியே வழங்கப்படுகிறது. browser நாங்கள் வெளியிட்டதையே இயக்குகிறதா என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

இது என்ன நிரூபிக்காது: கோப்பை லோட் செய்யும் பக்கத்தை நாங்களே வழங்குகிறோம், எனவே நாங்கள் வேறு பக்கத்தையும் வழங்கலாம். Integrity hashes, ஒரு பாதிக்கப்பட்ட CDN-இலிருந்து உங்களைப் பாதுகாக்கின்றன, vendor-இலிருந்து அல்ல. நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றமும் வேண்டுமென்றே செய்யப்பட வேண்டும், பக்க மூலத்தில் தெரியும்படி இருக்க வேண்டும், மேலும் யாரும் பெறக்கூடிய PyPI artifact-இலிருந்து வேறுபட்டதாக இருக்க வேண்டும். Self-hosting செய்வது அல்லது local-only ஆக இருப்பது, இந்த சார்பை முழுவதுமாக நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பிறகு: clawmetry
```

அல்லது ஒரே-வரி கட்டளை: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows-இல் Python 3.8+ தேவை, மற்றும் அதே மெஷினில் குறைந்தது ஒரு ஏஜென்ட் ரன்டைம் தேவை. Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

அல்லது ஏஜென்ட் இதை உங்களுக்காக அமைக்கட்டும். [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) ஸ்கில், Claude Code, Codex, Cursor, Gemini CLI, Copilot அல்லது OpenCode-க்கு ClawMetry நிறுவவும், மெஷினில் உள்ள ஏஜென்ட்கள் என்ன செய்கின்றன, எவ்வளவு செலவழிக்கின்றன என்பதை அறிக்கை செய்யவும், கோரிக்கை மீது ஒரு செஷனை நிறுத்தவும், அப்ரூவலுக்காக ரிஸ்க் உள்ள tool calls-ஐ இடைநிறுத்தவும் கற்றுக்கொடுக்கிறது:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ஆவணங்கள்

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ஒவ்வொரு adapterம் என்ன படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Provider-வாரி விண்டோக்கள், compaction vs overflow, ரன்டைம்-வாரி coverage |
| [Overhead](docs/OVERHEAD.md) | இன்ஸ்ட்ரூமென்டேஷனின் விலை, அளவிடப்பட்டது, மறுஉருவாக்கம் செய்ய harness உடன் |
| [Entitlements](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், tier மேட்ரிக்ஸ், license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, phone approvals |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | எங்கும் traces export செய்யவும், எதிலிருந்தும் OTLP ingest செய்யவும் |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain முழுவதும், இயக்கக்கூடிய உதாரணங்களுடன் |
| [SDK tracking](docs/SDK_TRACKING.md) | நீங்களே உருவாக்கிய ஏஜென்ட்களுக்கான cost attribution |
| [Chat channels](docs/CHANNELS.md) | Flow-இல் காட்டப்படும் chat adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | இது உள்ளூர் எப்படி வேலை செய்கிறது; மூலத்திலிருந்து இயக்குதல் |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் desktop-open pings, அவற்றை எப்படி அணைப்பது |

## ஸ்கிரீன்ஷாட்கள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான மெஷினில் இருந்து, read-only ஆக, எதுவும் seed செய்யாமல் எடுக்கப்பட்டது.

**எதாவது தவறாக இருக்கும்போது இது உங்களுக்குச் சொல்கிறது, என்ன நடந்தது என்பது மட்டும் அல்ல.**
மேலே இரண்டு ஏனோமலி பேனர்கள்: தினசரி சராசரியை விட 7 மடங்கு அதிகமாக இயங்கும் செலவு, மற்றும் 4.2 மடங்கு cost spike. அவற்றின் கீழே, சமீபத்திய 667 செஷன்களில் 324, waste சிக்னலைச் சுமந்திருக்கின்றன, காரணம் வாரியாக பட்டியலிடப்பட்டுள்ளது.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கே சென்றது என்பதை, ஒவ்வொரு காலகட்டத்திலும் இது காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றுக்கும் அதன் பின்னால் உள்ள டோக்கன்களுடனும் உங்கள் subscription ஏற்கனவே எவ்வளவு உள்ளடக்குகிறது என்பதுடனும். அதற்குக் கீழே, மீட்கக்கூடியதாக பட்டியலிடப்பட்ட சுமார் $1,128/மாதம் மற்றும் cache reuse மூலம் ஏற்கனவே சேமிக்கப்பட்ட $17,256/மாதம்.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு மெசேஜ் எப்படி பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
லைவ் ஃப்ளோ வரைபடம்: நீங்கள், அது வந்த சேனல், gateway, தற்போது பதிலளிக்கும் மாடல், மற்றும் அது பயன்படுத்திய ஒவ்வொரு டூலும். வேலை அவற்றின் வழியாக நகரும்போது நோட்கள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**மெஷினில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே அட்டவணையில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் ஆயுள் முழுவதும் எவ்வளவு செலவாகிறது, அது கடைசியாக எப்போது பார்க்கப்பட்டது, யாருக்குச் சொந்தமானது, மற்றும் ஒரு subscription பில்லை உள்ளடக்குகிறதா என்பது. இங்கே 14 ஏஜென்ட்கள், 3 செஷன்கள் வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கே சென்றது என்பதை, டூல் வாரியாக இது காட்டுகிறது.**
ஒரு உண்மையான செஷனின் ஒரு டர்ன்: 11.2 நிமிடங்களில் $1.16-க்கு 11 டூல்கள். ஒவ்வொரு Bash அழைப்புக்கும் model அழைப்புக்கும் டைம்லைனில் அதற்கான சொந்த பட்டை உள்ளது, எனவே 4.1 நிமிடங்கள் இயங்கிய கட்டளையும் 226ms இயங்கிய ஒன்றும் ஒரே பார்வையில் வேறுபடுத்தப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பிடுகிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக முடிந்தன, 2 கடினமான பணிகள் $48.57 செலவாயின, மற்றும் மதிப்பிடுவதற்குப் போதுமான செயல்பாடு இல்லாத ரன்கள் வெற்றிகளாக எண்ணப்படுவதற்குப் பதிலாக grade-இலிருந்து விடுவிக்கப்பட்டுள்ளன. ஒவ்வொரு கடினமான ரன்னும் அதன் trace-க்கு லிங்க் செய்கிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**கான்டெக்ஸ்ட் விண்டோ ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் விண்டோவில் 715K, 83.3% உச்சம், overflow-இல் அல்லாமல் அனைத்தும் proactive ஆக இயங்கிய 4 compactions, மற்றும் அதற்குப் பின்னால் உள்ள ஒவ்வொரு டர்னின் யூட்டிலைசேஷன்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
built-in டிடெக்டர்கள் நிறுவலிலிருந்தே ஆனாக உள்ளன: ஏஜென்ட் அமைதியானது, telemetry feed நிறுத்தப்பட்டது, cost spike, token burst, errors அதிகரிப்பு, error spike, budget threshold, threat signature match, security tool கண்டுபிடிப்பு, security posture மாற்றம். உங்கள் சொந்த விதிகள் இதற்கு மேல் விருப்பமானவை.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ரிஸ்க் உள்ள அழைப்பை இடைநிறுத்துவது opt-in ஆனது, மற்றும் ஆஃப் ஆகவே வழங்கப்படுகிறது.**
Recursive deletes, force pushes, sudo, secrets, package installs மற்றும் outbound calls ஒவ்வொன்றுக்கும் நீங்கள் ஆன் செய்யக்கூடிய ஒரு விதி உள்ளது. நீங்கள் அதைச் செய்யும் வரை, ClawMetry கவனிக்கிறது, எதையும் மாற்றாது. ஒன்று ஆன் ஆனதும், பொருந்தும் அழைப்புகள் இங்கே (அல்லது உங்கள் ஃபோனில்) approve அல்லது deny-க்காக காத்திருக்கும்.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ரன்டைம் வாரியாக மேலும்: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
