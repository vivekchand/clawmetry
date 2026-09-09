<!-- i18n-src:61beb8393e2f -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ang isang ahente ay maaaring gumawa ng isandaang tool call nang walang pag-usad.** Binabasa ng ClawMetry
ang mga session file na isinusulat na ng iyong mga coding agent, at inilalagay ang timeline,
ang mga tool call, at anumang token at cost data na inilalantad ng runtime sa isang
view — para malaman mo kung aling mahabang run ang gumagana kumpara sa isang natigil na lang.

Gumagana sa **30 AI agent runtime** — Claude Code, OpenAI Codex, Hermes, OpenClaw at 26 pa. Isang dashboard para sa buong fleet ng iyong ahente. ([ang kumpletong listahan](SUPPORTED_RUNTIMES.txt), na nabuo mula sa katalogo.)

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Walang kailangang i-configure. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900**. Zero config: hinahanap nito ang mga agent runtime na
mayroon ka na, binabasa ang mga ito nang read-only lamang, at walang binabago sa kung paano sila tumatakbo.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bago ka mag-install

| | |
|---|---|
| **Ano ang ginagawa nito** | Binabasa ang mga session file at log na isinusulat na ng iyong mga ahente. Walang SDK, walang pagbabago sa code, walang instrumentation sa iyong app. |
| **Ano ang makikita mo** | Session timeline, tool-by-tool replay, breakdown ng token at cost, at mga trajectory signal (looping, paulit-ulit na kabiguan) — kada runtime. |
| **Ano ang libre** | Binabasa ng `pip install clawmetry` ang **OpenClaw, NVIDIA NemoClaw at Goose** nang walang account, walang key, at walang network call. Ang iba pang 27 — Claude Code, Codex, Cursor at ang natitira — ay binabasa ng closed-source na kasamang app na `clawmetry-pro`, na kasama sa 7-araw na trial o sa isang plano — tingnan ang [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para sa eksaktong hatian. |
| **Paano magsimula** | `pip install clawmetry && clawmetry`, pagkatapos buksan ang localhost:8900. Wala pang ahente sa makinang ito? Bubuksan ng `clawmetry --sample` ang tatlong may-label na synthetic session. |
| **Ano ang umaalis sa iyong makina** | Walang session data, maliban kung patatakbuhin mo ang `clawmetry connect`. May dalawang bagay na tumatakbo bilang default, pareho itong opt-out at wala sa dalawa ang nagdadala ng session content: isang anonymous install ping at isang PyPI version check. Bawat destinasyon ay nakalista sa [docs/EGRESS.md](docs/EGRESS.md), na muling binuo mula sa wire capture sa halip na mula sa pagbabasa ng mga comment. |

May dalawang limitasyon na mahalagang malaman bago mo husgahan ang output: iba't ibang runtime ay
naglalantad ng ibang-ibang data (may ilang hindi naglalabas ng anumang cost — [ang matrix](docs/compatibility.md)
ang nagsasabi kung alin, kada runtime), at ang pagmamasid sa isang aksyon ay hindi katumbas ng kakayahang
harangin ito ([alin sa mga kontrol ang totoo, kada runtime](docs/APPROVALS.md)).


## Gumagana sa 30 agent runtime

**Libre sa open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sa isang bayad na plano:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Parehong dashboard ang makukuha ng bawat runtime. Patakbuhin ang ilan nang sabay-sabay at ire-rescope
ng header switcher ang bawat tab sa isa sa mga ito.

Gumawa ka ba ng sarili mong ahente gamit ang isang SDK? Sinusubaybayan din ng interceptor ang mga LLM call nito.
Tingnan ang [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ang makukuha mo

- **Mga session at transcript**: kung ano ang ginawa ng bawat ahente, turn by turn, na may replay
- **Cost at tokens**: kada runtime, model, session at araw, may mga anomaly flag
- **Flow**: live na diagram ng mga mensaheng dumadaan sa mga channel, model at tool
- **Brain**: ang stream ng reasoning at tool-call event habang nangyayari ito
- **Context blowout**: window utilization na nasukat kada provider, compaction laban sa forced overflow, kasama ang mapa kada runtime ng hindi namin *makita* ([paano](docs/CONTEXT_BLOWOUT.md))
- **Memory at skills**: ang mga file at skill na aktwal na na-load ng bawat runtime
- **Health at logs**: disk, memory, error rates, rate limits, live log stream
- **Alerts**: budget caps, error spikes, agent-offline, na iruruta sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: i-pause ang mapanganib na tool call *bago* ito tumakbo at aprubahan mula sa iyong telepono ([paano](docs/APPROVALS.md))

## Context blowout, at ang gastos ng pagbabantay

Dalawang tanong na sulit sasagutin bago ka manalig sa anumang tool na naghahambing ng ahente.

**Paano nito hinahandle ang context-window blowout sa iba't ibang runtime?**

Ang isang utilization percentage ay katapatan lamang kung ano ang hinahatian nito. Sinusukat ng ClawMetry
ang window kada provider mula sa [isang table na puwede mong basahin at
i-PR](clawmetry/context_windows.py), na sumasaklaw sa Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama at GLM. Hindi nito sinusukat ang lahat ng 30
runtime gamit ang panukat ng iisang vendor. Mahalaga ito: kung ang isang 300K GPT-5 turn ay isinukat
laban sa 200K ng Anthropic, mababasa itong ">100%, blown" kahit ito ay nasa 75% lamang ng
400K ng GPT-5. Ang parehong panukat ay itinatago ang isang totoong nag-overflow na 130K DeepSeek turn
bilang isang komportableng 65%.

Bawat window ay dala ang sariling provenance: `model_table`, `explicit_marker`,
`observed_floor`, o isang tapat na `default` kapag hindi namin alam ang model. Ang isang
gauge na binuo sa isang hula ay hindi kailanman lalabas nang may parehong awtoridad tulad ng isang binuo sa
isang lookup.

Ang ClawMetry ay nakakakita lamang ng mga compaction event sa ilang runtime. Kaya ang
`GET /api/context-coverage` ay nag-uulat, kada runtime, kung ang **zero ba ay ibig sabihin
"tumakbo nang malinis" o "bulag kami"**. Ang isang `0` na aktwal na ibig sabihin ay bulag ay sinasabi ito.
[Buong detalye](docs/CONTEXT_BLOWOUT.md)

**Magkano ang gastos ng instrumentation?**

| Path | Idinagdag sa iyong ahente | Default ba? |
|---|---|---|
| Session-file tailing (lahat ng 30 runtime) | **0**. Hiwalay na proseso, walang code ng ClawMetry sa iyong ahente | naka-on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** kada LLM call, o 0.009% ng isang 5s na call | naka-off |
| Pre-tool hook gate (warm cache) | **+44 ms** kada gated tool call, sa ibabaw ng 36 ms na interpreter floor | naka-off |
| Enforcement proxy | **+9.7 ms** kada LLM call | naka-off |

Gastos sa daemon host: **2,762 events/sec** ingest, **710 bytes/event** sa disk
(67.7 MB kada 100k events), at **~12% ng isang core** sustained sa isang abalang
install. Ang huling numero na iyon ay lampas sa aming sariling itinakdang badyet na 5-10%, kaya ito ay
inilathala bilang isang bug na dapat habulin sa halip na alisin sa page.

Sinukat sa isang Apple M2 Pro gamit ang `benchmarks/overhead.py`. Ang harness ay pinapatakbo
ang bawat kondisyon sa hiwalay na proseso, ina-alternate ang pagkakasunod-sunod nila, at **tumatangging
mag-print ng numero kapag hindi magkasundo ang mga round sa sign nito**. Patakbuhin ito sa iyong sariling
makina sa loob ng isang minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Bawat path ay sinusukat, kasama ang mga hook gate at ang enforcement proxy,
at ang harness ay tumatakbo sa Linux, macOS at Windows sa CI. May dalawang resulta na sulit
malaman: ang proxy ay may humigit-kumulang pitong beses na mas mataas na gastos sa Windows kumpara sa Linux, at
kasalukuyang sinusustena ng daemon ang humigit-kumulang 12% ng isang core, lampas sa aming sariling 5-10%
na badyet. Ang raw JSON, ang metodo, at kung ano pa ang hindi pa nasusukat ay nasa
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Pagpepresyo

| Plano | Ano ang saklaw nito | Presyo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, buong dashboard, local lamang | $0 |
| **Starter** | Bawat iba pang runtime sa itaas, fleet view, cloud sync | $9 kada node / buwan |
| **Pro** | Starter + kontrol at ebalwasyon: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 kada node / buwan |

Ang mga taunang plano, Enterprise, at ang kasalukuyang mga numero ay nasa
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Gumagana ang mga self-hosted license
key nang walang cloud (`clawmetry license`). Ang eksaktong hatian ng free/bayad ay
nasa [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Nananatili sa iyong makina ang iyong data

Binabasa ng ClawMetry ang mga lokal na session file at log. **Walang session data ang umaalis sa iyong makina
maliban kung patatakbuhin mo ang `clawmetry connect`** — walang prompts, tugon, tool arguments, laman ng file
o log lines. Kapag kumonekta ka, ang snapshot ay end-to-end encrypted
gamit ang key na hindi kailanman umaalis sa iyong makina, at nade-decrypt sa iyong browser. Kung ang isang
node ay walang key, ang upload ay nilalaktawan sa halip na ipadala nang plain, at walang
tugon ng server ang makapagpapa-off niyan.

May dalawang bagay na tumatakbo bilang default bago ka kumonekta, pareho itong opt-out at wala sa dalawa
ang nagdadala ng session data: isang anonymous install ping at isang version check laban sa
PyPI. Isang default install din ay minsanang hinahanap ang iyong pampublikong IP para sa isang startup banner
line. Bawat destinasyon, kung ano ang dala nito, at kung paano ito i-off ay nakalista sa
[docs/EGRESS.md](docs/EGRESS.md); ang self-hosted, repointed, at air-gapped na mga install ay
walang ginagawang discretionary outbound call.

Ang decryption ay nangyayari sa iyong browser, sa code na aming ipinapadala sa iyo. Dati itong isang
pangako lamang; ngayon ito ay isang bagay na maaari mong suriin. Bawat linyang humihipo sa iyong key ay
nasa isang mababasang file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
na kasama sa wheel at ipinapadala nang buo, naka-pin gamit ang Subresource
Integrity hash. Para kumpirmahin na ang browser ay pinapatakbo ang aming inilathala:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ang hindi nito napatunayan: kami ang naghahatid ng page na naglo-load ng file, kaya maaari kaming
maghatid ng ibang page. Pinoprotektahan ng integrity hash ang iyo mula sa isang na-compromise na CDN,
hindi mula sa vendor. Ang nakukuha mo ay anumang pagpapalit ay dapat sadya,
nakikita sa page source, at iba sa isang artifact sa PyPI na kahit sino ay makakakuha. Ang
pag-self-host o pananatiling local-only ay ganap na nag-aalis sa dependency na ito.

## Pag-install

```bash
pip install clawmetry     # tapos: clawmetry
```

O ang one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kailangan ng Python 3.8+ sa macOS, Linux o Windows, at hindi bababa sa isang agent runtime sa
parehong makina. Mga instruksyon sa Docker: [docs/DOCKER.md](docs/DOCKER.md).

O hayaan ang ahente ang mag-set up para sa iyo. Ang [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
skill ay tinuturuan ang Claude Code, Codex, Cursor, Gemini CLI, Copilot o OpenCode na
i-install ang ClawMetry, iulat kung ano ang ginagawa at ginagastos ng mga ahente sa makina,
ihinto ang isang session kapag hiniling, at i-hold ang mapanganib na tool call para sa aprubasyon:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentasyon

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | Ano ang binabasa ng bawat adapter, at paano magdagdag ng runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Mga window kada provider, compaction laban sa overflow, coverage kada runtime |
| [Overhead](docs/OVERHEAD.md) | Magkano ang gastos ng instrumentation, nasukat, may harness para ma-reproduce ito |
| [Entitlements](docs/ENTITLEMENTS.md) | Libre laban sa bayad, tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, mga aprubasyon sa telepono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | I-export ang traces kahit saan, mag-ingest ng OTLP mula sa kahit ano |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, may mga runnable na halimbawa |
| [SDK tracking](docs/SDK_TRACKING.md) | Pag-attribute ng cost para sa mga ahenteng ginawa mo mismo |
| [Chat channels](docs/CHANNELS.md) | Ang mga chat adapter na ipinapakita sa Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Mga sandboxed na setup ng NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Paano ito gumagana sa loob; pagpapatakbo mula sa source |
| [Telemetry](docs/TELEMETRY.md) | Ang anonymous install at desktop-open pings, at kung paano i-off ang mga ito |

## Mga Screenshot

Bawat numero sa ibaba ay mula sa isang totoong makina, read-only, walang seeded na anuman.

**Sinasabihan ka nito kapag may mali, hindi lang kung ano ang nangyari.**
Dalawang anomaly banner sa itaas: paggastos na tumatakbo nang 7x sa daily average, at isang
4.2x na cost spike. Sa ibaba nito, 324 sa 667 na kamakailang session ang may dalang waste
signal, na inilista ayon sa dahilan.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ipinapakita nito kung saan napunta ang pera, sa bawat window.**
$252.47 ngayon, $513.15 ngayong linggo, $1,312.92 ngayong buwan, bawat isa ay may kasamang
tokens sa likod nito at kung gaano karami nito ang sakop na ng iyong subscription. Sa ibaba nito,
humigit-kumulang $1,128/buwan na nakalista bilang recoverable at $17,256/buwan na naipon na
sa muling paggamit ng cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Iginuhit nito kung paano nagiging sagot ang isang mensahe.**
Ang live flow diagram: ikaw, ang channel kung saan ito dumating, ang gateway, ang model
na sumasagot sa ngayon, at bawat tool na inabot nito. Nagliliwanag ang mga node habang
gumagalaw ang trabaho sa mga ito.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Bawat ahente sa makina, sa isang table.**
Ano ang pinapatakbo nito, magkano ang gastos nito sa nakaraang 24 oras at sa buong buhay nito, kailan
ito huling nakita, sino ang may-ari, at kung sakop ba ito ng isang subscription. 14 na ahente dito,
3 session na gumagana, 13 tahimik.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ipinapakita nito kung saan napunta ang oras at pera ng isang turn, tool by tool.**
Isang turn ng isang totoong session: 11 tool sa loob ng 11.2 minuto para sa $1.16. Bawat Bash
call at model call ay may sariling bar sa timeline, kaya ang command na tumakbo ng
4.1 minuto at ang isang tumakbo ng 226ms ay agad na makikilala.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ginagrado nito ang trabaho, hindi lang ang gastos.**
Isang A ngayong linggo: 54 na gawain ang bumalik nang malinis, 2 magaspang ang nagkakahalaga ng $48.57, at
ang mga run na kulang ang aktibidad para husgahan ay hindi isinama sa grado sa halip na
ibilang bilang panalo. Bawat magaspang na run ay naka-link sa trace nito.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ipinapakita nito kung bakit patuloy na napupuno ang context window.**
715K ng 1M-token window sa pinakahuling turn, isang 83.3% na peak, 4 na compaction
na lahat ay nag-fire nang proactive sa halip na sa overflow, at ang utilization ng
bawat turn sa likod nito.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tumatakbo ang detection nang hindi mo kailangang i-configure ang anuman.**
Ang mga built-in na detector ay naka-on simula sa pag-install: tumahimik ang ahente, huminto ang
telemetry feed, cost spike, token burst, tumataas na error rates, error spike, budget
threshold, tumugmang threat signature, natagpuan ng security tool, nagbago ang security
posture. Ang iyong sariling mga panuntunan ay opsyonal sa ibabaw nito.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Ang pag-hold sa mapanganib na tanawag ay opt-in, at ipinapadala nang naka-off.**
Ang mga recursive delete, force push, sudo, secrets, package install, at outbound
call ay bawat isa ay may panuntunan na maaari mong i-on. Hangga't hindi mo ginagawa, binabantayan lang
ng ClawMetry at walang binabago. Kapag naka-on na ang isa, ang mga tumutugmang tawag ay naghihintay dito
(o sa iyong telepono) para sa pag-apruba o pagtanggi.

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

## Lisensya

MIT · Ginawa ni [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
