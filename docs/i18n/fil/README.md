<!-- i18n-src:c422fb7dd0da -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Tignan mo ang iniisip ng iyong agent.** Real-time observability para sa **21 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 16 pa. Isang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Isang command lang. Zero config. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Bubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 21 agent runtimes

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon sinusukat nito ang **buong agent fleet mo** sa isang dashboard, na awtomatikong nade-detect ang bawat runtime sa makina mo:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

Libre ang OpenClaw at NemoClaw sa open-source app; ang ibang runtimes ay bubukas gamit ang ClawMetry Cloud o self-hosted na Pro license. Lumipat ng runtime mula sa header at ang bawat tab — cost, tokens, tools, traces — ay mare-re-scope sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong free/paid split, tier matrix, `/api/entitlement` shape, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated diagram na nagpapakita ng daloy ng mensahe sa channels, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng sessions, impormasyon ng model
- **Usage** — Pagsubaybay sa token at cost na may daily/weekly/monthly breakdown
- **Sessions** — Aktibong agent sessions kasama ang model, tokens, huling aktibidad
- **Crons** — Naka-iskedyul na jobs kasama ang status, next run, tagal
- **Logs** — Color-coded real-time log streaming
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, daily notes
- **Transcripts** — Chat-bubble UI para sa pagbasa ng kasaysayan ng sessions
- **Alerts** — Budget caps, error-rate triggers, agent-offline detection; nagru-route sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Harangan ang mga destructive delete, force push, DB mutation, sudo, package install, network call sa likod ng one-click na sign-off

## Mga Screenshot

