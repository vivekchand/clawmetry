<!-- i18n-src:bab48eec552f -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang pag-iisip ng iyong agent.** Real-time observability para sa **14 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 10 pa. Isang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command. Zero config. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 agent runtimes

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong agent fleet** mo sa isang dashboard, na awtomatikong nade-detect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

Libre ang OpenClaw at NemoClaw sa open-source app; ang ibang runtimes naman ay bubukas gamit ang ClawMetry Cloud o isang self-hosted Pro license. Palitan ang runtime mula sa header at ang bawat tab — cost, tokens, tools, traces — ay mare-rescope sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong free/paid split, tier matrix, `/api/entitlement` shape, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated diagram na nagpapakita ng mga mensaheng dumadaloy sa mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng sessions, impormasyon ng model
- **Usage** — Token at cost tracking na may daily/weekly/monthly breakdowns
- **Sessions** — Aktibong agent sessions kasama ang model, tokens, huling aktibidad
- **Crons** — Naka-schedule na jobs kasama ang status, susunod na run, tagal
- **Logs** — Color-coded real-time log streaming
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, daily notes
- **Transcripts** — Chat-bubble UI para sa pagbasa ng session histories
- **Alerts** — Budget caps, error-rate triggers, agent-offline detection; nag-route sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — I-gate ang mga destructive deletes, force pushes, DB mutations, sudo, package installs, network calls sa likod ng one-click sign-off

## Mga Screenshot

