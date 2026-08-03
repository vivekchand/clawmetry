<!-- i18n-src:0e34918f8f2e -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang iyong agent habang nag-iisip.** Real-time observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, at 10 pa. Isang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [marami pa →](docs/i18n/)

Isang command lang. Walang kailangang i-configure. Awtomatikong dinedetect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Magbubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong agent fleet** mo sa isang dashboard, na awtomatikong nakikita ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

Libre ang OpenClaw at NemoClaw sa open-source app; buhay naman ang ibang runtime gamit ang ClawMetry Cloud o isang self-hosted Pro license. Palitan ang runtime mula sa header at ang bawat tab — cost, tokens, tools, traces — ay muling isasaayos batay sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong hati ng free/paid, tier matrix, ang hugis ng `/api/entitlement`, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live animated diagram na nagpapakita kung paano dumadaloy ang mga mensahe sa mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng session, impormasyon ng model
- **Usage** — Pagsubaybay sa token at cost na may daily/weekly/monthly breakdown
- **Sessions** — Aktibong mga agent session kasama ang model, tokens, huling aktibidad
- **Crons** — Mga naka-iskedyul na trabaho kasama ang status, susunod na takbo, tagal
- **Logs** — Color-coded real-time log streaming
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, mga araw-araw na tala
- **Transcripts** — Chat-bubble UI para sa pagbasa ng kasaysayan ng session
- **Alerts** — Mga budget cap, error-rate trigger, agent-offline detection; nire-route sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — I-gate ang mga destructive delete, force push, DB mutation, sudo, pag-install ng package, network call sa likod ng one-click sign-off

## Mga Screenshot

