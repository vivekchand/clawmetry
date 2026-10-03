<!-- i18n-src:c99ac0512cae -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ang isang agent ay kayang gumawa ng isandaang tool call nang walang anumang pag-unlad.** Binabasa ng ClawMetry
ang mga session file na isinusulat na ng mga coding agent mo, at ipinapasok ang timeline,
ang mga tool call at kung anumang token at cost data na ibinubunyag ng runtime sa isang
tanawin — para masabi mo kung aling mahabang takbo ang gumagana laban sa isang natigil lang.

Gumagana sa **33 AI agent runtime** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 29 pa. Isang dashboard para sa buong agent fleet mo. ([ang kumpletong listahan](SUPPORTED_RUNTIMES.txt), na nabuo mula sa catalogue.)

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Walang configuration. Awtomatikong natutuklasan ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900**. Walang configuration: hahanapin nito ang mga agent runtime
na mayroon ka na, babasahin ang mga ito sa mode na read-only, at hindi babaguhin kung paano sila tumatakbo.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bago ka mag-install

| | |
|---|---|
| **Ano ang gawain nito** | Binabasa ang mga session file at log na isinusulat na ng mga agent mo. Walang SDK, walang pagbabago sa code, walang instrumentation sa app mo. |
| **Ano ang makikita mo** | Session timeline, tool-by-tool replay, breakdown ng token at cost, at mga trajectory signal (looping, paulit-ulit na pagkabigo) — kada runtime. |
| **Ano ang libre** | Binabasa ng `pip install clawmetry` ang **OpenClaw, NVIDIA NemoClaw, Goose at Qwen Code** nang walang account, walang key, at walang network call. Ang iba pang 28 — Claude Code, Codex, Cursor at ang lahat ng natitira — ay binabasa ng closed-source na companion na `clawmetry-pro`, na dumarating kasama ang 7-araw na trial o isang plan — tingnan ang [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para sa eksaktong hati. |
| **Paano magsimula** | `pip install clawmetry && clawmetry`, pagkatapos buksan ang localhost:8900. Walang agent pa sa makinang ito? Bubuksan ng `clawmetry --sample` ang tatlong naka-label na synthetic session. |
| **Ano ang lumalabas sa makina mo** | Walang session data, maliban kung patakbuhin mo ang `clawmetry connect`. Dalawang bagay ang tumatakbo bilang default, pareho ay opt-out at wala sa mga ito ang may dalang session content: isang anonymous install ping at isang PyPI version check. Ang bawat destinasyon ay nakalista sa [docs/EGRESS.md](docs/EGRESS.md), na muling binuo mula sa isang wire capture sa halip na mula sa pagbasa ng mga comment. |

Dalawang limitasyon na dapat malaman mo bago husgahan ang output: ibinubunyag ng mga runtime ang
ibang-ibang data (ang ilan ay hindi naglalabas ng anumang cost — [ang matrix](docs/compatibility.md)
ang nagsasabi kung alin, kada runtime), at ang pag-obserba sa isang aksyon ay hindi pareho sa kakayahang
pigilan ito ([aling mga control ang totoo, kada runtime](docs/APPROVALS.md)).


## Gumagana sa 33 agent runtime

**Libre sa open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Sa bayad na plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Ang bawat runtime ay may parehong dashboard. Patakbuhin ang ilan nang sabay-sabay at ang header
switcher ay muling i-iskop ang bawat tab sa isa sa mga ito.

Gumawa ka ng sarili mong agent gamit ang SDK? Sinusubaybayan din ng interceptor ang mga LLM call nito.
Tingnan ang [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ano ang makukuha mo

- **Mga session at transcript**: ano ang ginawa ng bawat agent, turn by turn, kasama ang replay
- **Cost at token**: kada runtime, model, session at araw, kasama ang mga anomaly flag
- **Flow**: live diagram ng mga mensahe habang dumadaan sa mga channel, model at tool
- **Brain**: ang reasoning at tool-call event stream habang nangyayari ito
- **Context blowout**: window utilization na nakasize kada provider, compaction laban sa sapilitang overflow, kasama ang mapa kada runtime ng kung ano ang *hindi* natin makikita ([paano](docs/CONTEXT_BLOWOUT.md))
- **Memory at skills**: ang mga file at skill na talagang na-load ng bawat runtime
- **Health at logs**: disk, memory, error rate, rate limit, live log stream
- **Alerts**: budget cap, error spike, agent-offline, naka-route sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: i-pause ang mapanganib na tool call *bago* ito tumakbo at aprubahan mula sa telepono mo ([paano](docs/APPROVALS.md))

## Context blowout, at ang gastos ng pagmamasid

Dalawang tanong na dapat masagot bago ka magtiwala sa anumang agent-comparison tool.

**Paano nito hinahandle ang context-window blowout sa iba't ibang runtime?**

Ang isang utilization percentage ay tapat lamang hangga't tapat ang hinatian nito. Ang ClawMetry
ay nagsize ng window kada provider mula sa [isang table na mababasa at ma-PR mo](clawmetry/context_windows.py),
na sumasaklaw sa Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama at GLM.
Hindi nito sinusukat ang lahat ng 33 runtime gamit ang panukat ng isang vendor. Mahalaga ito: isang
300K GPT-5 turn na isinukat laban sa 200K ng Anthropic ay babasahin bilang ">100%, blown" kung saan
ito ay talagang 75% lamang ng 400K ng GPT-5. Ang parehong panukat ay itinatago ang isang totoong
na-overflow na 130K DeepSeek turn bilang isang komportableng 65%.

Ang bawat window ay may kasamang provenance: `model_table`, `explicit_marker`,
`observed_floor`, o isang tapat na `default` kapag hindi natin kilala ang model. Ang isang gauge
na binuo sa hula ay hindi kailanman nagre-render na may pareho ang awtoridad kumpara sa isang
binuo sa isang lookup.

Ang ClawMetry ay nakikita lang ang mga compaction event sa ilang runtime. Kaya iniulat ng
`GET /api/context-coverage`, kada runtime, kung ang isang zero ay nangangahulugang **"tumakbo
nang malinis" o "bulag kami"**. Ang isang `0` na sa totoo ay nangangahulugang bulag ay sinasabi
nito nang tapat. [Buong detalye](docs/CONTEXT_BLOWOUT.md)

**Magkano ba ang gastos ng instrumentation?**

| Path | Idinagdag sa agent mo | Default? |
|---|---|---|
| Session-file tailing (lahat ng 33 runtime) | **0**. Hiwalay na process, walang code ng ClawMetry sa agent mo | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** kada LLM call, o 0.009% ng 5s na call | off |
| Pre-tool hook gate (warm cache) | **+44 ms** kada gated tool call, higit sa 36 ms interpreter floor | off |
| Enforcement proxy | **+9.7 ms** kada LLM call | off |

Gastos sa daemon host: **2,762 event/sec** ang ingest, **710 byte/event** sa disk
(67.7 MB kada 100k event), at **~12% ng isang core** sustained sa isang abalang
install. Ang huling numerong iyan ay lampas sa sariling nakasaad na 5-10% na budget namin,
kaya inilathala ito bilang bug na dapat habulin sa halip na iwanan sa labas ng page.

Sinukat sa Apple M2 Pro gamit ang `benchmarks/overhead.py`. Pinapatakbo ng harness ang
bawat kondisyon sa hiwalay na process, pinapalit-palit ang pagkasunod-sunod nito, at **tumatangging
mag-print ng numero kapag hindi nagkakasundo ang mga round sa sign nito**. Patakbuhin ito sa sarili
mong makina sa isang minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Ang bawat path ay sinukat, kasama ang mga hook gate at ang enforcement proxy,
at ang harness ay tumatakbo sa Linux, macOS at Windows sa CI. Dalawang resulta na dapat malaman:
ang proxy ay nagkakahalaga ng humigit-kumulang pitong-ulit na mas mahal sa Windows kaysa sa Linux, at
ang daemon ay kasalukuyang sustained sa humigit-kumulang 12% ng isang core, lampas sa sariling 5-10%
na budget namin. Ang raw JSON, ang method, at kung ano ang hindi pa nasusukat ay nasa
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Pricing

| Plan | Ano ang sakop nito | Presyo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, buong dashboard, local lang | $0 |
| **Starter** | Lahat ng ibang runtime sa itaas, fleet view, cloud sync | $9 kada node / buwan |
| **Pro** | Starter + control at evaluation: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 kada node / buwan |

Ang mga annual plan, Enterprise at ang kasalukuyang mga numero ay nasa
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ang self-hosted license
keys ay gumagana nang walang cloud (`clawmetry license`). Ang eksaktong hati ng free/paid ay
nasa [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Nananatili sa makina mo ang data mo

Binabasa ng ClawMetry ang mga local session file at log. **Walang session data na lumalabas sa
makina mo maliban kung patakbuhin mo ang `clawmetry connect`** — walang prompt, reply, tool
argument, file content o log line. Kapag kumonekta ka, ang snapshot ay end-to-end encrypted
gamit ang key na hindi kailanman aalis sa makina mo, at na-decrypt sa browser mo. Kung ang isang
node ay walang key, ang upload ay nilaktawan sa halip na ipadala sa clear, at walang server response
na makakapagpatay nito.

Dalawang bagay ang tumatakbo bilang default bago ka kumonekta, pareho ay opt-out at wala sa mga ito ang
may dalang session data: isang anonymous install ping at isang version check laban sa
PyPI. Ang default install ay humahanap din ng public IP mo nang isang-pagkakataon para sa isang
startup banner line. Ang bawat destinasyon, kung ano ang dala nito at paano ito papatayin ay nakalista
sa [docs/EGRESS.md](docs/EGRESS.md); ang mga self-hosted, repointed at air-gapped na install ay
walang gumagawang discretionary outbound call.

Ang decryption ay nangyayari sa browser mo, sa code na pinapadala namin sa iyo. Dati itong isang
pangako; ngayon ito ay isang bagay na mabe-beripika mo. Ang bawat linya na humihipo sa key mo ay
nasa isang nababasang file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
na kasama sa wheel at ipinapadala verbatim, pinned gamit ang Subresource
Integrity hash. Para kumpirmahin na ang browser ay nagpapatakbo ng inilathala namin:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ano ang hindi napatunayan nito: kami ang nagpapadala ng page na nag-load ng file, kaya
posible kaming magpadala ng ibang page. Ang mga integrity hash ay pinoprotektahan ka mula sa
isang na-compromise na CDN, hindi mula sa vendor. Ang nakukuha mo ay na ang anumang pagpapalit ay
dapat sadya, nakikita sa page source, at iba sa artifact sa PyPI na kahit sino ay makukuha.
Ang pag-self-host o pananatiling local-only ay nag-aalis nang tuluyan sa dependency na ito.

## Install

```bash
pip install clawmetry     # pagkatapos: clawmetry
```

O ang one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kinakailangan ang Python 3.8+ sa macOS, Linux o Windows, at kahit isang agent runtime sa
parehong makina. Mga tagubilin sa Docker: [docs/DOCKER.md](docs/DOCKER.md).

O hayaan ang agent na i-set up ito para sa iyo. Tinuturuan ng skill na [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ang Claude Code, Codex, Cursor, Gemini CLI, Copilot o OpenCode na
mag-install ng ClawMetry, iulat kung ano ang gagawin at ginagastos ng mga agent sa makina,
ihinto ang isang session kapag hiniling, at i-hold ang mapanganib na tool call para sa approval:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Docs

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | Ano ang binabasa ng bawat adapter, at paano magdagdag ng runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Mga window kada provider, compaction laban sa overflow, coverage kada runtime |
| [Overhead](docs/OVERHEAD.md) | Magkano ang gastos ng instrumentation, sinukat, kasama ang harness para i-reproduce ito |
| [Entitlements](docs/ENTITLEMENTS.md) | Free laban sa paid, tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, mga phone approval |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | I-export ang mga trace saan man, mag-ingest ng OTLP mula sa anuman |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, kasama ang mga runnable example |
| [SDK tracking](docs/SDK_TRACKING.md) | Cost attribution para sa mga agent na ikaw mismo ang gumawa |
| [Chat channels](docs/CHANNELS.md) | Ang mga chat adapter na ipinapakita sa Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Mga sandboxed na setup ng NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Paano ito gumagana sa loob; pagpapatakbo mula sa source |
| [Telemetry](docs/TELEMETRY.md) | Ang anonymous install at desktop-open ping, at paano ito papatayin |

## Mga Screenshot

Ang bawat numero sa ibaba ay mula sa isang totoong makina, read-only, walang anumang na-seed.

**Sinasabihan ka nito kapag may mali, hindi lang kung ano ang nangyari.**
Dalawang anomaly banner sa itaas: gastos na 7x ng daily average, at isang
4.2x cost spike. Sa ibaba nito, 324 sa 667 kamakailang session na may dalang waste
signal, itemized ayon sa dahilan.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ipinapakita nito kung saan napunta ang pera, sa bawat window.**
$252.47 ngayon, $513.15 ngayong linggo, $1,312.92 ngayong buwan, bawat isa may kasamang token
sa likod nito at kung magkano ang nasasakop na ng subscription mo. Sa ibaba nito,
humigit-kumulang $1,128/buwan na itemized bilang recoverable at $17,256/buwan na
nai-save na ng cache reuse.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Iginuhit nito kung paano nagiging sagot ang isang mensahe.**
Ang live flow diagram: ikaw, ang channel kung saan ito dumating, ang gateway, ang model
na sumasagot sa ngayon, at ang bawat tool na ginamit nito. Nag-iilaw ang mga node habang
dumadaan ang trabaho sa mga ito.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Bawat agent sa makina, sa isang table.**
Ano ang pinapatakbo nito, ano ang gastos nito sa nakalipas na 24 oras at sa buong buhay
nito, kailan huling nakita, sino ang nagmamay-ari, at kung sinasakop ng subscription ang
bayarin. 14 agent dito, 3 session na gumagana, 13 tahimik.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ipinapakita nito kung saan napunta ang oras at pera ng isang turn, kada tool.**
Isang turn ng isang totoong session: 11 tool sa 11.2 minuto para sa $1.16. Ang bawat
Bash call at model call ay may sariling bar sa timeline, kaya ang command na tumakbo
nang 4.1 minuto at ang isa na tumakbo nang 226ms ay nakikilala sa isang sulyap lamang.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ginradwhuan nito ang trabaho, hindi lang ang gastos.**
Isang A ngayong linggo: 54 na gawain ang bumalik malinis, 2 magaspang na gastos ng $48.57,
at ang mga run na masyadong kaunti ang activity para husgahan ay hindi isinama sa grade
sa halip na bilangin bilang panalo. Ang bawat magaspang na run ay nakakonekta sa sariling trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ipinapakita nito kung bakit patuloy na napupuno ang context window.**
715K sa 1M-token window sa pinakahuling turn, isang 83.3% peak, 4 compaction na
lahat ay sumiklab nang proactive sa halip na dahil sa overflow, at ang utilization
ng bawat turn sa likod nito.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tumatakbo ang detection kahit walang i-configure ka.**
Ang built-in na mga detector ay naka-on mula sa install: agent na tumahimik, telemetry feed
na huminto, cost spike, token burst, umaakyat na error, error spike, budget
threshold, nakatugmang threat signature, security tool finding, nagbagong security posture.
Ang sariling mong mga rule ay optional sa ibabaw nito.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Ang pag-hold ng mapanganib na call ay opt-in, at ipinapadala nang naka-off.**
Ang recursive delete, force push, sudo, secrets, package install at outbound
call ay may sariling rule na mabubuksan mo. Hangga't hindi mo pa ito binubuksan, nagmamasid
ang ClawMetry at walang binabago. Kapag nabuksan ang isa, maghihintay dito ang mga tugmang
call (o sa telepono mo) para sa isang approve o deny.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Higit pa, kada runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Pagkilala

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT · Ginawa ni [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
