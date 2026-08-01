<!-- i18n-src:191e9094d7fa -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang iyong agent habang nag-iisip.** Real-time na observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 10 pa. Iisang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command. Walang configuration. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Magbubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong agent fleet** mo sa iisang dashboard, na awtomatikong nade-detect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

Libre ang OpenClaw at NemoClaw sa open-source app; ang ibang mga runtime ay maa-unlock gamit ang ClawMetry Cloud o self-hosted Pro license. I-switch ang runtime mula sa header at bawat tab, kasama ang cost, tokens, tools, traces, ay muling mag-a-align sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong free/paid split, tier matrix, `/api/entitlement` shape, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated diagram na nagpapakita ng mga mensaheng dumadaloy sa mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng sessions, impormasyon ng model
- **Usage** — Pagsubaybay sa token at cost na may daily/weekly/monthly breakdown
- **Sessions** — Aktibong agent sessions kasama ang model, tokens, huling aktibidad
- **Crons** — Naka-iskedyul na mga trabaho kasama ang status, susunod na run, tagal
- **Logs** — Color-coded na real-time log streaming
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, mga daily notes
- **Transcripts** — Chat-bubble UI para sa pagbabasa ng kasaysayan ng session
- **Alerts** — Budget caps, error-rate triggers, agent-offline detection; nagpapadala sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Harangan ang mga destructive delete, force push, DB mutation, sudo, pag-install ng package, network call sa likod ng one-click na pag-apruba

## Mga Screenshot

