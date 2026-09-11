<!-- i18n-src:12b97259721e -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ang isang agent ay maaaring gumawa ng isandaang tool call nang hindi umuusad.** Binabasa ng ClawMetry
ang mga session file na isinusulat na ng iyong mga coding agent, at inilalagay ang timeline,
ang mga tool call at anumang datos ng token at gastos na inilalantad ng runtime sa isang
pananaw — para masabi mo kung ang isang mahabang takbo ay gumagana o natigil na lang.

Gumagana sa **31 AI agent runtime** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 27 pa. Isang dashboard para sa buong fleet ng iyong agent. ([kumpletong listahan](SUPPORTED_RUNTIMES.txt), nabuo mula sa catalogue.)

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Walang configuration. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900**. Walang configuration: nahahanap nito ang mga agent runtime na
mayroon ka na, binabasa ang mga ito nang read-only, at walang binabago sa kung paano sila tumatakbo.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bago mag-install

| | |
|---|---|
| **Ano ang ginagawa nito** | Binabasa ang mga session file at log na isinusulat na ng iyong mga agent. Walang SDK, walang pagbabago sa code, walang instrumentation sa app mo. |
| **Ano ang makikita mo** | Session timeline, tool-by-tool replay, breakdown ng token at gastos, at mga trajectory signal (paikot-ikot, paulit-ulit na kabiguan) — kada runtime. |
| **Ano ang libre** | Binabasa ng `pip install clawmetry` ang **OpenClaw, NVIDIA NemoClaw, at Goose** nang walang account, walang key, at walang network call. Ang ibang 27 — Claude Code, Codex, Cursor at iba pa — ay binabasa ng closed-source na kasamang `clawmetry-pro`, na kasama sa 7-araw na trial o sa isang plano — tingnan ang [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) para sa eksaktong paghahati. |
| **Paano magsimula** | `pip install clawmetry && clawmetry`, pagkatapos buksan ang localhost:8900. Wala pang agent sa makinang ito? Binubuksan ng `clawmetry --sample` ang tatlong may-label na synthetic session. |
| **Ano ang umaalis sa iyong makina** | Walang session data, maliban kung patakbuhin mo ang `clawmetry connect`. May dalawang bagay na tumatakbo bilang default, pareho itong opt-out at wala sa kanila ang nagdadala ng session content: isang anonymous na install ping at isang PyPI version check. Nakalista ang bawat destinasyon sa [docs/EGRESS.md](docs/EGRESS.md), binuo mula sa wire capture sa halip na mula sa pagbasa ng mga komento. |

May dalawang limitasyon na dapat malaman bago husgahan ang resulta: naglalantad ang mga runtime ng
ibang-ibang datos (may ilang hindi naglalabas ng gastos — [ang matrix](docs/compatibility.md)
ang nagsasabi kung alin, kada runtime), at ang pag-obserba sa isang aksyon ay hindi katulad ng
kakayahang harangin ito ([alin sa mga kontrol ang totoo, kada runtime](docs/APPROVALS.md)).


## Gumagana sa 31 agent runtime

**Libre sa open source na app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Sa bayad na plano:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Iisang dashboard para sa lahat ng runtime. Patakbuhin ang ilan nang sabay at
ise-reset ng switcher sa header ang bawat tab papunta sa isa sa kanila.

