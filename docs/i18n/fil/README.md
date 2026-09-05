<!-- i18n-src:88be2deff5d5 -->
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

**Makita mo ang pag-iisip ng iyong agent.** Real-time na observability para sa **30 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 26 pa. Isang dashboard para sa buong fleet ng iyong mga agent.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command. Zero config. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Magbubukas sa **http://localhost:8900**. Zero config: hinahanap nito ang mga agent runtime na mayroon ka na, binabasa ang mga ito nang read-only, at walang binabago sa kung paano sila tumatakbo.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Gumagana sa 30 agent runtimes

**Libre sa open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sa bayad na plano:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Parehong dashboard ang makukuha ng bawat runtime. Patakbuhin ang ilan nang sabay at ire-rescope ng switcher sa header ang bawat tab papunta sa isa sa mga ito.

Ginawa ang sarili mong agent gamit ang isang SDK? Sinusubaybayan din ng interceptor ang mga LLM call nito. Tingnan ang [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ano ang makukuha mo

- **Sessions at transcripts**: kung ano ang ginawa ng bawat agent, turn by turn, may replay
- **Cost at tokens**: kada runtime, model, session at araw, may mga anomaly flag
- **Flow**: live diagram ng mga mensaheng dumadaloy sa mga channel, model at tool
- **Brain**: ang stream ng mga event ng reasoning at tool call habang nangyayari ito
- **Context blowout**: window utilization na naka-size kada provider, compaction laban sa forced overflow, kasama ang per-runtime na mapa ng kung ano ang *hindi* namin makita ([paano](docs/CONTEXT_BLOWOUT.md))
- **Memory at skills**: ang mga file at skill na aktwal na na-load ng bawat runtime
- **Health at logs**: disk, memory, error rates, rate limits, live log stream
- **Alerts**: budget caps, error spikes, agent-offline, ipinapasa sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: i-pause ang mapanganib na tool call *bago* ito tumakbo at aprubahan mula sa iyong telepono ([paano](docs/APPROVALS.md))

## Context blowout, at kung magkano ang gastos ng pagbabantay

Dalawang tanong na sulit sasagutin bago ka magtiwala sa anumang tool na naghahambing ng mga agent.

**Paano nito hinahandle ang context-window blowout sa iba't ibang runtime?**

Ang isang utilization percentage ay kasing-tapat lamang ng hinati nito. Sina-size ng ClawMetry ang window kada provider mula sa [isang table na mababasa mo at pwedeng i-PR](clawmetry/context_windows.py), sumasaklaw sa Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama at GLM. Hindi nito sinusukat ang lahat ng 30 runtime gamit ang panukat ng isang vendor lamang. Mahalaga iyon: ang isang 300K GPT-5 turn na sinukat laban sa 200K ng Anthropic ay babasahin bilang ">100%, blown" kahit na nasa 75% pa lamang ito ng 400K ni GPT-5. Ang parehong panukat ay nagtatago ng isang tunay na na-overflow na 130K DeepSeek turn bilang isang komportableng 65%.

Bawat window ay may kasamang provenance nito: `model_table`, `explicit_marker`, `observed_floor`, o isang tapat na `default` kapag hindi namin alam ang model. Ang isang gauge na binuo sa isang hula ay hindi kailanman lalabas nang may parehong awtoridad ng isang binuo sa isang lookup.

Nakikita lamang ng ClawMetry ang mga compaction event sa ilang runtime. Kaya ang `GET /api/context-coverage` ay nag-uulat, kada runtime, kung ang isang **zero ay ibig sabihin "tumakbo nang malinis" o "bulag kami"**. Ang isang `0` na aktwal na nangangahulugang bulag ay sinasabi ito.
[Buong detalye](docs/CONTEXT_BLOWOUT.md)

**Magkano ang gastos ng instrumentation?**

| Path | Naidagdag sa iyong agent | Default? |
|---|---|---|
| Session-file tailing (lahat ng 30 runtime) | **0**. Hiwalay na proseso, walang ClawMetry code sa iyong agent | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** kada LLM call, o 0.009% ng isang 5s call | off |
| Pre-tool hook gate (warm cache) | **+44 ms** kada gated tool call, higit sa 36 ms na interpreter floor | off |
| Enforcement proxy | **+9.7 ms** kada LLM call | off |

Gastos ng daemon host: **2,762 events/sec** na ingest, **710 bytes/event** sa disk
(67.7 MB kada 100k na event), at **~12% ng isang core** na sustained sa isang abalang install. Ang huling numerong iyon ay lampas sa aming sariling nakasaad na 5-10% na budget, kaya inilathala ito bilang isang bug na dapat habulin sa halip na hindi na banggitin sa page.

Sinukat sa isang Apple M2 Pro gamit ang `benchmarks/overhead.py`. Ang harness ay nagpapatakbo ng bawat kondisyon sa hiwalay na proseso, inaalternate ang pagkakasunod-sunod nila, at **tumatangging mag-print ng numero kapag hindi magkasundo ang mga round tungkol sa sign nito**. Patakbuhin ito sa sarili mong makina sa loob ng isang minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Bawat path ay sinusukat, kasama ang mga hook gate at ang enforcement proxy, at ang harness ay tumatakbo sa Linux, macOS at Windows sa CI. Dalawang resulta na sulit malaman: ang proxy ay may humigit-kumulang pitong beses na mas mataas na gastos sa Windows kaysa sa Linux, at kasalukuyang sinusustena ng daemon ang halos 12% ng isang core, higit sa aming sariling 5-10% na budget. Ang raw JSON, ang method, at kung ano pa ang hindi pa sinusukat ay nasa
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Pagpepresyo

| Plano | Sakop nito | Presyo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, buong dashboard, local lamang | $0 |
| **Starter** | Bawat ibang runtime sa itaas, fleet view, cloud sync | $9 kada node / buwan |
| **Pro** | Starter + control at evaluation: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 kada node / buwan |

Ang mga taunang plano, Enterprise at ang kasalukuyang mga numero ay nasa
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Gumagana ang mga self-hosted license key nang walang cloud (`clawmetry license`). Ang eksaktong hati ng free/paid ay nasa [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Nananatili sa iyong makina ang iyong data

Binabasa ng ClawMetry ang mga lokal na session file at log. **Walang session data na aalis sa iyong makina maliban kung patakbuhin mo ang `clawmetry connect`** — walang prompts, replies, tool arguments, file contents o log lines. Kapag kumonekta ka, ang snapshot ay end-to-end encrypted gamit ang isang key na hindi kailanman umaalis sa iyong makina, at nade-decrypt sa iyong browser. Kung walang key ang isang node, nilalaktawan ang upload sa halip na ipadala nang plain, at walang server response na makakapagpatay nito.

Dalawang bagay ang tumatakbo bilang default bago ka kumonekta, kapwa opt-out at wala sa dalawa ang may dalang session data: isang anonymous na install ping at isang version check laban sa PyPI. Ang default na install ay naghahanap din minsan ng iyong public IP para sa isang startup banner line. Bawat destinasyon, kung ano ang dala nito at paano ito i-off ay nakalista sa
[docs/EGRESS.md](docs/EGRESS.md); ang mga self-hosted, na-repoint, at air-gapped na install ay walang anumang discretionary outbound call.

Ang decryption ay nangyayari sa iyong browser, sa code na ipinapadala namin sa iyo. Ito dating isang pangako lamang; ngayon ay isang bagay na maaari mong suriin. Bawat linyang humahawak sa iyong key ay nasa isang mababasang file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), na sinasama sa loob ng wheel at ipinapadala nang verbatim, naka-pin gamit ang isang Subresource Integrity hash. Para kumpirmahin na pinapatakbo ng browser ang inilathala namin:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ang hindi napapatunayan nito: kami ang nagpapadala ng page na nagloload ng file, kaya posible kaming magpadala ng ibang page. Pinoprotektahan ka ng mga integrity hash mula sa isang compromised CDN, hindi mula sa vendor. Ang nakukuha mo ay dapat sadya, nakikita sa page source, at naiiba mula sa isang artifact sa PyPI na kaya ng sinuman kunin ang anumang pagpapalit. Ang pag-self-host o pananatiling local-only ay ganap na nag-aalis sa pag-asa dito.

## Pag-install

```bash
pip install clawmetry     # tapos: clawmetry
```

O ang one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kailangan ng Python 3.8+ sa macOS, Linux o Windows, at hindi bababa sa isang agent runtime sa parehong makina. Mga instruksyon sa Docker: [docs/DOCKER.md](docs/DOCKER.md).

O hayaan ang agent na mag-set up para sa iyo. Ang skill na [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ay nagtuturo sa Claude Code, Codex, Cursor, Gemini CLI, Copilot o OpenCode na
i-install ang ClawMetry, iulat kung ano ang ginagawa at ginagastos ng mga agent sa makina,
ihinto ang isang session kapag hiniling, at pigilan ang mapanganib na tool call para sa pag-apruba:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Docs

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | Ano ang binabasa ng bawat adapter, at paano magdagdag ng runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Mga window kada provider, compaction laban sa overflow, coverage kada runtime |
| [Overhead](docs/OVERHEAD.md) | Magkano ang gastos ng instrumentation, sinukat, may harness para i-reproduce ito |
| [Entitlements](docs/ENTITLEMENTS.md) | Free laban sa paid, tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, mga pag-apruba sa telepono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | I-export ang traces kahit saan, i-ingest ang OTLP mula sa kahit ano |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, may mga runnable example |
| [SDK tracking](docs/SDK_TRACKING.md) | Cost attribution para sa mga agent na ginawa mo mismo |
| [Chat channels](docs/CHANNELS.md) | Ang mga chat adapter na ipinapakita sa Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Mga sandboxed setup ng NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Paano ito gumagana sa loob; pagpapatakbo mula sa source |
| [Telemetry](docs/TELEMETRY.md) | Ang anonymous na install at desktop-open pings, at kung paano ito i-off |

## Mga Screenshot

Bawat numero sa ibaba ay galing sa isang tunay na makina, read-only, na walang anumang seedeng laman.

**Sinasabi nito sa iyo kapag may mali, hindi lang kung ano ang nangyari.**
Dalawang anomaly banner sa itaas: paggastos na tumatakbo nang 7x ang daily average, at isang
4.2x na cost spike. Sa ibaba nila, 324 sa 667 kamakailang session ang may dalang waste
signal, na inayos ayon sa dahilan.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ipinapakita nito sa iyo kung saan napunta ang pera, sa bawat window.**
$252.47 ngayon, $513.15 ngayong linggo, $1,312.92 ngayong buwan, bawat isa may kasamang tokens
sa likod nito at kung gaano karami ang sakop na ng iyong subscription. Sa ibaba nito, mga $1,128/buwan na na-itemize bilang recoverable at $17,256/buwan na naitipid na dahil sa cache reuse.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Iginuhit nito kung paano nagiging sagot ang isang mensahe.**
Ang live flow diagram: ikaw, ang channel kung saan ito dumating, ang gateway, ang model
na sumasagot ngayon, at bawat tool na ginamit nito. Nagliliwanag ang mga node habang gumagalaw ang trabaho sa mga ito.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Bawat agent sa makina, sa isang table.**
Ano ang tinatakbo nito, magkano ang gastos nito sa huling 24 oras at sa buong lifetime nito, kailan
ito huling nakita, sino ang may-ari nito, at kung sinasaklaw ba ito ng isang subscription. 14 na agent dito, 3 session ang gumagana, 13 tahimik.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ipinapakita nito kung saan napunta ang oras at pera ng isang turn, tool by tool.**
Isang turn ng isang tunay na session: 11 tool sa loob ng 11.2 minuto para sa $1.16. Bawat Bash
call at model call ay may sariling bar sa timeline, para ang command na tumakbo nang
4.1 minuto at ang isa na tumakbo nang 226ms ay makikilala kaagad.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ginagrado nito ang trabaho, hindi lang ang paggastos.**
Isang A ngayong linggo: 54 na gawain ang natapos nang malinis, 2 magulong isyu ang nagkakahalaga ng $48.57, at ang mga run na kulang sa aktibidad para husgahan ay hindi isinama sa grado sa halip na bilangin bilang panalo. Ang bawat magulong run ay naka-link sa trace nito.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ipinapakita nito kung bakit patuloy na napupuno ang context window.**
715K sa 1M-token window sa pinakahuling turn, isang 83.3% na peak, 4 na compaction
na lahat ay proactive na sumiklab sa halip na dahil sa overflow, at ang utilization ng
bawat turn sa likod nito.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tumatakbo ang detection nang hindi mo kailangang mag-configure ng kahit ano.**
Aktibo na ang built-in na mga detector mula sa pag-install: agent na tumahimik, tumigil na telemetry feed,
cost spike, token burst, tumataas na error, error spike, budget threshold, tumugmang threat
signature, security tool finding, nagbagong security posture. Opsyonal sa ibabaw nito ang sarili mong mga rule.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Opsyonal ang pagpigil sa isang mapanganib na call, at naka-off ito bilang default.**
Ang recursive deletes, force pushes, sudo, secrets, package installs at outbound
calls ay bawat isa may rule na maaari mong i-on. Hanggang hindi mo ito ginagawa, nagbabantay lamang ang ClawMetry at walang binabago. Kapag naka-on na ang isa, naghihintay dito ang mga tumutugmang call (o sa iyong telepono)
para sa isang approve o deny.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Higit pa, kada runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

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