### 🧠 Brain — Live agent event stream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token usage & session summary
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time tool call feed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Cost breakdown by model & session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace file browser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Posture & audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget caps, error-rate triggers, webhooks to Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Gate risky tool calls behind manual sign-off; policy-backed protection rules
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang ang mag-i-install ng
PreToolUse hook na nagpo-pause sa mga tumutugmang tool calls *bago* ang mga ito tumakbo at naghihintay
ng iyong desisyon (isang tap lang mula sa iyong telepono kapag naka-enable ang
[cloud push notifications](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang isang deny ay nag-block lamang sa isang tool call na iyon — mananatili ang session ng agent at maaari itong sumubok ng ibang paraan. Ang pag-approve mula sa telepono mo ay nagli-skip sa sarili nitong permission prompt ng Claude Code (nasagot mo na ito). Ang mga hindi tumutugmang tools ay nagkakahalaga ng ~40ms at
napupunta sa normal na permission flow ng Claude Code. Makakatanggap ka rin ng phone push kapag ang Claude Code mismo ay naghihintay sa iyo (`permission_prompt` /
`idle_prompt` notifications).

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

Ang v2 React app ay nasa `frontend/` at ito ay sine-serve sa `/v2` kapag
sinimulan ang Flask server na may naka-enable na v2.

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

Buksan ang `http://localhost:5173/v2/`. Ang Vite ay nagpo-proxy ng mga `/api` requests papunta sa
`http://localhost:8900`, kaya makakausap ng React app ang lokal na Flask server
nang walang karagdagang CORS setup.

Para i-build ang bundle na sinasama sa Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isinusulat sa `clawmetry/static/v2/dist/`.

## Runtime / Agent Compatibility

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtimes, hindi lamang ang OpenClaw. Bawat runtime na hindi OpenClaw ay may dedikadong reader adapter na nagsasalin ng native session format nito papunta sa unified shapes ng ClawMetry; ang daemon ay nagpapasok ng mga ito sa parehong DuckDB store + cloud snapshot, na naka-tag ayon sa runtime, at ang Session replay tab ay nagpapakita ng **runtime switcher** kapag may higit sa isa. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix + gabay sa pagdaragdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa OpenClaw-family primer.

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
| **PicoClaw** | Beta adapter | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool calls. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + message counts. |
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

Ang "Beta adapter" ay nangangahulugang nagpapadala ang ClawMetry ng reader para sa aktwal na on-disk format ng runtime na iyon, bawat isa ay binuo + na-verify laban sa tunay na install sa tunay na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Ang mga adapter ay read-only; ang bawat isa ay tapat tungkol sa aktwal na iniimbak ng runtime nito (hal., ang PicoClaw/NanoClaw/Cursor ay hindi nagsusulat ng token cost sa disk). Kapag maraming runtimes ang tumatakbo sa isang node, sino-scope ng runtime switcher ang sessions view sa isa para sa malinaw na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop cost attribution

Ang mga runtime sa itaas ay lahat nagsusulat ng sessions sa disk. Ang iyong sariling **production agent** — ang isa na binuo mo gamit ang OpenAI Agents SDK, LangChain, ang Vercel AI SDK, LlamaIndex, E2B, o isang plain `httpx` loop — ay hindi. Nakukuha pa rin ng zero-config interceptor ng ClawMetry ang mga LLM calls nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching sa `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` env var) ay nagta-tag sa bawat call ng isang **named source**, kaya bawat produktong pinapatakbo mo ay lumalabas bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview — calls, providers, latency, error rate per agent. Walang naka-set na source? Sinusubaybayan pa rin ang mga calls; nananatiling nakatago lang ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng runtime adapters (DuckDB → cloud snapshot), kaya ang out-loop sources ay nag-sync sa cloud dashboard tulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong traces kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa magkabilang direksyon, gamit ang **GenAI semantic conventions**, kaya ang traces ng iyong agent ay hindi kailanman naka-lock sa isang tool lamang.

**I-export** ang bawat session — LLM calls, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o sa sarili mong OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Opsyonal ang auth headers at poll interval bilang env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang traces at metrics mula sa iba pang bagay sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na ClawMetry dashboard **at** ang data mo sa anumang backend na ginagamit na ng team mo — walang lock-in, walang kailangang i-install na pangalawang agent.

## Configuration

Karamihan sa mga tao ay hindi na kailangan ng anumang config. Awtomatikong nade-detect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mo talagang mag-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng options: `clawmetry --help`

## Mga Suportadong Channel

Ipinapakita ng ClawMetry ang live activity para sa bawat OpenClaw channel na na-configure mo. Ang mga channel lang na talagang naka-setup sa iyong `openclaw.json` ang lumalabas sa Flow diagram — ang mga hindi naka-configure ay awtomatikong nakatago.

I-click ang anumang channel node sa Flow para makita ang live chat bubble view na may bilang ng incoming/outgoing messages.

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Messages, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Reads `~/Library/Messages/chat.db` directly |
| 💚 **WhatsApp** | ✅ Full | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel detection |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel detection |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in web UI sessions |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Via Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Via Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, E2EE support |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat via IRC connection |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ire-render lamang ang mga channel na talagang na-configure mo. Walang kinakailangang manual setup.

## Docker Deployment

Gusto mong patakbuhin ang ClawMetry sa isang container? Walang problema! 🐳

**Mabilisang simula sa Docker:**

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

> **Tandaan:** Kapag tumatakbo sa Docker, i-mount ang data + log directories ng iyong agent (hal. `~/.openclaw`, `~/.claude`, `~/.codex`) para ma-auto-detect ng ClawMetry ang iyong setup.

## Mga Kinakailangan

- Python 3.8+
- Flask (naka-install nang awtomatiko via pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, o Deep Agents (o naka-mount na volumes para sa Docker)
- Linux o macOS

## Suporta para sa NemoClaw / OpenShell

Awtomatikong nade-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed OpenShell containers.

Walang karagdagang configuration na kailangan sa karamihan ng kaso. Ang sync daemon ay awtomatikong tumutuklas ng session files kung saan man ito nakatira, sa `~/.openclaw/` sa host o sa loob ng OpenShell container.

### Paano ito gumagana

Nade-detect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sinusuri ang tumatakbong Docker containers para sa `openshell`, `nemoclaw`, o `ghcr.io/nvidia/` images, pagkatapos ay binabasa ang mga session via volume mounts o `docker cp`

Ang mga session files na na-sync mula sa NemoClaw containers ay naka-tag ng `runtime=nemoclaw` at `container_id` metadata sa cloud dashboard, para makilala mo ang mga ito bilang naiiba sa standard na OpenClaw sessions sa isang tingin lamang.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Iniiwasan nito ang mga restriction ng NemoClaw network policy.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong hahanapin ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell containers.

### Opsyonal: explicit na pangalan ng sandbox

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

| Endpoint | Port | Protocol | Kailangan |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oo (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Oo (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa container session discovery |

Ang sync daemon ay gumagawa lamang ng outbound HTTPS calls papunta sa `ingest.clawmetry.com`. Walang kinakailangang inbound ports.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang proyektong ito ay tested gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng iisang anonymous na "first run" ping papunta sa
`https://app.clawmetry.com/api/install` sa unang beses na patakbuhin mo ang
`clawmetry` CLI sa isang bagong makina. Ginagamit namin ito para bilangin ang mga install (ang
tanging marketing metric namin para sa isang OSS project) at para malaman kung
aling mga agent framework ang naka-install na sa mga user namin.

**Eksaktong isang POST bawat install**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na nakaimbak sa `~/.clawmetry/install_id` | dedup; hindi konektado sa iyong email o api_key |
| `version` | `0.12.167` | anong mga bersyon ang ginagamit sa labas |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga prayoridad sa suporta ng platform |
| `python` | `3.11.15` | Python version support matrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | aling mga agent ang dapat naming i-integrate susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng human installs mula sa CI noise |

**Ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code server-side
mula sa request, pagkatapos ay itinatapon ang IP), hostname, username, workspace
path, laman ng file, ang iyong api_key, ang iyong email, anumang PII o
bagay na tungkol sa workspace. Ang wire payload ay maaaring i-audit sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng nagdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ang network failure dito ay hindi kailanman humaharang sa pagpapatakbo ng `clawmetry` — ang
ping ay fire-and-forget sa isang daemon thread na may 3 s timeout.

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
  <strong>🦞 Panoorin ang pag-iisip ng iyong agent</strong><br>
  <sub>Ginawa ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
