<!-- i18n-src:b22579578775 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ஒரு ஏஜென்ட் முன்னேற்றமே இல்லாமல் நூறு டூல் அழைப்புகளைச் செய்யக்கூடும்.** ClawMetry
உங்கள் கோடிங் ஏஜென்ட்கள் ஏற்கெனவே எழுதும் செஷன் கோப்புகளைப் படித்து, டைம்லைன், டூல் அழைப்புகள், மற்றும் runtime வெளிப்படுத்தும் டோக்கன் மற்றும் செலவு தரவு அனைத்தையும் ஒரே காட்சியில் கொண்டு வருகிறது — இதனால் வேலை செய்யும் நீண்ட ரன்னையும் நின்றுவிட்ட ரன்னையும் நீங்கள் வேறுபடுத்தி அறியலாம்.

**32 AI ஏஜென்ட் runtimes** உடன் வேலை செய்கிறது — Claude Code, OpenAI Codex, Hermes, OpenClaw & மேலும் 28. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு. ([முழு பட்டியல்](SUPPORTED_RUNTIMES.txt), காட்டலாக் இலிருந்து உருவாக்கப்பட்டது.)

> 🌐 **இதை இதில் படியுங்கள்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. அனைத்தையும் தானாக கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** என்ற முகவரியில் திறக்கும். கட்டமைப்பு தேவையில்லை: நீங்கள் ஏற்கெனவே வைத்திருக்கும் ஏஜென்ட் runtime-களை இது கண்டறிந்து, அவற்றை read-only ஆக படித்து, அவை இயங்கும் விதத்தில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## நிறுவுவதற்கு முன்

| | |
|---|---|
| **இது என்ன செய்கிறது** | உங்கள் ஏஜென்ட்கள் ஏற்கெனவே எழுதும் செஷன் கோப்புகளையும் பதிவுகளையும் படிக்கிறது. SDK இல்லை, உங்கள் ஆப்பில் குறியீட்டு மாற்றம் இல்லை, instrumentation இல்லை. |
| **நீங்கள் காண்பது** | செஷன் டைம்லைன், டூல்-வாரியான மறுஇயக்கம், டோக்கன் மற்றும் செலவு பிரிவு, மற்றும் trajectory சிக்னல்கள் (லூப்பிங், மீண்டும் தோல்விகள்) — runtime வாரியாக. |
| **இலவசமாக என்ன கிடைக்கும்** | `pip install clawmetry` எந்த கணக்கும், key-யும், நெட்வொர்க் அழைப்பும் இல்லாமல் **OpenClaw, NVIDIA NemoClaw, Goose மற்றும் Qwen Code** ஆகியவற்றைப் படிக்கிறது. மற்ற 28 — Claude Code, Codex, Cursor மற்றும் பிற — closed-source `clawmetry-pro` துணை நிரலால் படிக்கப்படுகின்றன, இது 7-நாள் சோதனையுடன் அல்லது ஒரு திட்டத்துடன் வருகிறது — சரியான பிரிவுக்கு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) பார்க்கவும். |
| **எப்படி தொடங்குவது** | `pip install clawmetry && clawmetry`, பின்னர் localhost:8900-ஐ திறக்கவும். இந்த மெஷினில் இன்னும் ஏஜென்ட்கள் இல்லையா? `clawmetry --sample` லேபிள் செய்யப்பட்ட மூன்று செயற்கை செஷன்களுடன் திறக்கும். |
| **உங்கள் மெஷினை விட்டு என்ன வெளியேறுகிறது** | நீங்கள் `clawmetry connect` இயக்காத வரை எந்த செஷன் தரவும் வெளியேறாது. இயல்பாக இரண்டு விஷயங்கள் இயங்கும், இரண்டும் opt-out மற்றும் செஷன் உள்ளடக்கத்தை சுமக்காதவை: அநாமதேய நிறுவல் பிங் மற்றும் PyPI பதிப்பு சரிபார்ப்பு. ஒவ்வொரு இலக்கும் [docs/EGRESS.md](docs/EGRESS.md)-இல் பட்டியலிடப்பட்டுள்ளது, கருத்துகளைப் படிப்பதற்குப் பதிலாக ஒரு wire capture-இலிருந்து மறுகட்டமைக்கப்பட்டது. |

