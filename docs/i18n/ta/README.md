<!-- i18n-src:dc34072b2955 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **23 AI ஏஜென்ட் ரன்டைம்களுக்கான** நேரடி (real-time) கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 19. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை படிக்க:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. அனைத்தையும் தானாக கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும். கட்டமைப்பு தேவையில்லை: நீங்கள் ஏற்கெனவே வைத்திருக்கும் ஏஜென்ட் ரன்டைம்களை அது கண்டறிந்து, அவற்றை படிக்க-மட்டும் (read-only) அணுகி, அவை இயங்கும் விதத்தில் எதையும் மாற்றாது.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

**ஓபன் சோர்ஸ் ஆப்பில் இலவசம்:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**கட்டணத் திட்டத்தில்:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

ஒவ்வொரு ரன்டைமிற்கும் ஒரே டாஷ்போர்டு கிடைக்கும். பலவற்றை ஒரே நேரத்தில் இயக்கினால், தலைப்புப்பட்டியிலுள்ள சுவிட்சர் ஒவ்வொரு தாவலையும் அவற்றில் ஒன்றுக்கு மறு-நோக்கம் செய்யும்.

ஒரு SDK-யில் உங்கள் சொந்த ஏஜென்டை உருவாக்கினீர்களா? இன்டர்செப்டர் அதன் LLM அழைப்புகளையும் கண்காணிக்கும். பார்க்க [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## உங்களுக்குக் கிடைப்பவை

- **அமர்வுகள் & டிரான்ஸ்கிரிப்ட்கள் (Sessions & transcripts)**: ஒவ்வொரு ஏஜென்டும் என்ன செய்தது, ஒவ்வொரு முறையாக, ரீப்ளேயுடன்
- **செலவு & டோக்கன்கள் (Cost & tokens)**: ரன்டைம், மாடல், அமர்வு மற்றும் நாள் வாரியாக, முரண்பாட்டு (anomaly) குறிகளுடன்
- **ஃப்ளோ (Flow)**: சேனல்கள், மாடல்கள் மற்றும் கருவிகள் வழியாக செல்லும் செய்திகளின் நேரடி வரைபடம்
- **பிரெயின் (Brain)**: நடக்கும் போதே தர்க்க மற்றும் கருவி-அழைப்பு நிகழ்வு ஸ்ட்ரீம்
- **நினைவகம் & திறன்கள் (Memory & skills)**: ஒவ்வொரு ரன்டைமும் உண்மையில் லோட் செய்த கோப்புகள் மற்றும் திறன்கள்
- **ஆரோக்கியம் & பதிவுகள் (Health & logs)**: டிஸ்க், நினைவகம், பிழை விகிதங்கள், rate limits, நேரடி பதிவு ஸ்ட்ரீம்
- **எச்சரிக்கைகள் (Alerts)**: பட்ஜெட் வரம்புகள், பிழை எழுச்சிகள், ஏஜென்ட்-ஆஃப்லைன், Slack, Discord, PagerDuty, Telegram, மின்னஞ்சலுக்கு அனுப்பப்படும்
- **அனுமதிகள் (Approvals)**: அபாயகரமான கருவி அழைப்புகளை அவை இயங்குவதற்கு *முன்* இடைநிறுத்தி, உங்கள் மொபைலிலிருந்தே அனுமதி வழங்கவும் ([எப்படி](docs/APPROVALS.md))

## விலை நிர்ணயம்

| திட்டம் | எதை உள்ளடக்கியது | விலை |
|---|---|---|
| **இலவசம்** | OpenClaw + NVIDIA NemoClaw, முழு டாஷ்போர்டு, உள்ளூர் மட்டும் | $0 |
| **ஸ்டார்ட்டர்** | மேலே உள்ள மற்ற அனைத்து ரன்டைம்களும், fleet பார்வை, cloud sync | மாதத்திற்கு $9 / node |
| **Pro** | ஸ்டார்ட்டர் + நிர்வாகம் (governance): அனுமதிகள், கருவி-அபாய கொள்கைகள், மதிப்பீடுகள் (evals), முரண்பாடு கண்டறிதல், செலவு மேம்படுத்தி, OTel எக்ஸ்போர்ட் | மாதத்திற்கு $19 / node |

வருடாந்திரத் திட்டங்கள், Enterprise மற்றும் தற்போதைய எண்கள் இங்கு உள்ளன:
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. சொந்தமாக ஹோஸ்ட் செய்யப்பட்ட உரிமப் (license) சாவிகள் cloud இல்லாமலேயே வேலை செய்யும் (`clawmetry license`). துல்லியமான இலவச/கட்டணப் பிரிவு
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) இல் உள்ளது.

