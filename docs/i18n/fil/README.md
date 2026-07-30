<!-- i18n-src:9a05336fbdc1 -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang iyong ahente habang nag-iisip.** Real-time na observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 10 pa. Isang dashboard para sa buong fleet ng iyong mga ahente.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command. Walang kailangang i-configure. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Mabubuksan sa **http://localhost:8900** at tapos na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong fleet ng iyong mga ahente** sa iisang dashboard, na awtomatikong nade-detect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

Libre ang OpenClaw at NemoClaw sa open-source na app; ang ibang mga runtime naman ay bubukas gamit ang ClawMetry Cloud o isang self-hosted na Pro license. Lumipat ng runtime mula sa header at ang bawat tab — cost, tokens, tools, traces — ay muling mafo-focus sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong hati ng free/paid, tier matrix, hugis ng `/api/entitlement`, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated diagram na nagpapakita ng daloy ng mga mensahe sa mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng session, impormasyon ng modelo
- **Usage** — Pagsubaybay sa token at gastos na may daily/weekly/monthly breakdown
- **Sessions** — Aktibong mga session ng ahente kasama ang modelo, tokens, huling aktibidad
- **Crons** — Mga naka-iskedyul na trabaho kasama ang status, susunod na run, tagal
- **Logs** — Color-coded na real-time na log streaming
- **Memory** — Mag-browse ng SOUL.md, MEMORY.md, AGENTS.md, mga daily note
- **Transcripts** — Chat-bubble na UI para sa pagbasa ng kasaysayan ng session
- **Alerts** — Mga budget cap, error-rate trigger, agent-offline detection; ipinapadala sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Harangan ang mga mapanirang pagbura, force push, DB mutation, sudo, pag-install ng package, network call sa likod ng isang click na pag-apruba

## Mga Screenshot