Ginawa mo ba ang sarili mong agent gamit ang isang SDK? Sinusubaybayan din ng interceptor ang mga LLM call nito.
Tingnan ang [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Ano ang makukuha mo

- **Mga Session at transcript**: kung ano ang ginawa ng bawat agent, turn by turn, na may replay
- **Gastos at Token**: kada runtime, modelo, session at araw, na may mga anomaly flag
- **Flow**: live na diagram ng mga mensaheng dumadaan sa mga channel, modelo, at tool
- **Brain**: ang stream ng reasoning at tool-call event habang nangyayari ito
- **Context blowout**: laki ng window ayon sa provider, compaction laban sa sapilitang overflow, kasama ang mapa kada runtime ng hindi natin *makikita* ([paano](docs/CONTEXT_BLOWOUT.md))
- **Memory at skills**: ang mga file at skill na talagang na-load ng bawat runtime
- **Health at logs**: disk, memory, error rate, rate limit, live na log stream
- **Alerts**: mga budget cap, error spike, agent-offline, ipinapadala sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: i-pause ang mapanganib na tool call *bago* ito tumakbo at aprubahan mula sa iyong telepono ([paano](docs/APPROVALS.md))

## Context blowout, at ang gastos ng pagmamanman

Dalawang tanong na sulit sagutin bago ka manalig sa anumang tool na naghahambing ng agent.

**Paano nito hinahandle ang pag-blowout ng context-window sa iba't ibang runtime?**

Ang porsyentong utilization ay kasing-tapat lang ng kung ano ang hinahati nito. Sinusukat ng ClawMetry
ang laki ng window kada provider mula sa [isang table na puwede mong basahin at
i-PR](clawmetry/context_windows.py), na sumasaklaw sa Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama, at GLM. Hindi nito sinusukat ang lahat ng 31
runtime gamit ang panukat ng iisang vendor. Mahalaga iyon: ang isang 300K na GPT-5 turn na
sinukat gamit ang 200K ni Anthropic ay babasahing ">100%, sumabog" kahit na ito ay 75% lamang
ng 400K ng GPT-5. Ang parehong panukat ay nagtatago ng isang talagang na-overflow na 130K na DeepSeek turn
bilang isang komportableng 65%.

Bawat window ay may kasamang provenance nito: `model_table`, `explicit_marker`,
`observed_floor`, o isang tapat na `default` kapag hindi natin alam ang modelo. Ang isang gauge na
binuo sa isang hula ay hindi kailanman lumalabas nang may parehong awtoridad ng isang binuo
mula sa isang lookup.

Nakikita lang ng ClawMetry ang mga compaction event sa ilang runtime. Kaya iniuulat ng
`GET /api/context-coverage`, kada runtime, kung ang isang zero ay nangangahulugang **"tumakbo nang
malinis" o "bulag tayo"**. Ang `0` na talagang ibig sabihin ay bulag ay sinasabi nito.
[Buong detalye](docs/CONTEXT_BLOWOUT.md)

**Magkano ang gastos ng instrumentation?**

| Landas | Idinagdag sa iyong agent | Default? |
|---|---|---|
| Pag-tail ng session-file (lahat ng 31 runtime) | **0**. Hiwalay na proseso, walang code ng ClawMetry sa iyong agent | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** kada LLM call, o 0.009% ng isang 5s call | off |
| Pre-tool hook gate (warm cache) | **+44 ms** kada gated na tool call, sa ibabaw ng 36 ms na interpreter floor | off |
| Enforcement proxy | **+9.7 ms** kada LLM call | off |

Gastos ng daemon host: **2,762 events/sec** na ingest, **710 bytes/event** sa disk
(67.7 MB kada 100k event), at **~12% ng isang core** nang sustenido sa isang abalang
install. Ang huling numerong iyon ay lampas sa ating sariling nakasaad na 5-10% na
budget, kaya inilalathala ito bilang isang bug na dapat habulin sa halip na iwan sa labas ng pahina.

Sinukat sa isang Apple M2 Pro gamit ang `benchmarks/overhead.py`. Pinapatakbo ng harness
ang bawat kondisyon sa hiwalay na proseso, pinagpapalit-palit ang pagkakasunod-sunod nila, at
**tumatanggi na mag-print ng numero kapag hindi magkatugma ang mga round sa sign nito**. Patakbuhin ito
sa sarili mong makina sa loob ng isang minuto:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Sinusukat ang bawat landas, kasama ang mga hook gate at ang enforcement proxy,
at pinapatakbo ng harness sa Linux, macOS at Windows sa CI. May dalawang resulta na
sulit malaman: mga pitong beses na mas mahal ang proxy sa Windows kaysa sa Linux, at
kasalukuyang sustenido ng daemon ang halos 12% ng isang core, lampas sa ating sariling 5-10% na
budget. Ang raw JSON, ang metodo, at kung ano pa ang hindi pa nasusukat ay nasa
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Presyo

| Plano | Ano ang saklaw nito | Presyo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, buong dashboard, local lang | $0 |
| **Starter** | Bawat ibang runtime sa itaas, fleet view, cloud sync | $9 kada node / buwan |
| **Pro** | Starter + control at evaluation: approvals, tool-risk policy, eval, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 kada node / buwan |

Ang mga taunang plano, Enterprise, at ang mga kasalukuyang numero ay nasa
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Gumagana ang mga self-hosted na
license key nang walang cloud (`clawmetry license`). Ang eksaktong paghahati ng free/bayad ay nasa
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Nananatili ang iyong datos sa iyong makina

Binabasa ng ClawMetry ang mga local na session file at log. **Walang session data na
umaalis sa iyong makina maliban kung patakbuhin mo ang `clawmetry connect`** — walang prompt, sagot,
argumento ng tool, laman ng file o linya ng log. Kapag kumonekta ka, ang snapshot ay end-to-end
naka-encrypt gamit ang key na hindi kailanman umaalis sa iyong makina, at nade-decrypt sa iyong
browser. Kung walang key ang isang node, laktawan ang upload sa halip na ipadala nang bukas, at
walang tugon ng server na makapagpapatay niyan.

May dalawang bagay na tumatakbo bilang default bago ka kumonekta, pareho itong opt-out at wala
sa kanila ang nagdadala ng session data: isang anonymous na install ping at isang version check laban sa
PyPI. Ang default na pag-install ay minsan ding nagta-lookup ng iyong public IP para sa isang linya ng
banner sa startup. Bawat destinasyon, ang laman nito at kung paano ito i-off ay nakalista sa
[docs/EGRESS.md](docs/EGRESS.md); ang mga self-hosted, na-repoint, at air-gapped na install ay
walang ginagawang discretionary na outbound call.

Nangyayari ang decryption sa iyong browser, sa code na ibinibigay namin sa iyo. Dati itong isang
pangako lang; ngayon isa na itong bagay na puwede mong suriin. Bawat linya na humihipo sa iyong key
ay nasa isang mababasang file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
na kasama sa loob ng wheel at ibinibigay nang verbatim, naka-pin gamit ang Subresource
Integrity hash. Para kumpirmahin na tumatakbo ang browser ng inilathala namin:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Ano ang hindi napapatunayan niyan: ibinibigay namin ang pahinang nag-load ng file, kaya
puwede kaming magbigay ng ibang pahina. Ang mga integrity hash ay pinoprotektahan ka mula sa isang
na-compromise na CDN, hindi mula sa vendor. Ang nakukuha mo ay ang anumang pagpapalit ay kailangang
sinadya, nakikita sa page source, at iba mula sa artifact sa PyPI na kahit sino ay puwedeng kunin.
Ang pag-self-host o pananatili sa local-only ay ganap na nag-aalis ng pag-asa dito.

## Pag-install

```bash
pip install clawmetry     # pagkatapos: clawmetry
```

O ang one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kailangan ng Python 3.8+ sa macOS, Linux o Windows, at kahit isang agent runtime sa
parehong makina. Mga instruksyon sa Docker: [docs/DOCKER.md](docs/DOCKER.md).

O hayaan ang agent na mag-set up para sa iyo. Tinuturuan ng skill na [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ang Claude Code, Codex, Cursor, Gemini CLI, Copilot o OpenCode na
i-install ang ClawMetry, iulat kung ano ang ginagawa at ginagastos ng mga agent sa makina,
itigil ang isang session kapag hiniling, at panatilihing naka-hold ang mga mapanganib na tool call para sa approval:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Mga Dokumento

| | |
|---|---|
| [Compatibility ng runtime](docs/compatibility.md) | Ano ang binabasa ng bawat adapter, at paano magdagdag ng runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Mga window kada provider, compaction laban sa overflow, coverage kada runtime |
| [Overhead](docs/OVERHEAD.md) | Ano ang gastos ng instrumentation, sinukat, kasama ang harness para maulit ito |
| [Entitlements](docs/ENTITLEMENTS.md) | Libre laban sa bayad, tier matrix, license CLI |
| [Approvals at policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, mga approval sa telepono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | I-export ang mga trace kahit saan, mag-ingest ng OTLP mula sa kahit ano |
| [Dalhin ang sarili mong agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end to end, na may mga tatakbong halimbawa |
| [SDK tracking](docs/SDK_TRACKING.md) | Cost attribution para sa mga agent na sarili mong ginawa |
| [Mga chat channel](docs/CHANNELS.md) | Ang mga chat adapter na ipinapakita sa Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Mga sandboxed na setup ng NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Paano ito gumagana sa loob; pagpapatakbo mula sa source |
| [Telemetry](docs/TELEMETRY.md) | Ang mga anonymous na install at desktop-open ping, at kung paano ito i-off |

## Mga Screenshot

Bawat numero sa baba ay mula sa isang tunay na makina, read-only, walang seeded na datos.

**Sinasabihan ka nito kung may mali, hindi lang kung ano ang nangyari.**
Dalawang anomaly banner sa itaas: gastos na tumatakbo nang 7x sa araw-araw na average, at isang
4.2x na cost spike. Sa ibaba nila, 324 sa 667 na kamakailang session ang may dalang waste
signal, na hinati-hati ayon sa sanhi.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ipinapakita nito kung saan napunta ang pera, sa bawat window.**
$252.47 ngayong araw, $513.15 ngayong linggo, $1,312.92 ngayong buwan, bawat isa may
katumbas na token at kung gaano karami nito ang saklaw na ng subscription mo. Sa ibaba niyan,
mga $1,128/buwan na nakalista bilang recoverable at $17,256/buwan na nasagip na ng
muling paggamit ng cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Iginuhit nito kung paano nagiging sagot ang isang mensahe.**
Ang live na flow diagram: ikaw, ang channel na kinarating nito, ang gateway, ang modelong
sumasagot ngayon mismo, at bawat tool na ginamit nito. Nagliliwanag ang mga node habang dumadaan
ang trabaho sa kanila.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Bawat agent sa makina, sa isang table.**
Ano ang tumatakbo nito, magkano ang gastos nito sa huling 24 oras at sa buong buhay nito, kailan
ito huling nakita, sino ang may-ari, at kung sinasaklaw ba ito ng isang subscription. 14 na agent dito,
3 session na gumagana, 13 tahimik.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ipinapakita nito kung saan napunta ang oras at pera ng isang turn, tool by tool.**
Isang turn ng tunay na session: 11 tool sa loob ng 11.2 minuto para sa $1.16. Bawat Bash
call at model call ay may sariling bar sa timeline, kaya ang command na tumakbo ng 4.1 minuto
at ang tumakbo ng 226ms ay agad na makikilala.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ginagrade nito ang trabaho, hindi lang ang gastos.**
Isang A ngayong linggo: 54 na gawain ang bumalik nang malinis, 2 magaspang ang nagkahalaga ng
$48.57, at ang mga takbong may kulang na aktibidad para husgahan ay iniiwan sa labas ng grade sa
halip na bilangin bilang panalo. Bawat magaspang na takbo ay may link sa sarili nitong trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ipinapakita nito kung bakit patuloy na napupuno ang context window.**
715K sa 1M-token na window sa pinakahuling turn, isang 83.3% na peak, 4 na compaction na
lahat ay nag-fire nang proactive sa halip na sa overflow, at ang utilization ng bawat turn
sa likod niyan.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tumatakbo ang detection nang hindi mo kailangang mag-configure ng anuman.**
Naka-on na ang built-in na mga detector mula sa pag-install: tumahimik ang agent, huminto ang
telemetry feed, cost spike, token burst, tumataas na error, error spike, budget threshold,
tumugma ang threat signature, natagpuan ng security tool, nagbago ang security posture. Opsyonal
ang sarili mong mga rule sa ibabaw nito.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Opt-in ang pag-hold sa isang mapanganib na tapos, at naka-off ito bilang default.**
Ang recursive delete, force push, sudo, secrets, pag-install ng package, at outbound call ay
bawat isa ay may rule na puwede mong i-on. Hangga't hindi mo iyon ginagawa, nagmamanman lang ang
ClawMetry at walang binabago. Kapag naka-on na ang isa, ang mga tumutugmang tawag ay naghihintay
dito (o sa iyong telepono) para sa approve o deny.

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
