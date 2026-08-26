<!-- i18n-src:c111f32e69a5 -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **26 AI એજન્ટ રનટાઇમ્સ** માટે રિયલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 22. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આને આમાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું ઓટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. શૂન્ય કન્ફિગ: તે તમારી પાસે પહેલેથી જ રહેલા એજન્ટ રનટાઇમ્સ શોધી કાઢે છે, તેમને ફક્ત વાંચે છે, અને તેઓ કેવી રીતે ચાલે છે તેમાં કંઈ પણ બદલતું નથી.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 26 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં મફત:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાનમાં:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એ જ ડેશબોર્ડ મળે છે. એકસાથે અનેક ચલાવો અને હેડર સ્વિચર દરેક ટેબને તેમાંથી કોઈ એક પર ફરીથી સ્કોપ કરી દેશે.

તમારો પોતાનો એજન્ટ SDK પર બનાવ્યો છે? ઇન્ટરસેપ્ટર તેના LLM કૉલ્સ પણ ટ્રેક કરે છે. જુઓ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સ્ક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન બાય ટર્ન, રિપ્લે સાથે
- **ખર્ચ અને ટોકન્સ**: રનટાઇમ, મોડેલ, સેશન અને દિવસ પ્રમાણે, અસંગતતાના ફ્લેગ સાથે
- **Flow**: ચેનલો, મોડેલો અને ટૂલ્સમાંથી પસાર થતા મેસેજોનું લાઇવ ડાયાગ્રામ
- **Brain**: રિઝનિંગ અને ટૂલ-કૉલ ઇવેન્ટ સ્ટ્રીમ, જેમ જેમ થાય તેમ
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર લોડ કરેલી ફાઇલો અને સ્કિલ્સ
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર રેટ, રેટ લિમિટ્સ, લાઇવ લોગ સ્ટ્રીમ
- **અલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થયેલા
- **એપ્રૂવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલવા *પહેલાં* થોભાવો અને તમારા ફોનથી મંજૂર કરો ([કેવી રીતે](docs/APPROVALS.md))

## પ્રાઇસિંગ

| પ્લાન | શું આવરી લે છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, પૂરું ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરના બાકીના બધા રનટાઇમ્સ, ફ્લીટ વ્યુ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + ગવર્નન્સ: એપ્રૂવલ્સ, ટૂલ-રિસ્ક પોલિસીઝ, ઇવલ્સ, અસંગતતા શોધ, કોસ્ટ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન્સ, Enterprise અને હાલના આંકડા **[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર ઉપલબ્ધ છે. સેલ્ફ-હોસ્ટેડ લાયસન્સ કીઓ ક્લાઉડ વગર કામ કરે છે (`clawmetry license`). ફ્રી/પેઇડનું ચોક્કસ વિભાજન [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ વાંચે છે. જ્યાં સુધી તમે `clawmetry connect` ચલાવો નહીં ત્યાં સુધી કંઈ પણ તમારા બોક્સની બહાર જતું નથી. ત્યારે પણ સ્નેપશોટ એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે, એવી કીથી જે તમારા મશીનમાંથી ક્યારેય બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઇનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux અથવા Windows પર Python 3.8+ જોઈએ, અને એ જ મશીન પર ઓછામાં ઓછું એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

## દસ્તાવેજો

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | દરેક એડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવો |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, ટિયર મેટ્રિક્સ, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન એપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે ત્યાંથી OTLP ઇનજેસ્ટ કરો |
| [SDK tracking](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટ્સ માટે ખર્ચનું એટ્રિબ્યુશન |
| [Chat channels](docs/CHANNELS.md) | Flowમાં દેખાતા ચેટ એડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ્ડ NVIDIA NemoClaw સેટઅપ્સ |
| [Docker](docs/DOCKER.md) | ઇમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ્સ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | અંદર તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [Telemetry](docs/TELEMETRY.md) | અનામી ઇન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: ટોકન્સ, સેશન્સ, હેલ્થ | **એજન્ટ** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: મોડેલ અને સેશન પ્રમાણે | **Approvals**: જોખમી ટૂલ કૉલ્સને ગેટ કરો |

વધુ, દરેક રનટાઇમ પ્રમાણે: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## લાયસન્સ

MIT · [@vivekchand](https://github.com/vivekchand) દ્વારા બનાવેલ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