### 🧠 Brain — Live na agent event stream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Buod ng token usage at session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na feed ng tool call
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Breakdown ng gastos ayon sa modelo at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Browser ng file ng workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Mga budget cap, error-rate trigger, webhooks papunta sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Harangan ang mapanganib na tool call sa likod ng manual na pag-apruba; mga panuntunan sa proteksyon na suportado ng patakaran
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang ang mag-i-install ng
PreToolUse hook na huminto sa mga tumutugmang tool call *bago* ito tumakbo at maghihintay
sa iyong desisyon (isang tap lang mula sa iyong telepono kung naka-enable ang
[cloud push notifications](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang pag-deny ay humaharang lang sa isang tool call na iyon — mananatili ang session ng ahente at
maaari itong sumubok ng ibang paraan. Ang pag-apruba mula sa iyong telepono ay lumalaktaw sa
sariling permission prompt ng Claude Code (nasagot mo na ito). Ang mga hindi tumutugmang tool ay
nagkakahalaga lang ng humigit-kumulang 40ms at babalik sa normal na daloy ng pahintulot ng Claude Code.
Makakatanggap ka rin ng push notification sa telepono kapag ang Claude Code mismo ay naghihintay sa iyo
(mga notipikasyon na `permission_prompt` / `idle_prompt`).

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

## Pagbuo ng v2 Frontend

Ang v2 React app ay matatagpuan sa `frontend/` at inihahatid sa `/v2` kapag
sinimulan ang Flask server na naka-enable ang v2.

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

Buksan ang `http://localhost:5173/v2/`. Ipino-proxy ng Vite ang mga request na
`/api` papunta sa `http://localhost:8900`, kaya makakausap ng React app ang
lokal na Flask server nang walang karagdagang setup ng CORS.

Para bumuo ng bundle na ipinapadala kasama ng Python package:

```bash
cd frontend
npm run build
```

Isinusulat ang production bundle sa `clawmetry/static/v2/dist/`.

## Compatibility ng Runtime / Agent

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lang ang OpenClaw. Ang bawat runtime maliban sa OpenClaw ay may dedikadong reader adapter na nagsasalin ng native session format nito papunta sa unified shapes ng ClawMetry; ang daemon ay nag-i-ingest ng mga ito papunta sa parehong DuckDB store + cloud snapshot, na naka-tag ng runtime, at ang Session replay tab ay nagpapakita ng **runtime switcher** kapag mahigit isa ang naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix + gabay sa pagdaragdag ng mga runtime, at [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa primer ng OpenClaw family.

| Runtime / Agent | Status | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
| **PicoClaw** | Beta adapter | Flat na `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, modelo, tool calls. |
| **NanoClaw** | Beta adapter | Per-session na SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, modelo, tokens/gastos. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, modelo, tool calls + thinking, token usage. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, modelo, tool calls, token usage. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, modelo. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat proyekto. Transcripts, modelo, bilang ng token. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, modelo, tool calls, kabuuang token. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, modelo, tool calls, tokens + gastos. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, modelo, tool calls, token usage. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, modelo, tool calls, tokens + gastos. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, modelo, tool calls, tokens + gastos. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Mga workflow execution, node run, AI Agent prompt, modelo + tokens kung saan itinatala ito ng n8n. |

Ang ibig sabihin ng "Beta adapter" ay may reader ang ClawMetry para sa aktwal na on-disk format ng runtime na iyon, bawat isa ay binuo + na-verify laban sa isang tunay na install sa isang tunay na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Ang mga adapter ay read-only lamang; tapat ang bawat isa tungkol sa aktwal na iniimbak ng runtime nito (hal., hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, ise-scope ng runtime switcher ang view ng mga session sa isa para sa malinis na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop cost attribution

Ang lahat ng runtime sa itaas ay isinusulat ang mga session sa disk. Ang iyong sariling **production agent** — ang binuo mo gamit ang OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o isang plain na `httpx` loop — ay hindi. Nakukuha pa rin ng zero-config interceptor ng ClawMetry ang mga LLM call nito (gastos, tokens, latency, errors) sa pamamagitan ng monkey-patching ng `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang env var na `CLAWMETRY_SOURCE=support-agent`) ay nagta-tag sa bawat tawag ng isang **named source**, kaya ang bawat produktong pinapatakbo mo ay lalabas bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview — mga tawag, providers, latency, error rate bawat ahente. Walang naka-set na source? Sinusubaybayan pa rin ang mga tawag, nagtatago lang ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya nag-sy-sync ang mga out-loop source papunta sa cloud dashboard tulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong traces kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa parehong direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang traces ng iyong ahente sa iisang tool.

**I-export** ang bawat session — LLM calls, tools, sub-agents, tokens, gastos — bilang mga OTLP/HTTP GenAI span papunta sa anumang collector (Datadog, Grafana, Honeycomb, o iyong sariling OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Opsyonal ang mga auth header at poll interval bilang env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang traces at metrics mula sa iba pang bagay sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na ClawMetry dashboard **at** ang iyong data sa anumang backend na dati nang ginagamit ng iyong team — walang lock-in, walang pangalawang ahente na dapat i-install.

## Configuration

Karamihan sa mga tao ay hindi kailangan ng anumang config. Awtomatikong nade-detect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mo talagang i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng opsyon: `clawmetry --help`

## Mga Suportadong Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na na-configure mo. Ang mga channel lang na aktwal na naka-setup sa iyong `openclaw.json` ang lalabas sa Flow diagram — awtomatikong itinatago ang mga hindi pa naka-configure.

I-click ang anumang channel node sa Flow para makita ang live na chat bubble view na may bilang ng papasok/papalabas na mensahe.

| Channel | Status | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mga mensahe, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Detection ng guild + channel |
| 🟪 **Slack** | ✅ Full | ✅ | Detection ng workspace + channel |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na sessions ng web UI |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style na bubble UI |
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

> **Auto-detection:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ire-render lang ang mga channel na aktwal mong na-configure. Walang kailangang manual na setup.

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

> **Tandaan:** Kapag pinapatakbo sa Docker, i-mount ang mga direktoryo ng data + log ng iyong ahente (hal. `~/.openclaw`, `~/.claude`, `~/.codex`) para makita ng ClawMetry ang iyong setup nang awtomatiko.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong na-install sa pamamagitan ng pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, o n8n (o mga naka-mount na volume para sa Docker)
- Linux o macOS

## Suporta para sa NemoClaw / OpenShell

Awtomatikong nade-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga ahente sa loob ng sandboxed na mga OpenShell container.

Walang karagdagang configuration na kailangan sa karamihan ng mga kaso. Awtomatikong natutuklasan ng sync daemon ang mga session file, saan man ito naroroon, sa `~/.openclaw/` sa host o sa loob ng isang OpenShell container.

### Paano ito gumagana

Dini-detect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sinusuri ang mga tumatakbong Docker container para sa `openshell`, `nemoclaw`, o `ghcr.io/nvidia/` na mga image, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na na-sync mula sa mga container ng NemoClaw ay naka-tag ng `runtime=nemoclaw` at metadata ng `container_id` sa cloud dashboard, para makilala mo ang mga ito bukod sa mga standard na session ng OpenClaw sa isang sulyap lamang.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Iniiwasan nito ang mga restriction ng network policy ng NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong hahanapin ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell container.

### Opsyonal: eksplisitong pangalan ng sandbox

Kung hindi gumagana ang auto-detection, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon sa **loob** ng OpenShell sandbox, magdagdag ng egress rule na ito sa iyong network policy ng NemoClaw para maabot nito ang ingest API ng ClawMetry:

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

Ang sync daemon lang ang gumagawa ng outbound HTTPS calls papunta sa `ingest.clawmetry.com`. Walang kailangang inbound port.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang proyektong ito ay tinetesting gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng iisang anonymous na "first run" ping papunta sa
`https://app.clawmetry.com/api/install` sa unang beses na patatakbuhin mo ang
`clawmetry` CLI sa isang bagong makina. Ginagamit namin ito para bilangin ang
mga install (ang tanging marketing metric na mayroon kami para sa isang OSS
na proyekto) at para malaman kung aling mga agent framework ang na-install na
ng aming mga user.

**Eksaktong isang POST bawat install**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na naka-imbak sa `~/.clawmetry/install_id` | dedup; hindi konektado sa iyong email o api_key |
| `version` | `0.12.167` | anong mga bersyon ang ginagamit sa labas |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga prayoridad sa suporta ng platform |
| `python` | `3.11.15` | support matrix ng bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | anong mga ahente ang dapat naming i-integrate susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga install ng tao mula sa ingay ng CI |

**Ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code sa
server side mula sa request, pagkatapos ay itinatapon ang IP), hostname,
username, workspace path, laman ng file, ang iyong api_key, ang iyong email,
anumang PII o bagay na partikular sa workspace. Ang wire payload ay
maaaring suriin sa [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng magdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ang isang network failure dito ay hindi kailanman humaharang sa `clawmetry`
mula sa pagtakbo — ang ping ay fire-and-forget sa isang daemon thread na may
3 segundong timeout.

## Kasaysayan ng Star

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
  <strong>🦞 Panoorin ang iyong ahente habang nag-iisip</strong><br>
  <sub>Ginawa ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