### 🧠 Brain — Live na agent event stream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token usage at buod ng session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na tool call feed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Cost breakdown ayon sa model at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace file browser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget caps, error-rate triggers, webhooks papunta sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Harangan ang mapanganib na tool calls sa likod ng manual sign-off; policy-backed na mga protection rule
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang ang mag-i-install ng
PreToolUse hook na nagpapa-pause sa mga tumutugmang tool call *bago* ito tumakbo at naghihintay
sa desisyon mo (isang tap lang mula sa telepono mo kung naka-enable ang
[cloud push notifications](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang deny ay hinaharangan lang ang isang tool call na iyon — mananatili ang session ng agent at
maaari itong sumubok ng ibang paraan. Ang pag-apruba sa telepono mo ay nilalaktawan ang sariling
permission prompt ng Claude Code (sinagot mo na ito). Ang mga hindi tumutugmang tool ay
nagkakahalaga lamang ng ~40ms at bumabalik sa normal na permission flow ng Claude Code. Makakatanggap
ka rin ng push sa telepono kapag hinihintay ka mismo ng Claude Code (`permission_prompt` /
`idle_prompt` na mga notification).

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

Ang v2 React app ay nasa `frontend/` at nagsi-serve sa `/v2` kapag inilunsad ang Flask
server nang naka-enable ang v2.

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

Buksan ang `http://localhost:5173/v2/`. Ipinapasa ng Vite ang mga `/api` request papunta sa
`http://localhost:8900`, kaya makakausap ng React app ang lokal na Flask server nang
walang karagdagang CORS setup.

Para buuin ang bundle na sinasama sa Python package:

```bash
cd frontend
npm run build
```

Isinusulat ang production bundle sa `clawmetry/static/v2/dist/`.

## Runtime / Agent Compatibility

Nagmamasid ang ClawMetry sa maraming AI-agent runtime, hindi lang OpenClaw. Bawat non-OpenClaw runtime ay may dedikadong reader adapter na nagsasalin ng native session format nito papunta sa unified shapes ng ClawMetry; ini-ingest ito ng daemon sa parehong DuckDB store + cloud snapshot, na naka-tag ng runtime, at ipinapakita ng Session replay tab ang **runtime switcher** kapag may higit sa isang naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix + gabay sa pagdagdag ng runtimes, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa OpenClaw-family primer.

Pinapatakbo ang [Perplexity's numbat](https://github.com/perplexityai/numbat) agent-security tool? Ini-ingest ng ClawMetry ang mga natuklasan at desisyon sa pagpapatupad nito nang out-of-the-box — tingnan ang [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
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
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Mga workflow execution, node run, AI Agent prompts, model + tokens kung saan ito naitala ng n8n. |
| **Antigravity** | Beta adapter | Brain JSONL sa ilalim ng `~/.gemini/<flavor>/brain/`. Mga usapan, tool steps, thinking, per-generation na Gemini token split + cost, background-generation burn. |
| **GitHub Copilot** | Beta adapter | Copilot CLI `events.jsonl` sa ilalim ng `~/.copilot/session-state/` + ang `session-store.db` per-call usage ledger. Mga usapan, tool calls, model routing, cache-aware token split, vendor-billed AI-credit cost. |
| **Grok** | Beta adapter | xAI Grok Build CLI (Rust binary sa `~/.grok/bin/grok`): global event log `~/.grok/logs/unified.jsonl` + per-session `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Mga usapan, per-turn token split, model routing, at ang outbound repo payload ng CLI na naka-stage sa `~/.grok/upload_queue/` para makita mo kung ano ang lumabas sa makina mo. |

Ang ibig sabihin ng "Beta adapter" ay may reader ang ClawMetry para sa aktwal na on-disk na format ng runtime na iyon, na bawat isa ay binuo + na-verify laban sa totoong install sa totoong makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Ang mga adapter ay read-only; tapat ang bawat isa tungkol sa aktwal na iniimbak ng runtime nito (hal. hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, ang runtime switcher ay nagsi-scope sa sessions view papunta sa isa para sa malinis na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop cost attribution

Ang mga runtime sa itaas ay lahat nagsusulat ng sessions sa disk. Ang sarili mong **production agent** — yung binuo mo sa OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o simpleng `httpx` loop — ay hindi. Nakukuha pa rin ng zero-config interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching sa `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` env var) ay nagta-tag sa bawat call ng **pinangalanang source**, kaya bawat produktong pinapatakbo mo ay lalabas bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview — calls, providers, latency, error rate bawat agent. Walang naka-set na source? Nasusubaybayan pa rin ang mga call; nananatili lang tagong nakatago ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng runtime adapters (DuckDB → cloud snapshot), kaya nagsi-sync sa cloud dashboard ang out-loop sources tulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang traces mo kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa parehong direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang agent traces mo sa isang tool lang.

**I-export** ang bawat session — LLM calls, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o sarili mong OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Opsyonal na env vars ang auth headers at poll interval:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang traces, logs, at metrics mula sa kahit ano pa sa `/v1/traces`, `/v1/logs`, at `/v1/metrics`. Itutok ang anumang OpenTelemetry-instrumented na app dito:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Gumagana ang OTLP/JSON traces at logs sa plain `pip install clawmetry`, walang extras. Kailangan ng Protobuf ingest (at OTLP/JSON metrics) ng `pip install clawmetry[otel]`. Ang app na nagtatakda ng sarili nitong `service.name` ay lalabas bilang sarili nitong agent sa runtime switcher, kasama ang cost at tokens nito.

Makukuha mo ang zero-config, local-first na ClawMetry dashboard **at** ang data mo sa kahit anong backend na ginagamit na ng team mo — walang lock-in, walang pangalawang agent na iinstallin.

## Configuration

Karamihan sa mga tao ay hindi nangangailangan ng anumang config. Awtomatikong nade-detect ng ClawMetry ang workspace, logs, sessions, at crons mo.

Kung kailangan mo talagang i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng opsyon: `clawmetry --help`

## Mga Suportadong Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na na-configure mo. Ang mga channel lang na aktwal na naka-set up sa `openclaw.json` mo ang lalabas sa Flow diagram — ang mga hindi na-configure ay awtomatikong nakatago.

I-click ang anumang channel node sa Flow para makita ang live na chat bubble view kasama ang bilang ng papasok/palabas na mensahe.

| Channel | Status | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mensahe, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel detection |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel detection |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na web UI sessions |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style na bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage sa pamamagitan ng BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Sa pamamagitan ng Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Sa pamamagitan ng Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted na team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, may suportang E2EE |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat sa pamamagitan ng IRC connection |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** Binabasa ng ClawMetry ang `~/.openclaw/openclaw.json` mo at ini-render lang ang mga channel na aktwal mong na-configure. Walang kinakailangang manual setup.

## Docker Deployment

Gusto mong patakbuhin ang ClawMetry sa isang container? Walang problema! 🐳

**Quick start gamit ang Docker:**

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

**Docker Compose na halimbawa:**

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

> **Tala:** Kapag pinapatakbo sa Docker, i-mount ang data + log directories ng agent mo (hal. `~/.openclaw`, `~/.claude`, `~/.codex`) para ma-auto-detect ng ClawMetry ang setup mo.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong naiinstall via pip)
- AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, o QM (o naka-mount na volumes para sa Docker)
- Linux o macOS

## Suporta para sa NemoClaw / OpenShell

Awtomatikong dine-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed na OpenShell containers.

Walang karagdagang configuration na kinakailangan sa karamihan ng kaso. Awtomatikong tinutuklas ng sync daemon ang session files, nasa `~/.openclaw/` man ito sa host o sa loob ng OpenShell container.

### Paano ito gumagana

Dine-detect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sinusuri ang mga tumatakbong Docker container para sa `openshell`, `nemoclaw`, o `ghcr.io/nvidia/` na mga image, pagkatapos ay binabasa ang sessions sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na naka-sync mula sa NemoClaw containers ay naka-tag ng `runtime=nemoclaw` at `container_id` na metadata sa cloud dashboard, kaya madali mong makikilala ang mga ito bukod sa standard na OpenClaw sessions.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamagandang karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Naiiwasan nito ang mga paghihigpit sa network policy ng NemoClaw.

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

Kung kailangan mong patakbuhin ang sync daemon sa **loob** ng OpenShell sandbox, idagdag ang egress rule na ito sa network policy ng NemoClaw mo para maabot nito ang ingest API ng ClawMetry:

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

### Mga Port at endpoint

| Endpoint | Port | Protocol | Kinakailangan |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oo (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Oo (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa container session discovery |

Ang sync daemon lang ay gumagawa ng outbound HTTPS calls papunta sa `ingest.clawmetry.com`. Walang kinakailangang inbound ports.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang project na ito ay sinusubok gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng anonymous na install-lifecycle pings sa
`https://app.clawmetry.com/api/install`: isang `install` ping sa unang
pagkakataong patakbuhin mo ang `clawmetry` CLI sa bagong makina, isang `update` ping
sa unang run pagkatapos mag-upgrade sa bagong version, at isang `onboarded`
ping kapag natapos mo ang in-dashboard onboarding choice. Ginagamit namin ito
para bilangin ang totoong installs (ang raw na PyPI download numbers ay ~98% mirrors, CI,
at auto-update re-downloads) at para malaman kung aling mga agent framework at
versions ang aktwal na ginagamit.

**Pinakamarami isang POST bawat lifecycle event bawat version**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na naka-imbak sa `~/.clawmetry/install_id` | dedup; anonymous hanggang direkta mong ikonekta ang Cloud sync (ang authenticated daemon heartbeat na sana ang magdadala nito, na nag-uugnay ng install na ito sa account mo) |
| `event` | `install` / `update` / `onboarded` | bagong install kumpara sa upgrade ng umiiral na |
| `version` | `0.12.167` | kung anong mga version ang ginagamit |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga prayoridad sa suporta ng platform |
| `python` | `3.11.15` | Python version support matrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | aling mga agent ang dapat naming i-integrate susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalayin ang human installs sa CI noise |

**Ano ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code
server-side mula sa request, pagkatapos ay itinatapon ang IP), hostname, username, workspace
path, file contents, ang api_key mo, ang email mo, anumang PII o
workspace-specific na impormasyon. Ang wire payload ay auditable sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng nag-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Hindi kailanman hinaharangan ng pagkabigo ng network dito ang pagpapatakbo ng
`clawmetry` — ang ping ay fire-and-forget sa isang daemon thread na may 3 s timeout.

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
  <strong>🦞 Tignan mo ang iniisip ng iyong agent</strong><br>
  <sub>Ginawa ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
