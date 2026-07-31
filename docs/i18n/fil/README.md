<!-- i18n-src:8252f6b1d31d -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang iniisip ng iyong agent.** Real-time na observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 10 pa. Isang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Isang command lang. Zero config. Awtomatikong nadedetect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong agent fleet mo** sa isang dashboard, na awtomatikong nade-detect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

Libre ang OpenClaw at NemoClaw sa open-source app; ang ibang runtime naman ay gumagana gamit ang ClawMetry Cloud o self-hosted na Pro license. Lumipat ng runtime mula sa header at mag-re-scope ang bawat tab — cost, tokens, tools, traces — papunta sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong free/paid split, tier matrix, `/api/entitlement` shape, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated na diagram na nagpapakita ng daloy ng mga mensahe sa mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng sessions, impormasyon ng model
- **Usage** — Pagsubaybay ng token at cost na may daily/weekly/monthly breakdown
- **Sessions** — Aktibong agent sessions na may model, tokens, huling aktibidad
- **Crons** — Mga naka-iskedyul na trabaho na may status, susunod na run, tagal
- **Logs** — Color-coded na real-time na log streaming
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, mga daily notes
- **Transcripts** — Chat-bubble UI para sa pagbasa ng history ng sessions
- **Alerts** — Budget caps, error-rate triggers, agent-offline detection; nagruruta papunta sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — I-gate ang mapaminsalang pagtanggal, force pushes, DB mutations, sudo, pag-install ng package, network calls sa likod ng isang one-click sign-off

## Mga Screenshot

