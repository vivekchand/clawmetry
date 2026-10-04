<!-- i18n-src:c99ac0512cae -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ஒரு ஏஜெண்ட் முன்னேற்றம் இல்லாமலே நூறு tool call-களைச் செய்யக்கூடும்.** ClawMetry
உங்கள் கோடிங் ஏஜெண்ட்கள் ஏற்கெனவே எழுதும் session கோப்புகளைப் படித்து, டைம்லைனையும்,
tool call-களையும், ரன்டைம் வெளிப்படுத்தும் டோக்கன் மற்றும் செலவு தரவு எதுவானாலும்
ஒரு தொகுப்பு பார்வையில் கொண்டு வருகிறது — இதனால் வேலை செய்யும் ஒரு நீண்ட ரன்னை,
சிக்கிக் கிடக்கும் ஒன்றிலிருந்து வேறுபடுத்த உங்களுக்கு முடியும்.

**33 AI ஏஜெண்ட் ரன்டைம்களுடன்** செயல்படுகிறது — Claude Code, OpenAI Codex, Hermes, OpenClaw மற்றும் 29 மேலும். உங்கள் முழு ஏஜெண்ட் fleet-க்கும் ஒரு dashboard. ([முழு பட்டியல்](SUPPORTED_RUNTIMES.txt), catalogue-இலிருந்து உருவாக்கப்பட்டது.)

> 🌐 **இதை இந்த மொழிகளில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே ஒரு கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாக கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். கட்டமைப்பு தேவையில்லை: உங்களிடம் ஏற்கெனவே
இருக்கும் ஏஜெண்ட் ரன்டைம்களைக் கண்டறிந்து, அவற்றை read-only ஆக படித்து, அவை இயங்கும்
விதத்தில் எதையும் மாற்றாது.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## நிறுவுவதற்கு முன்

| | |
|---|---|
| **இது என்ன செய்கிறது** | உங்கள் ஏஜெண்ட்கள் ஏற்கெனவே எழுதும் session கோப்புகளையும் logs-ஐயும் படிக்கிறது. SDK இல்லை, code மாற்றம் இல்லை, உங்கள் app-இல் instrumentation இல்லை. |
| **நீங்கள் என்ன காண்பீர்கள்** | Session டைம்லைன், tool-by-tool replay, டோக்கன் மற்றும் செலவு பிரிவு, மற்றும் trajectory சிக்னல்கள் (looping, மீண்டும் மீண்டும் தோல்வி) — ரன்டைம் வாரியாக. |
| **எது இலவசம்** | `pip install clawmetry` எந்த கணக்கோ, key-ஆ, network call-ஆ இல்லாமல் **OpenClaw, NVIDIA NemoClaw, Goose மற்றும் Qwen Code**-ஐ படிக்கிறது. மற்ற 28 — Claude Code, Codex, Cursor மற்றும் பிற — closed-source `clawmetry-pro` துணைப் பயன்பாட்டால் படிக்கப்படுகின்றன, இது 7-நாள் trial-உடனோ plan-உடனோ வருகிறது — சரியான பிரிவுக்கு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) பார்க்கவும். |
| **எப்படி தொடங்குவது** | `pip install clawmetry && clawmetry`, பிறகு localhost:8900-ஐ திறக்கவும். இந்த மெஷினில் இன்னும் ஏஜெண்ட்கள் இல்லையா? `clawmetry --sample` மூன்று லேபிளிடப்பட்ட செயற்கை session-களுடன் திறக்கும். |
| **உங்கள் மெஷினிலிருந்து என்ன வெளியே செல்கிறது** | `clawmetry connect` இயக்கும் வரை, எந்த session தரவும் இல்லை. இயல்பாகவே இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும் opt-out செய்யக்கூடியவை, இரண்டுமே session content எதையும் கொண்டு செல்வதில்லை: ஒரு அநாமதேய நிறுவல் ping மற்றும் ஒரு PyPI version check. ஒவ்வொரு இடமும் [docs/EGRESS.md](docs/EGRESS.md)-இல் பட்டியலிடப்பட்டுள்ளது, கருத்துகளைப் படிப்பதைக் காட்டிலும் wire capture-இலிருந்து மீண்டும் கட்டமைக்கப்பட்டது. |