## உங்கள் தரவு உங்கள் கணினியிலேயே இருக்கும்

ClawMetry உள்ளூர் அமர்வுக் கோப்புகளையும் பதிவுகளையும் படிக்கும். நீங்கள் `clawmetry connect` ஐ இயக்காத வரை உங்கள் கணினியிலிருந்து எதுவும் வெளியேறாது. அப்படி இயக்கினாலும் கூட, ஸ்னாப்ஷாட் உங்கள் கணினியை விட்டு வெளியேறாத சாவியுடன் எண்ட்-டு-எண்ட் என்க்ரிப்ட் செய்யப்பட்டு, உங்கள் பிரவுசரிலேயே டிக்ரிப்ட் செய்யப்படும்.

## நிறுவல்

```bash
pip install clawmetry     # பின்னர்: clawmetry
```

அல்லது ஒரே-வரி கட்டளை: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux அல்லது Windows இல் Python 3.8+ தேவை, மேலும் அதே கணினியில் குறைந்தது ஒரு ஏஜென்ட் ரன்டைம் இருக்க வேண்டும். Docker வழிமுறைகள்: [docs/DOCKER.md](docs/DOCKER.md).

## ஆவணங்கள்

| | |
|---|---|
| [ரன்டைம் இணக்கத்தன்மை](docs/compatibility.md) | ஒவ்வொரு அடாப்டரும் என்ன படிக்கிறது, மற்றும் ஒரு ரன்டைமை எப்படி சேர்ப்பது |
| [Entitlements](docs/ENTITLEMENTS.md) | இலவசம் vs கட்டணம், டையர் மேட்ரிக்ஸ், லைசென்ஸ் CLI |
| [அனுமதிகள் & கொள்கைகள்](docs/APPROVALS.md) | இயக்கத்திற்கு முந்தைய கட்டுப்பாடு, அபாய மதிப்பீடு, மொபைல் அனுமதிகள் |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | எங்கும் trace-களை எக்ஸ்போர்ட் செய்யவும், எதிலிருந்தும் OTLP-ஐ இங்கெஸ்ட் செய்யவும் |
| [SDK கண்காணிப்பு](docs/SDK_TRACKING.md) | நீங்களே உருவாக்கிய ஏஜென்ட்களுக்கான செலவு ஒதுக்கீடு |
| [சாட் சேனல்கள்](docs/CHANNELS.md) | Flow இல் காட்டப்படும் சாட் அடாப்டர்கள் |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | சாண்ட்பாக்ஸ் செய்யப்பட்ட NVIDIA NemoClaw அமைப்புகள் |
| [Docker](docs/DOCKER.md) | இமேஜ், compose, volume mounts |
| [கட்டமைப்பு (Architecture)](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | இது உள்ளே எப்படி வேலை செய்கிறது; சோர்ஸிலிருந்து இயக்குதல் |
| [Telemetry](docs/TELEMETRY.md) | அநாமதேய நிறுவல் மற்றும் டெஸ்க்டாப்-ஓபன் பிங்குகள், அவற்றை எப்படி முடக்குவது |

## ஸ்கிரீன்ஷாட்கள்

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **கண்ணோட்டம் (Overview)**: டோக்கன்கள், அமர்வுகள், ஆரோக்கியம் | **பிரெயின் (Brain)**: நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம் |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **செலவு (Cost)**: மாடல் மற்றும் அமர்வு வாரியாக | **அனுமதிகள் (Approvals)**: அபாயகரமான கருவி அழைப்புகளைக் கட்டுப்படுத்துதல் |

ரன்டைம் வாரியாக மேலும்: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## நட்சத்திர வரலாறு (Star History)

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