### 🧠 Brain — Live agent event stream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Buod ng token usage at session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time tool call feed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Breakdown ng cost ayon sa model at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace file browser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget cap, error-rate trigger, webhook papunta sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — I-gate ang mga mapanganib na tool call sa likod ng manual sign-off; mga patakarang suportado ng policy
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang para mag-install ng
PreToolUse hook na nagpapahinto sa mga tumutugmang tool call *bago pa* ito tumakbo at
naghihintay ng iyong desisyon (isang tap lang mula sa iyong telepono kapag naka-enable ang
[cloud push notifications](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # sinusulat ang ~/.claude/settings.json (idempotent)
clawmetry hooks status      # kung ano ang naka-wire + ilang policy ang aktibo
clawmetry hooks uninstall   # tinatanggal lamang ang mga entry ng ClawMetry
```

Isang deny ay bina-block lamang ang isang tool call na iyon — mananatili ang session ng agent at maaari itong subukan ng ibang paraan. Ang pag-approve mula sa telepono mo ay lumalaktaw sa sariling permission prompt ng Claude Code (nasagot mo na ito). Ang mga hindi tumutugmang tool ay nagkakahalaga lamang ng ~40ms at bumabalik sa normal na permission flow ng Claude Code. Makakatanggap ka rin ng phone push kapag ang Claude Code mismo ay naghihintay sa iyo (`permission_prompt` / `idle_prompt` na mga notification).

## Pag-install

**One-liner (inirerekomenda):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Mula sa source:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Frontend Development

Ang v2 React app ay nasa `frontend/` at nasi-serve sa `/v2` kapag ang Flask
server ay sinimulan na naka-enable ang v2.

Gumamit ng dalawang terminal habang nagde-develop:

```bash
# Terminal 1: Flask API/server sa :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server sa :5173
cd frontend
nvm use
npm ci
npm run dev
```

Buksan ang `http://localhost:5173/v2/`. Ang Vite ay nagpo-proxy ng mga `/api` request patungo sa
`http://localhost:8900`, kaya ang React app ay makakapag-usap sa lokal na Flask server
nang walang karagdagang CORS setup.

Para i-build ang bundle na isasama sa Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isinusulat sa `clawmetry/static/v2/dist/`.

## Pagkakatugma ng Runtime / Agent

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lamang ang OpenClaw. Bawat runtime maliban sa OpenClaw ay may kasamang dedikadong reader adapter na nagsasalin ng native session format nito papunta sa unified na hugis ng ClawMetry; ino-ingest ito ng daemon papunta sa parehong DuckDB store + cloud snapshot, na naka-tag ayon sa runtime, at ipinapakita ng Session replay tab ang isang **runtime switcher** kapag mahigit isa ang naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix + gabay sa pagdaragdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa OpenClaw-family primer.

Pinapatakbo mo ba ang [numbat ni Perplexity](https://github.com/perplexityai/numbat), ang agent-security tool? Ino-ingest ng ClawMetry ang mga natuklasan at desisyon nito sa enforcement nang walang karagdagang configuration — tingnan ang [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
| **PicoClaw** | Beta adapter | Flat na `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool calls. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/cost. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool calls + thinking, token usage. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, model, tool calls, token usage. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, model. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat proyekto. Transcripts, model, token counts. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool calls, token totals. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool calls, tokens + cost. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool calls, token usage. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool calls, tokens + cost. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool calls, tokens + cost. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Workflow executions, node runs, AI Agent prompts, model + tokens kung saan naitatala ito ng n8n. |
| **Antigravity** | Beta adapter | Brain JSONL sa ilalim ng `~/.gemini/<flavor>/brain/`. Mga usapan, tool steps, thinking, per-generation na hati ng Gemini token + cost, background-generation na paggamit. |
| **GitHub Copilot** | Beta adapter | Copilot CLI `events.jsonl` sa ilalim ng `~/.copilot/session-state/` + ang `session-store.db` na per-call usage ledger. Mga usapan, tool calls, model routing, cache-aware na hati ng token, vendor-billed na AI-credit cost. |

Ang ibig sabihin ng "Beta adapter" ay may reader ang ClawMetry para sa aktwal na on-disk format ng runtime na iyon, na bawat isa ay binuo + na-verify laban sa tunay na install sa tunay na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Read-only ang mga adapter; tapat ang bawat isa tungkol sa aktwal na itinatago ng runtime nito (hal. hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, isinasaayos ng runtime switcher ang sessions view sa isa para sa malinaw na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop cost attribution

Ang mga runtime sa itaas ay pawang isinusulat ang mga session sa disk. Ang sarili mong **production agent** — ang binuo mo gamit ang OpenAI Agents SDK, LangChain, ang Vercel AI SDK, LlamaIndex, E2B, o isang plain `httpx` loop — ay hindi. Nakukuha pa rin ng zero-config interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching ng `httpx`/`requests`:

```python
import clawmetry.track            # i-activate ang interceptor
clawmetry.track.set_source("support-agent")   # pangalanan ang produktong ito

# ...tumatakbo ang agent mo nang normal; bawat LLM call ay natutunton + na-attribute na ngayon.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` env var) ay nagta-tag sa bawat call gamit ang isang **pinangalanang source**, kaya bawat produktong iyong pinapatakbo ay lumalabas bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview — mga call, providers, latency, error rate bawat agent. Walang naka-set na source? Natutunton pa rin ang mga call, nananatili lamang na nakatago ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya ang out-loop sources ay nagsi-sync sa cloud dashboard tulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong mga trace kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa magkabilang direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang mga trace ng agent mo sa isang tool lamang.

**I-export** ang bawat session — mga LLM call, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o sarili mong OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# katumbas:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Opsyonal ang mga auth header at poll interval bilang env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # karagdagang HTTP header
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # segundo (default 60)
```

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang mga trace at metrics mula sa iba pa sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na dashboard ng ClawMetry **at** ang data mo sa anumang backend na ginagamit na ng team mo — walang lock-in, walang pangalawang agent na kailangang i-install.

## Configuration

Karamihan sa mga tao ay hindi na kailangan ng anumang config. Awtomatikong dinedetect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mo talagang mag-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # I-bind sa localhost lamang
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Ang pangalan mo sa Flow visualization
```

Lahat ng opsyon: `clawmetry --help`

## Mga Sinusuportahang Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na na-configure mo. Ang mga channel na aktwal na naka-setup lamang sa iyong `openclaw.json` ang lumalabas sa Flow diagram — ang mga hindi na-configure ay awtomatikong itinatago.

I-click ang anumang channel node sa Flow para makita ang live chat bubble view na may bilang ng papasok/palabas na mensahe.

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mga mensahe, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel detection |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel detection |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in web UI sessions |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage sa pamamagitan ng BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Sa pamamagitan ng Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Sa pamamagitan ng Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted na team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, may suporta sa E2EE |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized na NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat sa pamamagitan ng IRC connection |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ire-render lamang ang mga channel na aktwal mong na-configure. Walang kinakailangang manual setup.

## Docker Deployment

Gusto mo bang patakbuhin ang ClawMetry sa loob ng container? Walang problema! 🐳

**Quick start gamit ang Docker:**

```bash
# I-build ang image
docker build -t clawmetry .

# Patakbuhin gamit ang default na settings
docker run -p 8900:8900 clawmetry

# O i-mount ang data dir ng agent mo (ipinakita: ang ~/.openclaw ng OpenClaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Halimbawang Docker Compose:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **Tandaan:** Kapag tumatakbo sa loob ng Docker, i-mount ang data + log directories ng agent mo (hal. `~/.openclaw`, `~/.claude`, `~/.codex`) para madetect ng ClawMetry ang setup mo.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong na-install sa pamamagitan ng pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, o GitHub Copilot (o naka-mount na volume para sa Docker)
- Linux o macOS

## Suporta para sa NemoClaw / OpenShell

Awtomatikong dinedetect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed OpenShell container.

Karaniwan nang walang karagdagang configuration na kinakailangan. Awtomatikong tinutuklas ng sync daemon ang mga session file kung nasa `~/.openclaw/` man ito sa host o sa loob ng OpenShell container.

### Paano ito gumagana

Dinedetect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sinusuri ang mga tumatakbong Docker container para sa mga imahe na `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na na-sync mula sa mga container ng NemoClaw ay naka-tag ng `runtime=nemoclaw` at `container_id` na metadata sa cloud dashboard, kaya makikilala mo ang mga ito sa isang tingin bilang kaiba sa karaniwang mga session ng OpenClaw.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Naiiwasan nito ang mga restriction ng network policy ng NemoClaw.

```bash
# Sa host (labas ng sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong hahanapin ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell container.

### Opsyonal: tahasang pangalan ng sandbox

Kung hindi gumana ang auto-detection, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, idagdag ang egress rule na ito sa iyong NemoClaw network policy para maabot nito ang ClawMetry ingest API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

I-apply gamit ang:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Mga Port at Endpoint

| Endpoint | Port | Protocol | Kinakailangan |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oo (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Oo (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa container session discovery |

Ang sync daemon ay gumagawa lamang ng outbound HTTPS call patungo sa `ingest.clawmetry.com`. Walang kinakailangang inbound port.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa mga SSH tunnel, reverse proxy, at Docker.

## Testing

Sinusubok ang proyektong ito gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng anonymous na install-lifecycle ping papunta sa
`https://app.clawmetry.com/api/install`: isang `install` ping sa unang
pagpapatakbo mo ng `clawmetry` CLI sa bagong makina, isang `update` ping
sa unang pagpapatakbo pagkatapos mag-upgrade sa bagong bersyon, at isang `onboarded`
ping kapag natapos mo ang pagpili sa in-dashboard onboarding. Ginagamit namin ito para
mabilang ang totoong mga install (ang raw na numero ng PyPI download ay ~98% mirrors, CI,
at auto-update na paulit-ulit na download) at para malaman kung aling agent frameworks at
bersyon ang aktwal na ginagamit.

**Pinakamarami isang POST bawat lifecycle event bawat bersyon**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random na UUID na naka-imbak sa `~/.clawmetry/install_id` | dedup; anonymous hanggang tahasan mong ikonekta ang Cloud sync (ang authenticated na daemon heartbeat ang magdadala nito, na nag-uugnay sa install na ito sa account mo) |
| `event` | `install` / `update` / `onboarded` | bagong install kumpara sa upgrade ng dati nang install |
| `version` | `0.12.167` | anong mga bersyon ang ginagamit |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga priyoridad sa suporta ng platform |
| `python` | `3.11.15` | matrix ng suporta sa bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | aling mga agent ang dapat naming isama sa susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng human install sa CI noise |

**Hindi namin ipinapadala ang**: IP (ang cloud ay hinahango ang country code server-side
mula sa request, pagkatapos ay itinatapon ang IP), hostname, username, workspace
path, laman ng file, ang iyong api_key, ang iyong email, anumang PII o
bagay na tiyak sa workspace. Ang wire payload ay maaaring i-audit sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng nagdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent na file marker
```

Ang isang pagkabigo sa network dito ay hindi kailanman humaharang sa pagpapatakbo ng
`clawmetry` — ang ping ay fire-and-forget sa isang daemon thread na may 3s na timeout.

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT

---

<p align="center">
  <strong>🦞 Panoorin ang iyong agent habang nag-iisip</strong><br>
  <sub>Ginawa ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
