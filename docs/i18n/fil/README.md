<!-- i18n-src:9767c8001c9c -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Tignan mo ang iniisip ng iyong agent.** Real-time na observability para sa **30 AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 26 pa. Iisang dashboard para sa buong fleet ng iyong mga agent.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [marami pa →](docs/i18n/)

Isang command lang. Walang configuration. Awtomatikong nadedetect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900**. Walang configuration: hinahanap nito ang mga agent runtime na mayroon ka na, binabasa ang mga ito nang read-only, at walang binabago sa paraan ng pagtakbo nila.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Gumagana sa 30 agent runtime

**Libre sa open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sa bayad na plano:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Parehong dashboard ang makukuha ng bawat runtime. Kung tumatakbo ang ilan nang sabay, muling itatakda ng switcher sa header ang bawat tab papunta sa isa sa mga ito.

Gumawa ka ng sarili mong agent gamit ang isang SDK sa halip? Sinusubaybayan din ng interceptor ang mga LLM call nito. Tingnan ang [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ano ang makukuha mo

- **Mga session at transcript**: kung ano ang ginawa ng bawat agent, turn by turn, na may replay
- **Gastos at token**: kada runtime, modelo, session at araw, may mga anomaly flag
- **Flow**: live na diagram ng mga mensaheng dumadaan sa mga channel, modelo at tool
- **Brain**: ang stream ng mga event ng reasoning at tool-call habang nangyayari ito
- **Context blowout**: window utilization na sinusukat ayon sa provider, compaction laban sa forced overflow, kasama ang per-runtime map ng mga bagay na *hindi* namin makita ([paano](docs/CONTEXT_BLOWOUT.md))
- **Memory at skills**: ang mga file at skill na talagang ni-load ng bawat runtime
- **Health at logs**: disk, memory, error rate, rate limit, live log stream
- **Mga alerto**: budget cap, error spike, agent-offline, iruruta papunta sa Slack, Discord, PagerDuty, Telegram, Email
- **Mga approval**: i-pause ang mapanganib na tool call *bago* pa ito tumakbo at aprubahan mula sa iyong telepono ([paano](docs/APPROVALS.md))

## Context blowout, at ang halaga ng pagsubaybay

Dalawang tanong na sulit sasagutin bago ka magtiwala sa anumang tool na naghahambing ng agent.

**Paano nito hinahawakan ang context-window blowout sa iba't ibang runtime?**

Ang porsyento ng utilization ay kasing-tapat lamang ng hinahatian nito. Sinusukat ng ClawMetry ang window kada provider mula sa [isang table na maaari mong basahin at i-PR](clawmetry/context_windows.py), na sumasaklaw sa Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama at GLM. Hindi nito sinusukat ang lahat ng 26 runtime gamit ang panukat ng isang vendor lang. Mahalaga iyon: ang isang 300K GPT-5 turn na isinukat laban sa 200K ng Anthropic ay babasahin bilang ">100%, blown" kahit na 75% lang ito ng 400K ng GPT-5. Ang parehong panukat ay itinatago ang isang tunay na overflowed na 130K DeepSeek turn bilang isang komportableng 65%.

Bawat window ay dala ang pinagmulan nito: `model_table`, `explicit_marker`, `observed_floor`, o isang tapat na `default` kapag hindi namin alam ang modelo. Ang isang gauge na binuo sa isang hula ay hindi kailanman ipinapakita na may parehong awtoridad ng isa na binuo sa isang lookup.

Nakikita lang ng ClawMetry ang mga compaction event sa ilang runtime. Kaya ang `GET /api/context-coverage` ay iniuulat, kada runtime, kung ang **zero ay ibig sabihin "tumakbo nang malinis" o "bulag kami"**. Ang isang `0` na talagang ibig sabihin ay bulag ay sinasabi iyon.
[Buong detalye](docs/CONTEXT_BLOWOUT.md)

**Magkano ang gastos ng instrumentation?**

| Path | Idinagdag sa iyong agent | Default? |
|---|---|---|
| Session-file tailing (lahat ng 30 runtime) | **0**. Hiwalay na proseso, walang ClawMetry code sa iyong agent | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** kada LLM call, o 0.009% ng isang 5s na tawag | off |
| Pre-tool hook gate (warm cache) | **+44 ms** kada gated tool call, higit sa 36 ms na interpreter floor | off |
| Enforcement proxy | **+9.7 ms** kada LLM call | off |

Gastos ng daemon host: **2,762 event/sec** ingest, **710 bytes/event** sa disk
(67.7 MB kada 100k event), at **~12% ng isang core** na sustained sa isang abalang install. Ang huling numerong iyon ay lampas sa aming inilagay na 5-10% na budget, kaya inilathala ito bilang isang bug na dapat habulin sa halip na hindi na banggitin sa page.

Sinukat sa isang Apple M2 Pro gamit ang `benchmarks/overhead.py`. Pinapatakbo ng harness ang bawat kondisyon sa hiwalay na proseso, pinagpapalit-palit ang pagkakasunod-sunod nito, at **tumatangging maglabas ng numero kapag hindi magkatugma ang mga round sa senyales nito**. Patakbuhin ito sa sarili mong makina sa loob ng isang minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Bawat path ay sinusukat, kasama ang mga hook gate at ang enforcement proxy, at pinapatakbo ng harness sa Linux, macOS at Windows sa CI. Dalawang resulta na sulit malaman: ang proxy ay humigit-kumulang pitong beses na mas mahal sa Windows kumpara sa Linux, at ang daemon sa kasalukuyan ay sustained sa mga 12% ng isang core, higit sa aming sariling 5-10% na budget. Ang raw JSON, ang metodo, at kung ano pa ang hindi pa nasusukat ay nasa [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Pagpepresyo

| Plano | Ano ang saklaw nito | Presyo |
|---|---|---|
| **Libre** | OpenClaw + NVIDIA NemoClaw + Goose, buong dashboard, local lang | $0 |
| **Starter** | Bawat ibang runtime sa itaas, fleet view, cloud sync | $9 kada node / buwan |
| **Pro** | Starter + control at evaluation: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 kada node / buwan |

Ang mga taunang plano, Enterprise at ang kasalukuyang mga numero ay nasa
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Gumagana ang self-hosted license keys kahit walang cloud (`clawmetry license`). Ang eksaktong hati ng libre/bayad ay nasa [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Nananatili ang iyong data sa iyong makina

Binabasa ng ClawMetry ang mga lokal na session file at log. **Walang session data na aalis sa iyong makina maliban kung patakbuhin mo ang `clawmetry connect`** — walang prompt, sagot, tool argument, laman ng file o log line. Kapag kumonekta ka, ang snapshot ay end-to-end encrypted gamit ang isang key na hindi kailanman umaalis sa iyong makina, at dini-decrypt sa iyong browser. Kung walang key ang isang node, lalaktawan ang upload sa halip na ipadala nang walang encryption, at walang tugon ng server ang makakapatay nito.

May dalawang bagay na tumatakbo bilang default bago ka kumonekta, parehong opt-out at wala sa mga ito ang nagdadala ng session data: isang anonymous install ping at isang version check laban sa PyPI. Ang isang default install ay naghahanap din ng iyong public IP nang isang beses para sa isang startup banner line. Ang bawat destinasyon, kung ano ang dala nito at kung paano ito papatayin ay nakalista sa [docs/EGRESS.md](docs/EGRESS.md); ang mga self-hosted, repointed at air-gapped na install ay walang ginagawang discretionary na outbound call.

Ang decryption ay nagaganap sa iyong browser, sa code na ipinapadala namin sa iyo. Isa itong pangako dati; ngayon isa na itong bagay na maaari mong suriin. Bawat linya na humahawak sa iyong key ay nasa isang mababasang file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), na ipinapadala sa loob ng wheel at inihahatid nang literal, naka-pin gamit ang isang Subresource Integrity hash. Para kumpirmahin na pinapatakbo ng browser kung ano ang inilathala namin:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ang hindi napapatunayan nito: kami ang naghahatid ng page na naglo-load ng file, kaya maaari naming ihatid ang ibang page. Ang mga integrity hash ay proteksyon sa iyo mula sa isang na-compromise na CDN, hindi mula sa vendor. Ang nakukuha mo ay kailangang sinasadya, nakikita sa page source, at iba sa isang artifact sa PyPI na kahit sino ay maaaring kunin ang anumang pagpapalit. Ang self-hosting o pananatili sa local-only ay tuluyang inaalis ang dependency.

## Pag-install

```bash
pip install clawmetry     # pagkatapos: clawmetry
```

O ang one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kailangan ng Python 3.8+ sa macOS, Linux o Windows, at kahit isang agent runtime sa parehong makina. Mga instruksyon sa Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Mga Dokumento

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | Ano ang binabasa ng bawat adapter, at kung paano magdagdag ng runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Mga window kada provider, compaction laban sa overflow, coverage kada runtime |
| [Overhead](docs/OVERHEAD.md) | Ano ang gastos ng instrumentation, sinukat, kasama ang harness para maulit ito |
| [Entitlements](docs/ENTITLEMENTS.md) | Libre laban sa bayad, tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, mga approval sa telepono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | I-export ang mga trace kahit saan, i-ingest ang OTLP mula sa kahit ano |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, may mga runnable na halimbawa |
| [SDK tracking](docs/SDK_TRACKING.md) | Cost attribution para sa mga agent na ikaw mismo ang gumawa |
| [Chat channels](docs/CHANNELS.md) | Ang mga chat adapter na ipinapakita sa Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed na mga setup ng NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Kung paano ito gumagana sa loob; pagpapatakbo mula sa source |
| [Telemetry](docs/TELEMETRY.md) | Ang anonymous install at desktop-open na mga ping, at kung paano isara ang mga ito |

## Mga Screenshot

Bawat numero sa ibaba ay mula sa isang tunay na makina, read-only, na walang binhing data.

**Sinasabi nito sa iyo kung may mali, hindi lang kung ano ang nangyari.**
Dalawang anomaly banner sa itaas: gastos na tumatakbo nang 7x sa daily average, at isang 4.2x cost spike. Sa ilalim nito, 324 sa 667 kamakailang session ang may dalang waste signal, na inilista ayon sa dahilan.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ipinapakita nito sa iyo kung saan napunta ang pera, sa bawat window.**
$252.47 ngayong araw, $513.15 ngayong linggo, $1,312.92 ngayong buwan, bawat isa may kasamang token sa likod nito at kung gaano karami dito ang sakop na ng iyong subscription. Sa ibaba nito, mga $1,128/buwan na nakalista bilang mababawi at $17,256/buwan na nailigtas na ng cache reuse.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Iginuguhit nito kung paano nagiging sagot ang isang mensahe.**
Ang live flow diagram: ikaw, ang channel kung saan ito dumating, ang gateway, ang modelong sumasagot ngayon, at bawat tool na hinawakan nito. Nagliliwanag ang mga node habang dumadaan ang trabaho sa mga ito.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Bawat agent sa makina, sa isang table.**
Ano ang tumatakbo nito, magkano ang gastos nito sa nakaraang 24 na oras at sa buong buhay nito, kailan huling nakita, sino ang may-ari, at kung sinasaklaw ba ito ng isang subscription. 14 na agent dito, 3 session na gumagana, 13 tahimik.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ipinapakita nito kung saan napunta ang oras at pera ng isang turn, tool by tool.**
Isang turn ng isang tunay na session: 11 tool sa loob ng 11.2 minuto para sa $1.16. Bawat Bash call at model call ay may sariling bar sa timeline, kaya ang command na tumakbo nang 4.1 minuto at ang isang tumakbo nang 226ms ay makikilala kaagad.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ginagrado nito ang trabaho, hindi lang ang gastos.**
Isang A ngayong linggo: 54 na gawain ang bumalik nang malinis, 2 magaspang na gawain ang nagkahalaga ng $48.57, at ang mga run na kulang ang aktibidad para hatulan ay hindi isinama sa grado sa halip na bilangin bilang panalo. Bawat magaspang na run ay may link sa sarili nitong trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ipinapakita nito kung bakit patuloy na napupuno ang context window.**
715K sa isang 1M-token window sa pinakabagong turn, isang 83.3% na peak, 4 na compaction na lahat ay pumutok nang proactive sa halip na dahil sa overflow, at ang utilization ng bawat turn sa likod nito.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tumatakbo ang detection nang hindi mo kailangang mag-configure ng anuman.**
Ang mga built-in na detector ay naka-on mula sa install: tumahimik ang agent, huminto ang telemetry feed, cost spike, token burst, tumataas na error, error spike, budget threshold, tumugmang threat signature, natuklasan ng security tool, nagbagong security posture. Ang sarili mong mga rule ay opsyonal na dagdag dito.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Opt-in ang pag-hold ng mapanganib na tawag, at naka-off bilang default.**
Ang recursive delete, force push, sudo, secrets, package install at outbound call ay bawat isa ay may rule na maaari mong i-on. Hanggang sa gawin mo, nagmamasid lang ang ClawMetry at walang binabago. Kapag na-on na ang isa, hihintay dito ang mga tumutugmang tawag (o sa iyong telepono) para sa isang approve o deny.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Marami pa, kada runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Kasaysayan ng Star

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lisensya

MIT · Ginawa ni [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
