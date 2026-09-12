<!-- i18n-src:a855a14295b0 -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Kayang gumawa ng isang ahente ng isandaang tool call nang walang anumang pag-unlad.** Binabasa ng ClawMetry
ang mga session file na isinusulat na ng iyong mga coding agent, at inilalagay ang timeline,
ang mga tool call, at anumang datos ng token at gastos na inilalantad ng runtime sa iisang
view — para makita mo agad kung ang isang mahabang run ay gumagana o natigil na lang.

Gumagana kasama ng **32 AI agent runtime** — Claude Code, OpenAI Codex, Hermes, OpenClaw at 28 pa. Isang dashboard para sa buong fleet ng iyong ahente. ([ang kumpletong listahan](SUPPORTED_RUNTIMES.txt), gawa mula sa katalogo.)

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Walang kailangang i-configure. Awtomatikong nakikita ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900**. Walang configuration: hinahanap nito ang mga agent runtime na
mayroon ka na, binabasa ang mga ito nang read-only lamang, at walang binabago sa kung paano sila tumatakbo.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bago mag-install

| | |
|---|---|
| **Ano ang ginagawa nito** | Binabasa ang mga session file at log na isinusulat na ng iyong mga ahente. Walang SDK, walang pagbabago sa code, walang instrumentation sa iyong app. |
| **Ano ang makikita mo** | Session timeline, tool-by-tool replay, breakdown ng token at gastos, at mga trajectory signal (looping, paulit-ulit na pagkabigo) — kada runtime. |
| **Ano ang libre** | Binabasa ng `pip install clawmetry` ang **OpenClaw, NVIDIA NemoClaw, at Goose** nang walang account, walang key, at walang network call. Ang iba pang 27 — Claude Code, Codex, Cursor at ang iba pa — ay binabasa ng closed-source na kasamang `clawmetry-pro`, na dumarating kasama ang 7-araw na trial o isang plano — tingnan ang [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para sa eksaktong hati. |
| **Paano magsimula** | `pip install clawmetry && clawmetry`, pagkatapos buksan ang localhost:8900. Wala pang mga ahente sa makinang ito? Binubuksan ng `clawmetry --sample` ang tatlong may-label na synthetic session. |
| **Ano ang lumalabas sa iyong makina** | Walang datos ng session, maliban kung patakbuhin mo ang `clawmetry connect`. Dalawang bagay ang tumatakbo bilang default, parehong opt-out at wala sa mga ito ang nagdadala ng laman ng session: isang anonymous install ping at isang PyPI version check. Bawat destinasyon ay nakalista sa [docs/EGRESS.md](docs/EGRESS.md), muling ginawa mula sa wire capture sa halip na mula sa pagbabasa ng mga komento. |

May dalawang limitasyon na dapat malaman bago mo hatulan ang output: naglalantad ang mga runtime ng
lubhang magkakaibang datos (may ilan na hindi naglalantad ng anumang gastos — [ang matrix](docs/compatibility.md)
ang nagsasabi kung alin, kada runtime), at ang pag-obserba sa isang aksyon ay hindi katulad ng
kakayahang harangin ito ([alin sa mga kontrol ang totoo, kada runtime](docs/APPROVALS.md)).


## Gumagana kasama ang 32 agent runtime

**Libre sa open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sa bayad na plano:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Parehong dashboard ang makukuha ng bawat runtime. Magpatakbo ng ilan nang sabay at ang header
switcher ay muling itatakda ang saklaw ng bawat tab sa isa sa kanila.

Gumawa ka ba ng sarili mong ahente gamit ang isang SDK sa halip? Sinusubaybayan din ng interceptor
ang mga LLM call nito. Tingnan ang [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ano ang makukuha mo

- **Mga session at transcript**: kung ano ang ginawa ng bawat ahente, turn by turn, na may replay
- **Gastos at token**: kada runtime, modelo, session at araw, na may mga anomaly flag
- **Flow**: live na diagram ng mga mensaheng gumagalaw sa mga channel, modelo, at tool
- **Brain**: ang stream ng kaisipan at tool-call event habang nangyayari ito
- **Context blowout**: laki ng window na naaangkop kada provider, compaction laban sa sapilitang overflow, kasama ang mapa kada runtime ng kung ano ang *hindi* namin makita ([paano](docs/CONTEXT_BLOWOUT.md))
- **Memory at skills**: ang mga file at skill na talagang na-load ng bawat runtime
- **Health at logs**: disk, memory, error rate, rate limit, live log stream
- **Alerts**: budget cap, error spike, agent-offline, iniruruta sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: i-pause ang mapanganib na tool call *bago* ito tumakbo at aprubahan mula sa iyong telepono ([paano](docs/APPROVALS.md))

## Context blowout, at ang halaga ng pagmamasid

Dalawang tanong na sulit sagutin bago ka magtiwala sa anumang tool na naghahambing ng ahente.

**Paano nito hinahawakan ang context-window blowout sa iba't ibang runtime?**

Ang isang utilization percentage ay kasing-tapat lang ng hinahatian nito. Sinusukat ng ClawMetry
ang window kada provider mula sa [isang table na mababasa at maaaring i-PR](clawmetry/context_windows.py),
sumasaklaw sa Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama, at GLM. Hindi
nito sinusukat lahat ng 32 runtime gamit ang panukat ng isang vendor lamang. Mahalaga ito: isang
300K na turn ng GPT-5 na sinukat gamit ang 200K ng Anthropic ay babasahin bilang ">100%, sumabog"
gayong nasa 75% lamang ito ng 400K ng GPT-5. Ang parehong panukat ay nagtatago sa isang tunay na
umapaw na 130K na turn ng DeepSeek bilang komportableng 65%.

Bawat window ay may kasamang provenance: `model_table`, `explicit_marker`,
`observed_floor`, o isang tapat na `default` kapag hindi namin alam ang modelo. Ang isang gauge
na binuo sa isang hula ay hindi kailanman magre-render nang may parehong awtoridad gaya ng isa na
binuo sa isang lookup.

Nakikita lamang ng ClawMetry ang mga compaction event sa ilang runtime. Kaya iniuulat ng
`GET /api/context-coverage`, kada runtime, kung ang isang **zero ay ibig sabihin "tumakbo nang
malinis" o "bulag kami"**. Ang isang `0` na talagang ibig sabihin ay bulag ay sinasabi nito.
[Buong detalye](docs/CONTEXT_BLOWOUT.md)

**Magkano ang gastos ng instrumentation?**

| Landas | Idinagdag sa iyong ahente | Default? |
|---|---|---|
| Session-file tailing (lahat ng 32 runtime) | **0**. Hiwalay na proseso, walang code ng ClawMetry sa iyong ahente | naka-on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** kada LLM call, o 0.009% ng 5s na tawag | naka-off |
| Pre-tool hook gate (warm cache) | **+44 ms** kada gated tool call, higit sa 36 ms na interpreter floor | naka-off |
| Enforcement proxy | **+9.7 ms** kada LLM call | naka-off |

Gastos sa daemon host: **2,762 event/segundo** na ingest, **710 bytes/event** sa disk
(67.7 MB kada 100k na event), at **~12% ng isang core** na sustenido sa isang abalang install. Ang
huling numerong iyon ay higit sa aming sariling nakasaad na 5-10% na badyet, kaya inilathala ito
bilang isang bug na hahabulin sa halip na alisin sa pahina.

Sinukat sa Apple M2 Pro gamit ang `benchmarks/overhead.py`. Pinapatakbo ng harness ang bawat
kundisyon sa hiwalay na proseso, pinagpapalit-palit ang pagkakasunod-sunod nito, at **tumatangging
mag-print ng numero kapag hindi magkatugma ang mga round sa senyales nito**. Patakbuhin ito sa iyong
sariling makina sa loob ng isang minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Nasusukat ang bawat landas, kasama ang mga hook gate at ang enforcement proxy, at pinapatakbo ng
harness sa Linux, macOS, at Windows sa CI. Dalawang resulta na sulit malaman: humigit-kumulang
pitong beses na mas mataas ang gastos ng proxy sa Windows kumpara sa Linux, at sa kasalukuyan ay
sustenido ang daemon sa humigit-kumulang 12% ng isang core, higit sa aming sariling 5-10% na
badyet. Ang hilaw na JSON, ang metodo, at kung ano pa ang hindi pa nasusukat ay nasa
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Presyo

| Plano | Ano ang saklaw nito | Presyo |
|---|---|---|
| **Libre** | OpenClaw + NVIDIA NemoClaw + Goose, buong dashboard, local lamang | $0 |
| **Starter** | Bawat ibang runtime sa itaas, fleet view, cloud sync | $9 kada node / buwan |
| **Pro** | Starter + kontrol at ebalwasyon: approvals, tool-risk policy, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 kada node / buwan |

Ang mga taunang plano, Enterprise, at ang kasalukuyang mga numero ay nasa
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Gumagana ang mga self-hosted license
key nang walang cloud (`clawmetry license`). Ang eksaktong hati ng libre/bayad ay nasa
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Nananatili sa iyong makina ang iyong datos

Binabasa ng ClawMetry ang mga lokal na session file at log. **Walang datos ng session na lalabas
sa iyong makina maliban kung patakbuhin mo ang `clawmetry connect`** — walang prompt, tugon, tool
argument, laman ng file, o linya ng log. Kapag kumonekta ka, ang snapshot ay end-to-end
encrypted gamit ang isang key na hindi kailanman umaalis sa iyong makina, at dine-decrypt sa iyong
browser. Kung walang key ang isang node, lalaktawan ang upload sa halip na ipadala nang hindi naka-
encrypt, at walang tugon ng server ang makakapagpatay dito.

May dalawang bagay na tumatakbo bilang default bago ka kumonekta, parehong opt-out at wala sa mga
ito ang nagdadala ng datos ng session: isang anonymous install ping at isang version check laban
sa PyPI. Ang isang default na install ay naghahanap din ng iyong pampublikong IP nang minsan para
sa isang startup banner line. Bawat destinasyon, kung ano ang dinadala nito, at kung paano ito
i-off ay nakalista sa [docs/EGRESS.md](docs/EGRESS.md); ang mga self-hosted, repointed, at
air-gapped na install ay hindi gumagawa ng anumang discretionary na outbound call.

Nangyayari ang decryption sa iyong browser, gamit ang code na ipinapadala namin sa iyo. Isang
pangako ito dati; isang bagay na na ngayon ay mave-verify mo. Bawat linya na humihipo sa iyong key
ay nasa isang mababasang file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
na kasama sa loob ng wheel at ipinapadala nang literal, na naka-pin gamit ang isang Subresource
Integrity hash. Para kumpirmahin na ang browser ay nagpapatakbo ng inilathala namin:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ang hindi napapatunayan nito: kami ang nagpapadala ng pahina na nag-lo-load ng file, kaya
maaari kaming magpadala ng ibang pahina. Pinoprotektahan ng mga integrity hash mula sa isang
nakompromisong CDN, hindi mula sa vendor. Ang nakukuha mo ay dapat sinasadya, nakikita sa source
ng pahina, at naiiba sa isang artifact sa PyPI na kayang kunin ninuman ang anumang substitution.
Ang pag-self-host o pananatiling local-only ay ganap na nag-aalis ng dependency na ito.

## Pag-install

```bash
pip install clawmetry     # pagkatapos: clawmetry
```

O ang one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kailangan ng Python 3.8+ sa macOS, Linux, o Windows, at hindi bababa sa isang agent runtime sa
parehong makina. Mga tagubilin sa Docker: [docs/DOCKER.md](docs/DOCKER.md).

O hayaan ang ahente ang mag-setup para sa iyo. Tinuturuan ng skill na [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ang Claude Code, Codex, Cursor, Gemini CLI, Copilot, o OpenCode na i-install ang ClawMetry, iulat
kung ano ang ginagawa at ginagastos ng mga ahente sa makina, ihinto ang isang session kapag
hiniling, at panatilihing naka-hold ang mapanganib na tool call para sa pag-apruba:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Mga Dokumento

| | |
|---|---|
| [Pagkakatugma ng runtime](docs/compatibility.md) | Ano ang binabasa ng bawat adapter, at paano magdagdag ng runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Mga window kada provider, compaction laban sa overflow, saklaw kada runtime |
| [Overhead](docs/OVERHEAD.md) | Magkano ang gastos ng instrumentation, sinukat, kasama ang harness para ulitin ito |
| [Entitlements](docs/ENTITLEMENTS.md) | Libre laban sa bayad, tier matrix, license CLI |
| [Approvals at policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, pag-apruba sa telepono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | I-export ang mga trace kahit saan, mag-ingest ng OTLP mula sa kahit ano |
| [Gamitin ang sarili mong ahente](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain nang end to end, na may mga runnable na halimbawa |
| [SDK tracking](docs/SDK_TRACKING.md) | Attribution ng gastos para sa mga ahenteng sarili mong ginawa |
| [Mga chat channel](docs/CHANNELS.md) | Ang mga chat adapter na ipinapakita sa Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Mga sandboxed na setup ng NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Arkitektura](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Kung paano ito gumagana sa loob; pagpapatakbo mula sa source |
| [Telemetry](docs/TELEMETRY.md) | Ang anonymous install at desktop-open pings, at kung paano i-off ang mga ito |

## Mga Screenshot

Bawat numero sa ibaba ay mula sa isang tunay na makina, read-only, na walang anumang inihasik.

**Sinasabi nito sa iyo kung may mali, hindi lang kung ano ang nangyari.**
Dalawang anomaly banner sa itaas: gastos na tumatakbo nang 7x sa pang-araw-araw na average, at
isang 4.2x na cost spike. Sa ibaba nito, 324 sa 667 kamakailang session ang may dalang waste
signal, na nakalista ayon sa dahilan.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ipinapakita nito sa iyo kung saan napunta ang pera, sa bawat window.**
$252.47 ngayon, $513.15 sa linggong ito, $1,312.92 sa buwang ito, bawat isa ay may kasamang mga
token sa likod nito at kung gaano karami ang saklaw na ng iyong subscription. Sa ibaba niyan, mga
$1,128/buwan na nakalista bilang recoverable at $17,256/buwan na nasagip na sa pamamagitan ng
cache reuse.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Iginuguhit nito kung paano nagiging sagot ang isang mensahe.**
Ang live flow diagram: ikaw, ang channel kung saan ito dumating, ang gateway, ang modelong
sumasagot ngayon mismo, at bawat tool na kinuha nito. Nagliliwanag ang mga node habang gumagalaw
ang trabaho sa mga ito.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Bawat ahente sa makina, sa isang table.**
Ano ang pinapatakbo nito, magkano ang gastos nito sa nakaraang 24 oras at sa buong buhay nito,
kailan ito huling nakita, sino ang may-ari nito, at kung sinasaklaw ba ito ng isang subscription.
14 na ahente rito, 3 session na gumagana, 13 tahimik.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ipinapakita nito kung saan napunta ang oras at pera ng isang turn, tool por tool.**
Isang turn ng isang tunay na session: 11 tool sa loob ng 11.2 minuto para sa $1.16. Bawat Bash
call at model call ay may sariling bar sa timeline, kaya ang command na tumakbo nang 4.1 minuto
at ang isa na tumakbo nang 226ms ay agad na makikilala.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ginagradu nito ang trabaho, hindi lang ang gastos.**
Isang A ngayong linggo: 54 na gawain ang bumalik nang malinis, 2 magaspang na nagkahalaga ng
$48.57, at ang mga run na may masyadong kaunting aktibidad para husgahan ay hindi isinama sa
grado sa halip na bilangin bilang panalo. Bawat magaspang na run ay naka-link sa trace nito.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ipinapakita nito kung bakit patuloy na napupuno ang context window.**
715K ng 1M-token na window sa pinakahuling turn, isang 83.3% na peak, 4 na compaction na
proactive lahat sa halip na dahil sa overflow, at ang utilisasyon ng bawat turn sa likod nito.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tumatakbo ang detection nang hindi mo kailangang mag-configure ng kahit ano.**
Naka-on na ang mga built-in na detector mula sa pag-install: tumahimik ang ahente, huminto ang
telemetry feed, cost spike, token burst, umaakyat na error, error spike, budget threshold,
threat signature na natugma, security tool finding, nagbago ang security posture. Opsyonal ang
sarili mong mga panuntunan sa ibabaw nito.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Ang pag-hold sa isang mapanganib na tawag ay opt-in, at naka-off bilang default.**
Ang recursive deletes, force push, sudo, secrets, package install, at outbound call ay bawat isa
ay may panuntunang maaari mong i-on. Hanggang hindi mo ito ginagawa, nagmamasid lang ang
ClawMetry at walang binabago. Kapag naka-on na ang isa, ang mga tumutugmang tawag ay maghihintay
dito (o sa iyong telepono) para sa isang aprubahan o tanggihan.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Higit pa, kada runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Pagkilala

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