### 🧠 Brain — Live na agent event stream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token usage at buod ng session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na feed ng tool call
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Breakdown ng cost ayon sa model at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace file browser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget caps, error-rate triggers, webhooks papunta sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — I-gate ang mapanganib na tool calls sa likod ng manual sign-off; mga policy-backed protection rule
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang para
mag-install ng PreToolUse hook na nagpapahinto sa mga tumutugmang tool call
*bago* ito tumakbo at naghihintay sa iyong desisyon (isang tap lang mula sa
telepono mo kapag naka-enable ang
[cloud push notifications](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang deny ay nagba-block lang sa isang tool call na iyon — mananatili ang
session ng agent at maaari itong sumubok ng ibang paraan. Ang pag-approve
mula sa telepono mo ay nagli-skip sa sarili ni Claude Code na permission
prompt (nasagot mo na ito). Ang mga tool na hindi tumutugma ay ~40ms lang
ang gastos at babalik sa normal na permission flow ni Claude Code. Makakatanggap
ka rin ng push sa telepono kapag si Claude Code mismo ay naghihintay sa iyo
(`permission_prompt` / `idle_prompt` na mga notipikasyon).

## I-install

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

Ang v2 React app ay nasa `frontend/` at naka-serve sa `/v2` kapag
sinimulan ang Flask server na naka-enable ang v2.

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

Buksan ang `http://localhost:5173/v2/`. Ang Vite ay nagpo-proxy ng mga
`/api` request papunta sa `http://localhost:8900`, kaya ang React app ay
makakapag-usap sa lokal na Flask server nang walang dagdag na CORS setup.

Para bumuo ng bundle na kasama sa Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isinusulat sa `clawmetry/static/v2/dist/`.

## Runtime / Agent Compatibility

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lang ang OpenClaw. Bawat runtime na hindi OpenClaw ay may sariling reader adapter na nagsasalin ng katutubong session format nito papunta sa unified shapes ng ClawMetry; ini-ingest ito ng daemon papunta sa parehong DuckDB store + cloud snapshot, na naka-tag ayon sa runtime, at ipinapakita ng Session replay tab ang isang **runtime switcher** kapag higit sa isang runtime ang naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix + gabay sa pagdagdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa primer ng OpenClaw-family.

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nadedetect |
| **PicoClaw** | Beta adapter | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool calls. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/cost. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool calls + thinking, token usage. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, model, tool calls, token usage. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, model. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat project. Transcripts, model, token counts. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool calls, token totals. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool calls, tokens + cost. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool calls, token usage. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool calls, tokens + cost. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool calls, tokens + cost. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Workflow executions, node runs, AI Agent prompts, model + tokens kung saan ito itinatala ng n8n. |

Ang ibig sabihin ng "Beta adapter" ay nagpapadala ang ClawMetry ng reader para sa aktwal na on-disk format ng runtime na iyon, na bawat isa ay binuo + na-verify laban sa tunay na install sa tunay na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Read-only ang mga adapter; tapat ang bawat isa tungkol sa aktwal na itinatabi ng runtime nito sa disk (hal., hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, sino-scope ng runtime switcher ang sessions view papunta sa isa para sa malinis na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop cost attribution

Ang mga runtime sa itaas ay lahat nagsusulat ng mga session sa disk. Ang sarili mong **production agent** — ang binuo mo gamit ang OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o isang plain `httpx` loop — ay hindi. Nahuhuli pa rin ng zero-config interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching ng `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` env var) ay nagta-tag sa bawat call ng isang **named source**, kaya ang bawat produktong pinapatakbo mo ay lumalabas bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview — mga call, providers, latency, error rate bawat agent. Walang naka-set na source? Sinusubaybayan pa rin ang mga call, natatago lang ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya ang mga out-loop source ay nag-sync sa cloud dashboard tulad ng lahat ng iba, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong traces kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa magkabilang direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang traces ng iyong agent sa isang tool lang.

**I-export** ang bawat session — LLM calls, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o sarili mong OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Opsyonal ang auth headers at poll interval bilang mga env var:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang traces at metrics mula sa kahit ano pa sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na dashboard ng ClawMetry **at** ang datos mo sa anumang backend na ginagamit na ng iyong team — walang lock-in, walang pangalawang agent na kailangang i-install.

## Configuration

Karamihan sa mga tao ay hindi na kailangan ng anumang config. Awtomatikong nade-detect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mong i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng opsyon: `clawmetry --help`

## Mga Suportadong Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na na-configure mo. Ang mga channel lang na talagang naka-set up sa iyong `openclaw.json` ang lumalabas sa Flow diagram — awtomatikong itinatago ang mga hindi na-configure.

I-click ang anumang channel node sa Flow para makita ang live na chat bubble view na may bilang ng papasok/palabas na mensahe.

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Messages, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel detection |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel detection |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na sessions ng web UI |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style na bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage sa pamamagitan ng BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Sa pamamagitan ng Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Sa pamamagitan ng Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted na team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, may suportang E2EE |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat sa pamamagitan ng koneksiyon sa IRC |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ini-render lang ang mga channel na talagang na-configure mo. Walang kailangang manual na setup.

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

> **Tandaan:** Kapag tumatakbo sa Docker, i-mount ang data + log directories ng iyong agent (hal. `~/.openclaw`, `~/.claude`, `~/.codex`) para ma-auto-detect ng ClawMetry ang iyong setup.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong naka-install via pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, o n8n (o mga naka-mount na volume para sa Docker)
- Linux o macOS

## Suporta sa NemoClaw / OpenShell

Awtomatikong nade-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ni NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng mga naka-sandbox na OpenShell container.

Sa karamihan ng mga kaso, walang kailangang dagdag na configuration. Awtomatikong natutuklasan ng sync daemon ang mga session file kahit nasaan man ito — sa `~/.openclaw/` sa host o sa loob ng isang OpenShell container.

### Paano ito gumagana

Dineditek ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sinusuri ang mga tumatakbong Docker container para sa `openshell`, `nemoclaw`, o `ghcr.io/nvidia/` na mga image, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na na-sync mula sa mga NemoClaw container ay naka-tag ng `runtime=nemoclaw` at `container_id` metadata sa cloud dashboard, kaya makikilala mo ang mga ito bukod sa mga karaniwang OpenClaw session sa isang tingin lang.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Nakakaiwas ito sa mga restriksyon ng NemoClaw network policy.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong hahanapin ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell container.

### Opsyonal: eksplisitong pangalan ng sandbox

Kung hindi gumana ang auto-detection, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, magdagdag ng egress rule na ito sa iyong NemoClaw network policy para maabot nito ang ClawMetry ingest API:

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

### Mga port at endpoint

| Endpoint | Port | Protocol | Required |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oo (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Oo (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa container session discovery |

Ang sync daemon lang ang gumagawa ng outbound HTTPS calls papunta sa `ingest.clawmetry.com`. Walang kailangang inbound ports.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang proyektong ito ay tinetest gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng anonymous na install-lifecycle pings papunta sa
`https://app.clawmetry.com/api/install`: isang `install` ping sa unang
pagkakataong pinapatakbo mo ang `clawmetry` CLI sa bagong makina, isang
`update` ping sa unang run pagkatapos mag-upgrade sa bagong bersyon, at
isang `onboarded` ping kapag natapos mo ang in-dashboard onboarding choice.
Ginagamit namin ito para bilangin ang tunay na mga install (ang hilaw na
bilang ng PyPI download ay ~98% mirrors, CI, at auto-update na muling
pag-download) at para malaman kung aling mga agent framework at bersyon
ang talagang ginagamit.

**Pinakamarami ay isang POST bawat lifecycle event bawat bersyon**, na naglalaman ng:

| Field | Halimbawa | Dahilan |
|---|---|---|
| `install_id` | random na UUID na naka-imbak sa `~/.clawmetry/install_id` | dedup; anonymous hanggang sa eksplisitong ikonekta mo ang Cloud sync (ang authenticated na daemon heartbeat ang magdadala noon, na nag-uugnay sa install na ito sa iyong account) |
| `event` | `install` / `update` / `onboarded` | fresh install kumpara sa upgrade ng umiiral na install |
| `version` | `0.12.167` | kung anong mga bersyon ang ginagamit |
| `os` / `os_version` | `Darwin` / `25.3.0` | priyoridad ng suporta sa platform |
| `python` | `3.11.15` | support matrix ng bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | aling mga agent ang dapat naming i-integrate susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga tunay na install ng tao mula sa ingay ng CI |

**Ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code mula
sa server side batay sa request, pagkatapos ay tinatanggal ang IP), hostname,
username, workspace path, laman ng file, ang iyong api_key, ang iyong email,
o anumang PII o bagay na tukoy sa workspace. Ang wire payload ay
maaaring i-audit sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng magdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ang isang network failure dito ay hindi kailanman humaharang sa pagpapatakbo
ng `clawmetry` — ang ping ay fire-and-forget sa isang daemon thread na may
3 segundong timeout.

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
  <strong>🦞 Panoorin ang iniisip ng iyong agent</strong><br>
  <sub>Ginawa ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng ekosistema ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