நீங்கள் வெளியீட்டை மதிப்பிடுவதற்கு முன் தெரிந்துகொள்ள வேண்டிய இரண்டு வரம்புகள்: ரன்டைம்கள்
மிகவும் வேறுபட்ட தரவை வெளிப்படுத்துகின்றன (சில எந்த செலவையும் வெளியிடுவதில்லை —
[matrix](docs/compatibility.md) ஒவ்வொரு ரன்டைமுக்கும் எது என்று சொல்கிறது), மற்றும் ஒரு
செயலைக் கவனிப்பது அதைத் தடுக்க முடிவது போல் அல்ல ([ரன்டைம் வாரியாக எந்த கட்டுப்பாடுகள்
உண்மையானவை](docs/APPROVALS.md)).


## 33 ஏஜெண்ட் ரன்டைம்களுடன் செயல்படுகிறது

**திறந்த மூலத் தளத்தில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**கட்டணமுள்ள திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ஒவ்வொரு ரன்டைமும் அதே dashboard-ஐப் பெறுகிறது. பலவற்றை ஒரே நேரத்தில் இயக்கினால்,
header switcher ஒவ்வொரு tab-ஐயும் அவற்றில் ஒன்றிற்கு மீண்டும் scope செய்யும்.

ஒரு SDK-இல் உங்கள் சொந்த ஏஜெண்டைக் கட்டினீர்களா? interceptor அதன் LLM call-களையும்
கண்காணிக்கும். [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **Sessions & transcripts**: ஒவ்வொரு ஏஜெண்டும் என்ன செய்தது, turn வாரியாக, replay-உடன்
- **செலவு & டோக்கன்கள்**: ரன்டைம், மாடல், session மற்றும் நாள் வாரியாக, anomaly flags-உடன்
- **Flow**: channels, models மற்றும் tools மூலம் நகரும் செய்திகளின் live diagram
- **Brain**: reasoning மற்றும் tool-call நிகழ்வு stream, அது நடக்கும் போதே
- **Context blowout**: provider வாரியாக அளவிடப்பட்ட window பயன்பாடு, compaction vs forced overflow, மற்றும் நாங்கள் *பார்க்க முடியாதது* எது என்பதன் ரன்டைம் வாரியான வரைபடம் ([எப்படி](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: ஒவ்வொரு ரன்டைமும் உண்மையில் லோட் செய்த கோப்புகள் மற்றும் skills
- **Health & logs**: டிஸ்க், memory, error rates, rate limits, live log stream
- **Alerts**: budget caps, error spikes, agent-offline, Slack, Discord, PagerDuty, Telegram, Email-க்கு route செய்யப்படும்
- **Approvals**: ஆபத்தான tool call-களை அவை இயங்கு*முன்பே* நிறுத்தி, உங்கள் தொலைபேசியிலிருந்து approve செய்யவும் ([எப்படி](docs/APPROVALS.md))

## Context blowout, மற்றும் கவனிப்பதன் செலவு என்ன

எந்த ஏஜெண்ட்-ஒப்பீட்டு கருவியையும் நம்புவதற்கு முன் பதில் தெரிந்துகொள்ள வேண்டிய இரண்டு கேள்விகள்.

**ரன்டைம்களுக்கு இடையே context-window blowout-ஐ இது எப்படி கையாளுகிறது?**

ஒரு utilization சதவீதம், அது எதைப் பிரிக்கிறதோ அதை மட்டுமே உண்மையாக இருக்கும்.
ClawMetry நீங்கள் படித்து PR செய்யக்கூடிய [ஒரு table](clawmetry/context_windows.py)-இலிருந்து
provider வாரியாக window-ஐ அளவிடுகிறது, இது Anthropic, OpenAI, Google, xAI, DeepSeek,
Kimi, Qwen, Mistral, Llama மற்றும் GLM-ஐ உள்ளடக்கியது. இது 33 ரன்டைம்களையும் ஒரு
விற்பனையாளரின் அளவுகோலால் அளப்பதில்லை. இது முக்கியம்: Anthropic-இன் 200K-க்கு எதிராக
மதிப்பிடப்பட்ட 300K GPT-5 turn ">100%, blown" என்று படிக்கப்படும், ஆனால் உண்மையில் அது
GPT-5-இன் 400K-இல் 75% ஆகும். அதே அளவுகோல் உண்மையிலேயே overflow ஆன 130K DeepSeek
turn-ஐ வசதியான 65% ஆக மறைக்கும்.

ஒவ்வொரு window-உம் அதன் provenance-உடன் வருகிறது: `model_table`, `explicit_marker`,
`observed_floor`, அல்லது மாடலைத் தெரியாதபோது ஒரு நேர்மையான `default`. ஒரு guess-இல்
கட்டப்பட்ட gauge, ஒரு lookup-இல் கட்டப்பட்டதைப் போன்ற அதே authority-உடன் ஒருபோதும்
render ஆகாது.

ClawMetry சில ரன்டைம்களில் மட்டுமே compaction நிகழ்வுகளைக் காண முடியும். எனவே
`GET /api/context-coverage`, ரன்டைம் வாரியாக, **`0` என்பது "சுத்தமாக ஓடியது" என்று
அர்த்தமா அல்லது "நாங்கள் குருடராக இருக்கிறோம்" என்று அர்த்தமா** என்பதைப் புகாரளிக்கிறது.
உண்மையில் குருடு என்று பொருள்படும் `0`, அதையே சொல்லும். [முழு விவரம்](docs/CONTEXT_BLOWOUT.md)

**Instrumentation-இன் செலவு என்ன?**

| Path | உங்கள் ஏஜெண்டுக்குச் சேர்க்கப்பட்டது | இயல்பாகவா? |
|---|---|---|
| Session-file tailing (அனைத்து 33 ரன்டைம்களும்) | **0**. தனி process, உங்கள் ஏஜெண்டில் ClawMetry code இல்லை | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | ஒவ்வொரு LLM call-க்கும் **+0.44 ms**, அல்லது 5s call-இல் 0.009% | off |
| Pre-tool hook gate (warm cache) | gated tool call ஒன்றுக்கு **+44 ms**, 36 ms interpreter floor-க்கு மேல் | off |
| Enforcement proxy | ஒவ்வொரு LLM call-க்கும் **+9.7 ms** | off |

Daemon host செலவு: ingest **2,762 events/sec**, டிஸ்க்கில் **710 bytes/event**
(100k events-க்கு 67.7 MB), மற்றும் busy நிறுவலில் நிலையான **~12% of one core**.
அந்த கடைசி எண், நாங்களே குறிப்பிட்ட 5-10% budget-ஐ விட அதிகம், எனவே அது பக்கத்தை
விட்டு விடப்படாமல், தொடர வேண்டிய ஒரு bug ஆக வெளியிடப்படுகிறது.

Apple M2 Pro-இல் `benchmarks/overhead.py` மூலம் அளக்கப்பட்டது. இந்த harness ஒவ்வொரு
condition-ஐயும் தனித்தனி process-இல் இயக்கி, அவற்றின் வரிசையை மாற்றி, **rounds
அவற்றின் sign-இல் உடன்படாதபோது ஒரு எண்ணை print செய்ய மறுக்கிறது**. உங்கள் சொந்த
மெஷினில் ஒரு நிமிடத்தில் அதை இயக்கவும்:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook gates மற்றும் enforcement proxy உட்பட ஒவ்வொரு path-உம் அளக்கப்படுகிறது, மற்றும்
இந்த harness CI-இல் Linux, macOS மற்றும் Windows-இல் இயங்குகிறது. தெரிந்துகொள்ள
வேண்டிய இரண்டு முடிவுகள்: Windows-இல் proxy, Linux-ஐ விட ஏழு மடங்கு அதிகமாக
செலவாகிறது, மற்றும் daemon தற்போது நாங்களே குறிப்பிட்ட 5-10% budget-ஐ விட, ஒரு
core-இன் சுமார் 12%-ஐ நிலையாகச் சுமக்கிறது. raw JSON, முறை, இன்னும் அளவிடப்படாதது
எது என்பது [docs/OVERHEAD.md](docs/OVERHEAD.md)-இல் உள்ளது.

## விலை நிர்ணயம்

| திட்டம் | இது எதை உள்ளடக்குகிறது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, முழு dashboard, local மட்டும் | $0 |
| **Starter** | மேலே உள்ள மற்ற ஒவ்வொரு ரன்டைமும், fleet view, cloud sync | node ஒன்றுக்கு மாதம் $9 |
| **Pro** | Starter + control மற்றும் evaluation: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | node ஒன்றுக்கு மாதம் $19 |

ஆண்டு திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் **[clawmetry.com/pricing](https://clawmetry.com/pricing)**-இல்
உள்ளன. Self-hosted license keys cloud இல்லாமலே வேலை செய்யும் (`clawmetry license`).
சரியான இலவச/கட்டண பிரிவு [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)-இல் உள்ளது.

## உங்கள் தரவு உங்கள் மெஷினில் இருக்கும்

ClawMetry local session கோப்புகள் மற்றும் logs-ஐ படிக்கிறது. **நீங்கள்
`clawmetry connect`-ஐ இயக்கும் வரை, எந்த session தரவும் உங்கள் box-இலிருந்து
வெளியேறாது** — prompts, replies, tool arguments, file contents அல்லது log
lines எதுவும் இல்லை. நீங்கள் connect செய்தால், snapshot உங்கள் மெஷினை விட்டு
ஒருபோதும் வெளியேறாத ஒரு key-உடன் end-to-end encrypt செய்யப்பட்டு, உங்கள்
browser-இல் decrypt செய்யப்படுகிறது. ஒரு node-க்கு key இல்லையென்றால், upload
தெளிவாக அனுப்பப்படுவதற்குப் பதிலாக தவிர்க்கப்படும், எந்த server பதிலும் அதை
மாற்ற முடியாது.

நீங்கள் connect செய்வதற்கு முன் இயல்பாகவே இரண்டு விஷயங்கள் இயங்குகின்றன, இரண்டும்
opt-out செய்யக்கூடியவை, இரண்டுமே session தரவைக் கொண்டு செல்வதில்லை: ஒரு அநாமதேய
நிறுவல் ping மற்றும் PyPI-க்கு எதிரான ஒரு version check. ஒரு இயல்புநிலை நிறுவல்,
startup banner வரிக்காக உங்கள் public IP-ஐ ஒரு முறை தேடுகிறது. ஒவ்வொரு இடமும்,
அது என்ன கொண்டு செல்கிறது, அதை எப்படி நிறுத்துவது என்பது
[docs/EGRESS.md](docs/EGRESS.md)-இல் பட்டியலிடப்பட்டுள்ளது; self-hosted,
repointed மற்றும் air-gapped நிறுவல்கள் தேர்ச்சி அடிப்படையிலான outbound
calls எதையும் செய்யாது.

Decryption உங்கள் browser-இல், நாங்கள் உங்களுக்கு வழங்கும் code-இல் நடக்கிறது.
இது முன்பு ஒரு வாக்குறுதியாக இருந்தது; இப்போது அது நீங்கள் சரிபார்க்கக்கூடிய
ஒன்று. உங்கள் key-ஐத் தொடும் ஒவ்வொரு வரியும் ஒரு படிக்கக்கூடிய கோப்பில் உள்ளது,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), இது wheel-க்கு
உள்ளேயே ஷிப் செய்யப்பட்டு, அப்படியே வழங்கப்படுகிறது, ஒரு Subresource Integrity
hash-உடன் பின் செய்யப்பட்டுள்ளது. browser நாங்கள் வெளியிட்டதை இயக்குகிறது என்பதை
உறுதிப்படுத்த:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

இது நிரூபிக்காதது என்ன: கோப்பை ஏற்றும் பக்கத்தை நாங்கள் வழங்குகிறோம், எனவே
நாங்கள் வேறு பக்கத்தை வழங்கலாம். Integrity hashes உங்களை ஒரு பழுதடைந்த CDN-இலிருந்து
பாதுகாக்கின்றன, விற்பனையாளரிடமிருந்து அல்ல. நீங்கள் பெறுவது என்னவெனில், எந்த
மாற்றீடும் வேண்டுமென்றே செய்யப்பட்டதாகவும், page source-இல் தெரியும்படியாகவும்,
யாரும் fetch செய்யக்கூடிய PyPI-இல் உள்ள artifact-இலிருந்து வேறுபட்டதாகவும்
இருக்க வேண்டும். Self-hosting அல்லது local-only ஆக இருப்பது இந்த சார்பை
முற்றிலும் நீக்குகிறது.

## நிறுவல்

```bash
pip install clawmetry     # பிறகு: clawmetry
```

அல்லது ஒரே-வரி: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows-இல் Python 3.8+ தேவை, மற்றும் அதே மெஷினில் குறைந்தது
ஒரு ஏஜெண்ட் ரன்டைம் தேவை. Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

அல்லது ஏஜெண்டையே அதை உங்களுக்காக அமைக்க விடுங்கள். [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
skill, Claude Code, Codex, Cursor, Gemini CLI, Copilot அல்லது OpenCode-க்கு
ClawMetry-ஐ நிறுவவும், மெஷினில் உள்ள ஏஜெண்ட்கள் என்ன செய்கின்றன, எவ்வளவு செலவு
செய்கின்றன என்பதைப் புகாரளிக்கவும், கோரிக்கையின் பேரில் ஒரு session-ஐ நிறுத்தவும்,
ஆபத்தான tool call-களை approval-க்காக நிறுத்தி வைக்கவும் கற்றுத் தருகிறது:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ஆவணங்கள்

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ஒவ்வொரு adapter-உம் என்ன படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Provider வாரியான windows, compaction vs overflow, ரன்டைம் வாரியான coverage |
| [Overhead](docs/OVERHEAD.md) | Instrumentation-இன் செலவு என்ன, அளக்கப்பட்டது, அதை மீண்டும் உருவாக்க harness-உடன் |
| [Entitlements](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, தொலைபேசி approvals |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces-ஐ எங்கும் export செய்யவும், OTLP-ஐ எதிலிருந்தும் ingest செய்யவும் |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain முடிவு வரை, இயங்கக்கூடிய எடுத்துக்காட்டுகளுடன் |
| [SDK tracking](docs/SDK_TRACKING.md) | நீங்களே கட்டிய ஏஜெண்ட்களுக்கான செலவு attribution |
| [Chat channels](docs/CHANNELS.md) | Flow-இல் காட்டப்படும் chat adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw அமைவுகள் |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | இது உள்ளே எப்படி வேலை செய்கிறது; source-இலிருந்து இயக்குவது |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் desktop-open pings, அவற்றை எப்படி நிறுத்துவது |

## Screenshots

கீழே உள்ள ஒவ்வொரு எண்ணும் ஒரு உண்மையான மெஷினிலிருந்து, read-only ஆக, எதுவும்
seed செய்யப்படாமல் எடுக்கப்பட்டது.

**எதுவும் தவறாக இருக்கும்போது அது உங்களுக்குச் சொல்கிறது, என்ன நடந்தது என்பது
மட்டுமல்ல.** மேலே இரண்டு anomaly banners: daily average-ஐ விட 7x செலவு
இயங்குகிறது, மற்றும் 4.2x செலவு spike. அவற்றின் கீழே, சமீபத்திய 667 sessions-இல்
324, காரணம் வாரியாக பிரிக்கப்பட்ட ஒரு waste signal-ஐ சுமந்து செல்கின்றன.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**பணம் எங்கே சென்றது என்பதை, ஒவ்வொரு window-இலும் இது உங்களுக்குக் காட்டுகிறது.**
இன்று $252.47, இந்த வாரம் $513.15, இந்த மாதம் $1,312.92, அதன் பின்னணியில் உள்ள
டோக்கன்களுடனும், உங்கள் subscription அதில் எவ்வளவு ஏற்கெனவே கவர் செய்கிறது
என்பதுடனும். அதற்குக் கீழே, சுமார் $1,128/மாதம் recoverable ஆக பிரிக்கப்பட்டது
மற்றும் cache மறு பயன்பாட்டால் ஏற்கெனவே சேமிக்கப்பட்ட $17,256/மாதம்.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ஒரு செய்தி எப்படி பதிலாக மாறுகிறது என்பதை இது வரைகிறது.**
Live flow diagram: நீங்கள், அது வந்த channel, gateway, இப்போது பதிலளிக்கும்
model, மற்றும் அது அடைந்த ஒவ்வொரு tool-உம். வேலை அவற்றின் வழியாக நகரும்போது
nodes ஒளிரும்.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**மெஷினில் உள்ள ஒவ்வொரு ஏஜெண்டும், ஒரு table-இல்.**
அது என்ன இயக்குகிறது, கடந்த 24 மணி நேரத்திலும் அதன் வாழ்நாள் முழுவதும் அதன்
செலவு என்ன, அது எப்போது கடைசியாகக் காணப்பட்டது, அதை யார் வைத்திருக்கிறார்கள்,
மற்றும் ஒரு subscription பில்-ஐ கவர் செய்கிறதா. இங்கே 14 ஏஜெண்ட்கள், 3 sessions
வேலை செய்கின்றன, 13 அமைதியாக உள்ளன.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ஒரு turn-இன் நேரமும் பணமும் எங்கே சென்றது என்பதை, tool வாரியாக இது காட்டுகிறது.**
ஒரு உண்மையான session-இன் ஒரு turn: 11.2 நிமிடங்களில் $1.16-க்கு 11 tools.
ஒவ்வொரு Bash call-உம் model call-உம் timeline-இல் அதன் சொந்த bar-ஐப்
பெறுகிறது, எனவே 4.1 நிமிடங்கள் இயங்கிய கட்டளையும் 226ms இயங்கியதும் ஒரு பார்வையில்
வேறுபடுத்தப்படுகின்றன.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**இது வேலையை grade செய்கிறது, செலவை மட்டும் அல்ல.**
இந்த வாரம் ஒரு A: 54 பணிகள் சுத்தமாக முடிந்தன, 2 கரடுமுரடானவை $48.57 செலவாகின,
மற்றும் judge செய்ய போதுமான செயல்பாடு இல்லாத runs, வெற்றிகளாக கணக்கிடப்படுவதற்குப்
பதிலாக grade-இலிருந்து விடுபட்டுள்ளன. ஒவ்வொரு கரடுமுரடான run-உம் அதன் trace-க்கு
இணைக்கிறது.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**context window ஏன் தொடர்ந்து நிரம்பிக் கொண்டே இருக்கிறது என்பதை இது காட்டுகிறது.**
சமீபத்திய turn-இல் 1M-டோக்கன் window-இல் 715K, 83.3% peak, overflow-இல் அல்லாமல்
proactive ஆகவே தீப்பற்றிய 4 compactions, மற்றும் அதன் பின்னணியில் உள்ள ஒவ்வொரு
turn-இன் utilisation.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**நீங்கள் எதையும் கட்டமைக்காமலேயே கண்டறிதல் இயங்குகிறது.**
built-in detectors நிறுவலிலிருந்தே இயக்கத்தில் உள்ளன: ஏஜெண்ட் அமைதியானது, telemetry
feed நின்றது, செலவு spike, token burst, errors ஏறுகிறது, error spike, budget
threshold, threat signature match ஆனது, security tool கண்டுபிடிப்பு, security
posture மாறியது. உங்கள் சொந்த விதிகள் இதன் மேல் விருப்பத்தின் பேரில் உள்ளன.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ஆபத்தான call-ஐ நிறுத்தி வைப்பது விருப்பத்தின் பேரில், மற்றும் off ஆகவே ஷிப் ஆகிறது.**
Recursive deletes, force pushes, sudo, secrets, package installs மற்றும்
outbound calls ஒவ்வொன்றும் நீங்கள் on செய்யக்கூடிய ஒரு விதியைப் பெறுகின்றன.
நீங்கள் செய்யும் வரை, ClawMetry பார்த்துக் கொண்டிருக்கும், எதையும் மாற்றாது.
ஒன்று on ஆன பிறகு, பொருந்தும் calls, approve அல்லது deny செய்ய இங்கே (அல்லது
உங்கள் தொலைபேசியில்) காத்திருக்கும்.

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

MIT · [@vivekchand](https://github.com/vivekchand) ஆல் கட்டப்பட்டது · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