### 🧠 Brain — Live na agent event stream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Buod ng token usage at session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na feed ng tool call
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Breakdown ng cost ayon sa model at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — File browser ng workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget caps, error-rate triggers, webhooks sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Harangan ang mga mapanganib na tool call sa likod ng manual na pag-apruba; mga patakarang protection rule
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang ang mag-i-install ng
PreToolUse hook na naghihinto sa mga tumutugmang tool call *bago* pa ito tumakbo at maghihintay
para sa iyong desisyon (isang tap lang mula sa iyong telepono gamit ang
[cloud push notifications](https://app.clawmetry.com/push) na naka-enable):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang isang deny ay naghaharang lamang sa iisang tool call na iyon — mananatili sa agent ang session nito at maaari
itong sumubok ng ibang paraan. Ang pag-apruba mula sa telepono mo ay lalaktaw sa sarili ni Claude Code na
permission prompt (nasagot mo na ito). Ang mga tool na hindi tumutugma ay nagkakahalaga lamang ng ~40ms at
babalik sa normal na permission flow ng Claude Code. Makakatanggap ka rin ng push sa telepono kapag si Claude Code mismo
ay naghihintay sa iyo (`permission_prompt` / `idle_prompt` na mga notification).

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

Ang v2 React app ay matatagpuan sa `frontend/` at nagsi-serve sa `/v2` kapag ang Flask
server ay sinimulan na naka-enable ang v2.

Gumamit ng dalawang terminal habang nagde-develop:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

Buksan ang `http://localhost:5173/v2/`. Ang Vite ay nagpo-proxy ng mga `/api` request papunta sa
`http://localhost:8900`, kaya ang React app ay makakapag-usap sa lokal na Flask server
nang walang karagdagang CORS setup.

Para buuin ang bundle na isasama sa Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isusulat sa `clawmetry/static/v2/dist/`.

## Pagkakatugma sa Runtime / Agent

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lang ang OpenClaw. Bawat runtime na hindi OpenClaw ay may dedikadong reader adapter na nagsasalin ng native session format nito papunta sa unified shapes ng ClawMetry; ini-ingest ito ng daemon papunta sa parehong DuckDB store + cloud snapshot, na naka-tag ng runtime, at ipinapakita ng Session replay tab ang isang **runtime switcher** kapag may higit sa isang runtime na naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa kumpletong matrix + gabay sa pagdaragdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa primer ng OpenClaw-family.

Pinapatakbo ang [Perplexity's numbat](https://github.com/perplexityai/numbat) na agent-security tool? Ini-ingest ng ClawMetry ang mga natuklasan at enforcement decision nito nang out of the box — tingnan ang [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
| **PicoClaw** | Beta adapter | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool calls. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/cost. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool calls + thinking, token usage. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, model, tool calls, token usage. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, model. |
| **Aider** | Beta adapter | `.aider.chat.history.md` per project. Transcripts, model, token counts. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool calls, token totals. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool calls, tokens + cost. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool calls, token usage. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool calls, tokens + cost. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool calls, tokens + cost. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Workflow executions, node runs, AI Agent prompts, model + tokens kung saan ito itinatala ng n8n. |
| **Antigravity** | Beta adapter | Brain JSONL sa ilalim ng `~/.gemini/<flavor>/brain/`. Mga usapan, tool steps, thinking, per-generation na Gemini token split + cost, background-generation burn. |

Ang ibig sabihin ng "Beta adapter" ay nagbibigay ang ClawMetry ng reader para sa aktwal na on-disk format ng runtime na iyon, bawat isa ay binuo + na-verify laban sa isang tunay na install sa isang tunay na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Read-only ang mga adapter; tapat ang bawat isa sa kung ano talaga ang naka-imbak ng runtime nito (hal., hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, ang runtime switcher ay naglilimita sa sessions view sa iisa para sa malinaw na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop cost attribution

Ang mga runtime sa itaas ay lahat nagsusulat ng sessions sa disk. Ang sarili mong **production agent** — ang binuo mo gamit ang OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o isang simpleng `httpx` loop — ay hindi. Nasusubaybayan pa rin ng zero-config interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching ng `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` na environment variable) ay nagta-tag sa bawat call ng isang **named source**, kaya ang bawat produktong pinapatakbo mo ay lalabas bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview — mga calls, providers, latency, error rate kada agent. Walang naka-set na source? Nasusubaybayan pa rin ang mga call, natatago lang ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya ang out-loop sources ay nagsi-sync sa cloud dashboard tulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong traces kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa parehong direksyon, gamit ang **GenAI semantic conventions**, kaya ang mga trace ng agent mo ay hindi kailanman nakakulong sa iisang tool lang.

**I-export** ang bawat session — LLM calls, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o ang sarili mong OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Opsyonal ang auth headers at poll interval bilang environment variables:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Pag-ingest** — tinatanggap ng built-in na OTLP receiver ang traces at metrics mula sa kahit ano pa sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na dashboard ng ClawMetry **at** ang iyong data sa anumang backend na ginagamit na ng team mo — walang lock-in, walang ikalawang agent na kailangang i-install.

## Configuration

Karamihan sa mga tao ay hindi na kailangan ng anumang config. Awtomatikong nade-detect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mo talagang i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng opsyon: `clawmetry --help`

## Mga Suportadong Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na naka-configure mo. Ang mga channel lamang na aktwal na naka-setup sa `openclaw.json` mo ang lalabas sa Flow diagram; ang mga hindi naka-configure ay awtomatikong itinatago.

I-click ang anumang channel node sa Flow para makita ang live na chat bubble view kasama ang bilang ng papasok/papalabas na mensahe.

| Channel | Status | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mensahe, stats, 10s na refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Pag-detect ng guild + channel |
| 🟪 **Slack** | ✅ Full | ✅ | Pag-detect ng workspace + channel |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na sessions ng web UI |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style na bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage sa pamamagitan ng BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Sa pamamagitan ng Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Sa pamamagitan ng Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted na team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, may suportang E2EE |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized na NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat sa pamamagitan ng IRC connection |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** Binabasa ng ClawMetry ang `~/.openclaw/openclaw.json` mo at ire-render lamang ang mga channel na aktwal mong na-configure. Walang kinakailangang manual na setup.

## Docker Deployment

Gusto mo bang patakbuhin ang ClawMetry sa isang container? Walang problema! 🐳

**Mabilisang simula gamit ang Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Halimbawa ng Docker Compose:**

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

> **Tandaan:** Kapag pinapatakbo sa Docker, i-mount ang data + log directories ng iyong agent (hal., `~/.openclaw`, `~/.claude`, `~/.codex`) para ma-auto-detect ng ClawMetry ang setup mo.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong naka-install sa pamamagitan ng pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, o Antigravity (o naka-mount na volumes para sa Docker)
- Linux o macOS

## Suporta sa NemoClaw / OpenShell

Awtomatikong nade-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed OpenShell containers.

Walang kailangang karagdagang configuration sa karamihan ng mga kaso. Awtomatikong tinutuklas ng sync daemon ang mga session file, mabuhay man ito sa `~/.openclaw/` sa host o sa loob ng OpenShell container.

### Paano ito gumagana

Dinedetect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — tinitingnan ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sinasaliksik ang tumatakbong mga Docker container para sa `openshell`, `nemoclaw`, o `ghcr.io/nvidia/` na mga image, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na na-sync mula sa NemoClaw containers ay naka-tag ng `runtime=nemoclaw` at `container_id` metadata sa cloud dashboard, para makilala mo ang mga ito bukod sa karaniwang OpenClaw sessions sa isang tingin lamang.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Naiiwasan nito ang mga restriction ng network policy ng NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong hahanapin ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell containers.

### Opsyonal: tahasang pangalan ng sandbox

Kung hindi gumana ang auto-detection, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, idagdag ang egress rule na ito sa network policy ng NemoClaw mo para maabot nito ang ingest API ng ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Oo (lokal na dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa container session discovery |

Ang sync daemon ay gumagawa lamang ng outbound HTTPS calls papunta sa `ingest.clawmetry.com`. Walang kinakailangang inbound ports.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang proyektong ito ay sinusubok gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng anonymous na install-lifecycle pings papunta sa
`https://app.clawmetry.com/api/install`: isang `install` ping sa unang
pagkakataong patakbuhin mo ang `clawmetry` CLI sa isang bagong makina, isang `update` ping
sa unang run pagkatapos mag-upgrade sa bagong bersyon, at isang `onboarded`
ping kapag natapos mo ang in-dashboard na pagpili ng onboarding. Ginagamit namin ito
para bilangin ang tunay na mga install (ang raw na bilang ng PyPI download ay ~98% mirrors, CI,
at auto-update re-downloads) at para malaman kung aling mga agent framework at
bersyon ang aktwal na ginagamit.

**Pinakamarami ay isang POST kada lifecycle event kada bersyon**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random na UUID na naka-imbak sa `~/.clawmetry/install_id` | dedup; anonymous hanggang tahasan mong ikonekta ang Cloud sync (ang authenticated daemon heartbeat na ang magdadala nito mula roon, na nag-uugnay sa install na ito sa account mo) |
| `event` | `install` / `update` / `onboarded` | bagong install kumpara sa upgrade ng umiiral na |
| `version` | `0.12.167` | kung aling mga bersyon ang ginagamit |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga prayoridad sa suporta ng platform |
| `python` | `3.11.15` | support matrix para sa bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | aling mga agent ang dapat naming i-integrate sa susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga install ng tao sa ingay ng CI |

**Ano ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code server-side
mula sa request, pagkatapos ay itatapon ang IP), hostname, username, workspace
path, laman ng file, ang api_key mo, ang email mo, anumang PII o
partikular sa workspace. Ang wire payload ay auditable sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng magdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ang pagkabigo ng network dito ay hindi kailanman humaharang sa `clawmetry` para tumakbo — ang
ping ay fire-and-forget sa isang daemon thread na may 3 segundong timeout.

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lisensya

MIT

---

<p align="center">
  <strong>🦞 Panoorin ang iyong agent habang nag-iisip</strong><br>
  <sub>Binuo ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