வெளியீட்டை மதிப்பிடுவதற்கு முன் தெரிந்துகொள்ள வேண்டிய இரண்டு வரம்புகள்: runtimes மிகவும் வேறுபட்ட தரவை வெளிப்படுத்துகின்றன (சில எந்த செலவையும் வெளியிடுவதே இல்லை — எது என்பதை [matrix](docs/compatibility.md) runtime வாரியாகக் கூறுகிறது), மற்றும் ஒரு செயலை கவனிப்பது அதைத் தடுக்க முடியும் என்பதற்கு சமமல்ல ([எந்தக் கட்டுப்பாடுகள் உண்மையானவை, runtime வாரியாக](docs/APPROVALS.md)).


## 32 ஏஜென்ட் runtimes உடன் வேலை செய்கிறது

**ஓபன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**கட்டணத் திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு runtime-க்கும் அதே டாஷ்போர்டு கிடைக்கும். பலவற்றை ஒரே நேரத்தில் இயக்கினால் ஹெடர் ஸ்விட்சர் ஒவ்வொரு டேபையும் அவற்றில் ஒன்றுக்கு மறுஸ்கோப் செய்கிறது.

உங்கள் சொந்த ஏஜென்டை SDK-இல் கட்டியிருந்தீர்களா? இன்டர்செப்டர் அதன் LLM அழைப்புகளையும் கண்காணிக்கும். [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **செஷன்கள் & டிரான்ஸ்கிரிப்ட்கள்**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, டர்ன் டர்னாக, மறுஇயக்கத்துடன்
- **செலவு & டோக்கன்கள்**: runtime, மாடல், செஷன் மற்றும் நாள் வாரியாக, அசாதாரண குறியீடுகளுடன்
- **Flow**: செய்திகள் சேனல்கள், மாடல்கள் மற்றும் டூல்கள் வழியாக நகரும் நேரடி வரைபடம்
- **Brain**: நடக்கும்போதே தர்க்கம் மற்றும் டூல்-அழைப்பு நிகழ்வு ஸ்ட்ரீம்
- **Context blowout**: ப்ரொவைடர் வாரியாக அளவிடப்பட்ட window பயன்பாடு, compaction vs கட்டாய overflow, மேலும் நாம் *பார்க்க முடியாதவற்றின்* runtime வாரியான வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: ஒவ்வொரு runtime-ம் உண்மையில் லோட் செய்த கோப்புகள் மற்றும் skills
- **Health & logs**: டிஸ்க், மெமரி, error rates, rate limits, நேரடி பதிவு ஸ்ட்ரீம்
- **Alerts**: பட்ஜெட் வரம்புகள், error spikes, ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, Email-க்கு route செய்யப்படும்
- **Approvals**: அபாயகரமான டூல் அழைப்புகளை அவை இயங்குவதற்கு *முன்பே* இடைநிறுத்தி, உங்கள் ஃபோனிலிருந்து அங்கீகரிக்கவும் ([எப்படி](docs/APPROVALS.md))

## Context blowout, மற்றும் கண்காணிப்பதற்கான செலவு

எந்த ஏஜென்ட்-ஒப்பீட்டு டூலையும் நம்புவதற்கு முன் பதிலளிக்க வேண்டிய இரண்டு கேள்விகள்.

**runtimes முழுவதும் context-window blowout-ஐ இது எப்படி கையாள்கிறது?**

பயன்பாட்டு சதவீதம் அது எதைக் கொண்டு வகுக்கிறதோ அதற்குச் சமமான நேர்மையானது. ClawMetry நீங்கள் படித்து PR செய்யக்கூடிய [ஒரு அட்டவணையிலிருந்து](clawmetry/context_windows.py) ப்ரொவைடர் வாரியாக window-ஐ அளவிடுகிறது, இது Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama மற்றும் GLM-ஐ உள்ளடக்குகிறது. இது ஒரே விற்பனையாளரின் அளவுகோலால் அனைத்து 33 runtimes-ஐயும் அளவிடுவதில்லை. இது முக்கியம்: Anthropic-இன் 200K-க்கு எதிராக மதிப்பிடப்பட்ட 300K GPT-5 டர்ன் ">100%, blown" எனப் படிக்கிறது, ஆனால் உண்மையில் அது GPT-5-இன் 400K-இல் 75% ஆகும். அதே அளவுகோல் உண்மையில் overflow ஆன 130K DeepSeek டர்னை வசதியான 65% ஆக மறைக்கிறது.

ஒவ்வொரு window-உம் அதன் தோற்றத்துடன் வருகிறது: `model_table`, `explicit_marker`, `observed_floor`, அல்லது மாடலைத் தெரியாதபோது நேர்மையான `default`. யூகத்தின் அடிப்படையில் கட்டப்பட்ட ஒரு gauge, lookup-இன் அடிப்படையில் கட்டப்பட்டதைப் போன்ற அதே அதிகாரத்துடன் ஒருபோதும் காட்சியளிக்காது.

சில runtimes-இல் மட்டுமே ClawMetry-க்கு compaction நிகழ்வுகளைக் காண முடியும். எனவே `GET /api/context-coverage` ஒவ்வொரு runtime-ஐயும் பற்றி, **பூஜ்ஜியம் "சுத்தமாக ஓடியது" என்று பொருள்படுமா அல்லது "நமக்குத் தெரியவில்லை" என்று பொருள்படுமா** என்பதைப் புகாரளிக்கிறது. உண்மையில் தெரியாது என்று அர்த்தமுள்ள `0` அப்படியே கூறுகிறது.
[முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**instrumentation-இன் செலவு என்ன?**

| பாதை | உங்கள் ஏஜென்டுக்குச் சேர்க்கப்பட்டது | இயல்பாக? |
|---|---|---|
| செஷன்-கோப்பு tailing (அனைத்து 33 runtimes) | **0**. தனி process, உங்கள் ஏஜென்டில் ClawMetry குறியீடு இல்லை | இயக்கத்தில் |
| HTTP இன்டர்செப்டர் (`CLAWMETRY_INTERCEPT=1`) | ஒவ்வொரு LLM அழைப்புக்கும் **+0.44 ms**, அல்லது 5s அழைப்பின் 0.009% | ஆஃப் |
| Pre-tool hook gate (warm cache) | 36 ms interpreter floor-க்கு மேல், gate செய்யப்பட்ட ஒவ்வொரு டூல் அழைப்புக்கும் **+44 ms** | ஆஃப் |
| Enforcement proxy | ஒவ்வொரு LLM அழைப்புக்கும் **+9.7 ms** | ஆஃப் |

Daemon host செலவு: **2,762 நிகழ்வுகள்/வினாடி** ingest, டிஸ்க்கில் **710 bytes/நிகழ்வு** (100k நிகழ்வுகளுக்கு 67.7 MB), மற்றும் ஒரு பிஸியான நிறுவலில் தொடர்ச்சியாக **ஒரு core-இன் ~12%**. அந்த கடைசி எண் நமது சொந்த 5-10% பட்ஜெட்டைவிட அதிகமாக உள்ளது, எனவே இது பக்கத்திலிருந்து விடுவதற்குப் பதிலாக துரத்தப்பட வேண்டிய பிழையாக வெளியிடப்படுகிறது.

Apple M2 Pro-இல் `benchmarks/overhead.py` மூலம் அளவிடப்பட்டது. harness ஒவ்வொரு நிலையையும் தனித்தனி processஇல் இயக்கி, அவற்றின் வரிசையை மாற்றி, **சுற்றுகள் அதன் அடையாளத்தில் உடன்படாதபோது எண்ணை அச்சிட மறுக்கிறது**. அதை உங்கள் சொந்த மெஷினில் ஒரு நிமிடத்தில் இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook gates மற்றும் enforcement proxy உள்ளிட்ட ஒவ்வொரு பாதையும் அளவிடப்படுகிறது, மேலும் harness CI-இல் Linux, macOS மற்றும் Windows-இல் இயங்குகிறது. தெரிந்துகொள்ள வேண்டிய இரண்டு முடிவுகள்: Windows-இல் proxy Linux-ஐ விட சுமார் ஏழு மடங்கு அதிகம் செலவாகிறது, மற்றும் daemon தற்போது ஒரு core-இன் சுமார் 12%-ஐ தொடர்ச்சியாகப் பயன்படுத்துகிறது, இது நமது சொந்த 5-10% பட்ஜெட்டைவிட அதிகம். மூல JSON, முறை, மற்றும் இன்னும் அளவிடப்படாதவை [docs/OVERHEAD.md](docs/OVERHEAD.md)-இல் உள்ளன.

## விலை நிர்ணயம்

| திட்டம் | அது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, முழு டாஷ்போர்டு, லோக்கல் மட்டும் | $0 |
| **Starter** | மேலே உள்ள மற்ற ஒவ்வொரு runtime-ம், fleet காட்சி, cloud sync | $9 ஒரு node-க்கு / மாதம் |
| **Pro** | Starter + கட்டுப்பாடு மற்றும் மதிப்பீடு: approvals, tool-risk கொள்கைகள், evals, அசாதாரண கண்டறிதல், செலவு optimizer, OTel export, tamper-evident audit log | $19 ஒரு node-க்கு / மாதம் |

வருடாந்திர திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)**-இல் உள்ளன. சொந்தமாக-ஹோஸ்ட் செய்யப்பட்ட license keys cloud இல்லாமல் வேலை செய்கின்றன (`clawmetry license`). சரியான இலவச/கட்டண பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-இல் உள்ளது.

## உங்கள் தரவு உங்கள் மெஷினிலேயே இருக்கும்

ClawMetry லோக்கல் செஷன் கோப்புகளையும் பதிவுகளையும் படிக்கிறது. **நீங்கள் `clawmetry connect` இயக்காத வரை உங்கள் பெட்டியிலிருந்து எந்த செஷன் தரவும் வெளியேறாது** — prompts இல்லை, replies இல்லை, டூல் arguments இல்லை, கோப்பு உள்ளடக்கம் இல்லை அல்லது log lines இல்லை. நீங்கள் இணைக்கும்போது, snapshot உங்கள் மெஷினை ஒருபோதும் விட்டு வெளியேறாத key-யுடன் end-to-end encrypted செய்யப்படுகிறது, மேலும் உங்கள் browser-இல் decrypt செய்யப்படுகிறது. ஒரு node-க்கு key இல்லையென்றால், upload plain text-இல் அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படுகிறது, மேலும் எந்த server பதிலும் அதை மாற்ற முடியாது.

நீங்கள் இணைப்பதற்கு முன் இயல்பாக இரண்டு விஷயங்கள் இயங்கும், இரண்டும் opt-out மற்றும் செஷன் தரவைச் சுமக்காதவை: அநாமதேய நிறுவல் பிங் மற்றும் PyPI-க்கு எதிரான பதிப்பு சரிபார்ப்பு. இயல்புநிலை நிறுவல் ஒரு தொடக்க பேனர் வரிக்காக உங்கள் பொது IP-ஐயும் ஒருமுறை தேடுகிறது. ஒவ்வொரு இலக்கும், அது என்ன சுமக்கிறது, மற்றும் அதை எப்படி அணைப்பது என்பது [docs/EGRESS.md](docs/EGRESS.md)-இல் பட்டியலிடப்பட்டுள்ளது; சொந்தமாக-ஹோஸ்ட் செய்யப்பட்ட, மறுவழிநடத்தப்பட்ட மற்றும் air-gapped நிறுவல்கள் எந்த விருப்ப outbound அழைப்பையும் செய்யாது.

Decryption நாங்கள் உங்களுக்கு வழங்கும் குறியீட்டில், உங்கள் browser-இலேயே நடக்கிறது. அது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள் சரிபார்க்கக்கூடிய ஒன்று. உங்கள் key-ஐத் தொடும் ஒவ்வொரு வரியும் ஒரே படிக்கக்கூடிய கோப்பில் உள்ளது, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது wheel-க்குள் அனுப்பப்பட்டு, Subresource Integrity hash-உடன் pin செய்யப்பட்டு, அப்படியே சேவை செய்யப்படுகிறது. browser நாங்கள் வெளியிட்டதையே இயக்குகிறது என்பதை உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

இது எதை நிரூபிக்கவில்லை: கோப்பை லோட் செய்யும் பக்கத்தை நாங்கள் வழங்குகிறோம், எனவே நாங்கள் வேறு பக்கத்தை வழங்கக்கூடும். Integrity hashes உங்களை ஒரு சமரசம் செய்யப்பட்ட CDN-இலிருந்து பாதுகாக்கும், விற்பனையாளரிடமிருந்து அல்ல. நீங்கள் பெறுவது என்னவென்றால், எந்த மாற்றமும் வேண்டுமென்றே செய்யப்பட்டதாகவும், பக்க மூலத்தில் தெரியும்படியாகவும், யாரும் பெறக்கூடிய PyPI-இலுள்ள artifact-இலிருந்து வேறுபட்டதாகவும் இருக்க வேண்டும். சொந்தமாக-ஹோஸ்ட் செய்வது அல்லது லோக்கல்-மட்டும் நிலையில் இருப்பது இந்த சார்பை முற்றிலும் நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பின்னர்: clawmetry
```

அல்லது ஒற்றை-லைன்: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows-இல் Python 3.8+ தேவை, மேலும் அதே மெஷினில் குறைந்தது ஒரு ஏஜென்ட் runtime தேவை. Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

அல்லது ஏஜென்டையே உங்களுக்காக அதை அமைக்க அனுமதிக்கவும். [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) skill Claude Code, Codex, Cursor, Gemini CLI, Copilot அல்லது OpenCode-க்கு ClawMetry-ஐ நிறுவவும், மெஷினில் உள்ள ஏஜென்ட்கள் என்ன செய்கின்றன மற்றும் செலவழிக்கின்றன என்பதைப் புகாரளிக்கவும், கோரிக்கையின் பேரில் ஒரு செஷனை நிறுத்தவும், மற்றும் அபாயகரமான டூல் அழைப்புகளை அங்கீகாரத்திற்காக நிறுத்தி வைக்கவும் கற்பிக்கிறது:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ஆவணங்கள்

| | |
|---|---|
| [Runtime இணக்கத்தன்மை](docs/compatibility.md) | ஒவ்வொரு adapter-ம் என்ன படிக்கிறது, மற்றும் ஒரு runtime-ஐ எப்படி சேர்ப்பது |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ப்ரொவைடர்-வாரியான windows, compaction vs overflow, runtime-வாரியான coverage |
| [Overhead](docs/OVERHEAD.md) | instrumentation-இன் செலவு, அளவிடப்பட்டது, அதை மறுஉருவாக்கம் செய்யும் harness-உடன் |
| [Entitlements](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, phone approvals |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | traces-ஐ எங்கும் export செய்யவும், எதிலிருந்தும் OTLP-ஐ ingest செய்யவும் |
| [உங்கள் சொந்த ஏஜென்டைக் கொண்டு வாருங்கள்](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain முழுவதுமாக, இயங்கக்கூடிய உதாரணங்களுடன் |
| [SDK கண்காணிப்பு](docs/SDK_TRACKING.md) | நீங்களே கட்டமைத்த ஏஜென்ட்களுக்கான செலவு பங்கீடு |
| [Chat channels](docs/CHANNELS.md) | Flow-இல் காட்டப்படும் chat adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [கட்டமைப்பு](ARCHITECTURE.md) · [வளர்ச்சி](docs/DEVELOPMENT.md) | உள்ளே இது எப்படி வேலை செய்கிறது; மூலத்திலிருந்து இயக்குதல் |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் desktop-open pings, மற்றும் அவற்றை எப்படி அணைப்பது |

## திரைக்காட்சிகள்

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான மெஷினிலிருந்து, read-only ஆக, எதுவும் விதைக்கப்படாமல் எடுக்கப்பட்டது.

**ஏதோ தவறு நடக்கும்போது அது உங்களுக்குச் சொல்கிறது, என்ன நடந்தது என்பதை மட்டும் அல்ல.**
மேலே இரண்டு anomaly banners: தினசரி சராசரியை விட 7 மடங்கு அதிகமான செலவு, மற்றும் 4.2x செலவு spike. அவற்றுக்குக் கீழே, சமீபத்திய 667 செஷன்களில் 324 waste சிக்னலைச் சுமந்து, காரணம் வாரியாகப் பட்டியலிடப்பட்டுள்ளது.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கு சென்றது என்பதை ஒவ்வொரு window-இலும் இது உங்களுக்குக் காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, ஒவ்வொன்றுக்கும் அதற்குப் பின்னால் உள்ள டோக்கன்களுடனும் உங்கள் subscription ஏற்கெனவே எவ்வளவு கவர் செய்கிறது என்பதுடனும். அதற்குக் கீழே, சுமார் $1,128/மாதம் மீட்கக்கூடியதாகவும், $17,256/மாதம் ஏற்கெனவே cache reuse மூலம் சேமிக்கப்பட்டதாகவும் பட்டியலிடப்பட்டுள்ளது.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு செய்தி எப்படி பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
நேரடி flow வரைபடம்: நீங்கள், அது வந்த சேனல், gateway, இப்போது பதிலளிக்கும் மாடல், மற்றும் அது அணுகிய ஒவ்வொரு டூலும். வேலை அவற்றின் வழியாக நகரும்போது நோட்கள் ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**மெஷினில் உள்ள ஒவ்வொரு ஏஜென்டும், ஒரே அட்டவணையில்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் ஆயுட்காலம் முழுவதும் அதன் செலவு என்ன, அது கடைசியாக எப்போது காணப்பட்டது, யாருக்குச் சொந்தமானது, மற்றும் ஒரு subscription பில்லை கவர் செய்கிறதா என்பது. இங்கே 14 ஏஜென்ட்கள், 3 செஷன்கள் வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு டர்னின் நேரமும் பணமும் எங்கு சென்றது என்பதை இது டூல் வாரியாகக் காட்டுகிறது.**
ஒரு உண்மையான செஷனின் ஒரு டர்ன்: 11 டூல்கள், 11.2 நிமிடங்களில், $1.16-க்கு. ஒவ்வொரு Bash அழைப்பும் மாடல் அழைப்பும் timeline-இல் அதன் சொந்த பட்டையைப் பெறுகிறது, எனவே 4.1 நிமிடங்கள் ஓடிய கட்டளையும் 226ms ஓடியதும் ஒரே பார்வையில் வேறுபடுத்தி அறியப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை மதிப்பிடுகிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக முடிந்தன, 2 கடினமானவை $48.57 செலவழித்தன, மற்றும் மதிப்பிட போதிய செயல்பாடு இல்லாத ரன்கள் வெற்றிகளாக எண்ணப்படுவதற்குப் பதிலாக தரப்படுத்தலிலிருந்து விடுபடுகின்றன. ஒவ்வொரு கடினமான ரன்னும் அதன் trace-க்கு இணைக்கிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**context window ஏன் தொடர்ந்து நிரம்புகிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய டர்னில் 1M-டோக்கன் window-இல் 715K, 83.3% உச்சம், 4 compactions, அனைத்தும் overflow-இல் அல்லாமல் proactive ஆக fire ஆனது, மேலும் அதற்குப் பின்னால் உள்ள ஒவ்வொரு டர்னின் பயன்பாடும்.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
built-in detectors நிறுவலிலிருந்து ஆன்: ஏஜென்ட் அமைதியானது, telemetry feed நின்றது, செலவு spike, டோக்கன் burst, errors அதிகரிப்பு, error spike, பட்ஜெட் threshold, threat signature match, security tool கண்டுபிடிப்பு, security posture மாற்றம். உங்கள் சொந்த விதிகள் மேலதிகமாக விருப்பமானவை.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**அபாயகரமான அழைப்பை நிறுத்தி வைப்பது opt-in, மேலும் ஆஃப் ஆக அனுப்பப்படுகிறது.**
Recursive deletes, force pushes, sudo, secrets, package நிறுவல்கள் மற்றும் outbound அழைப்புகள் ஒவ்வொன்றும் நீங்கள் ஆன் செய்யக்கூடிய ஒரு விதியைப் பெறுகின்றன. நீங்கள் அதைச் செய்யும் வரை, ClawMetry கண்காணிக்கிறது, எதையும் மாற்றாது. ஒன்று ஆன் செய்யப்பட்டதும், பொருந்தும் அழைப்புகள் இங்கே (அல்லது உங்கள் ஃபோனில்) approve அல்லது deny-க்காக காத்திருக்கும்.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

மேலும், runtime வாரியாக: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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

MIT · [@vivekchand](https://github.com/vivekchand) ஆல் உருவாக்கப்பட்டது · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
