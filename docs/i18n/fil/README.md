<!-- i18n-src:8f42d460a973 -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang iniisip ng iyong agent.** Real-time na observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, at 10 pa. Isang dashboard para sa buong fleet ng iyong agent.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Walang kailangang i-configure. Awtomatikong nadedetect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Magbubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat na nito ang **buong fleet ng iyong agent** sa isang dashboard, na awtomatikong nadedetect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

Libre ang OpenClaw at NemoClaw sa open-source na app; nabubuksan ang ibang runtime gamit ang ClawMetry Cloud o self-hosted na Pro license. Magpalit ng runtime mula sa header at ang bawat tab — cost, tokens, tools, traces — ay muling mase-scope sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong hating free/paid, tier matrix, hugis ng `/api/entitlement`, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated na diagram na nagpapakita ng daloy ng mga mensahe sa pagitan ng mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng sessions, impormasyon ng model
- **Usage** — Pagsubaybay sa token at cost na may daily/weekly/monthly breakdown
- **Sessions** — Aktibong mga session ng agent kasama ang model, tokens, huling aktibidad
- **Crons** — Naka-iskedyul na trabaho kasama ang status, susunod na run, tagal
- **Logs** — Color-coded na real-time na log streaming
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, mga daily note
- **Transcripts** — Chat-bubble na UI para sa pagbasa ng history ng session
- **Alerts** — Budget caps, error-rate triggers, agent-offline detection; nagru-route sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Haharangin ang mapaminsalang pagbura, force pushes, DB mutations, sudo, pag-install ng package, at mga network call hanggang sa may one-click na pag-apruba

## Mga Screenshot

### 🧠 Brain — Live na event stream ng agent
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token usage at buod ng session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na feed ng tool call
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Breakdown ng gastos ayon sa model at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace file browser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget caps, error-rate triggers, webhooks papunta sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Haharangin ang mapanganib na tool call hanggang sa manual na pag-apruba; mga patakarang protektado ng policy
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## Pag-develop ng v2 Frontend

Ang v2 React app ay nasa `frontend/` at inihahain sa `/v2` kapag ang Flask
server ay sinimulan na naka-enable ang v2.

Gumamit ng dalawang terminal habang nagdedevelop:

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

Buksan ang `http://localhost:5173/v2/`. Ini-proxy ng Vite ang mga request sa `/api`
papunta sa `http://localhost:8900`, kaya makakausap ng React app ang lokal na
Flask server nang walang karagdagang setup ng CORS.

Para buuin ang bundle na kasama sa Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isinusulat sa `clawmetry/static/v2/dist/`.

## Runtime / Agent Compatibility

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lang ang OpenClaw. Ang bawat runtime na hindi OpenClaw ay may kasamang dedikadong reader adapter na nagsasalin ng katutubong format ng session nito papunta sa pinag-isang hugis ng ClawMetry; ini-ingest ito ng daemon papunta sa parehong DuckDB store + cloud snapshot, na naka-tag ayon sa runtime, at ipinapakita ng Session replay tab ang isang **runtime switcher** kapag may higit sa isa. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix at gabay sa pagdagdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa panimulang gabay ng OpenClaw-family.

| Runtime / Agent | Status | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nadedetect |
| **PicoClaw** | Beta adapter | Flat na `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool calls. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/cost. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool calls + thinking, token usage. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, model, tool calls, token usage. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, model. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat project. Transcripts, model, bilang ng token. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool calls, kabuuang token. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool calls, tokens + cost. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool calls, token usage. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool calls, tokens + cost. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool calls, tokens + cost. |

Ang ibig sabihin ng "Beta adapter" ay may inihahain ang ClawMetry na reader para sa aktwal na on-disk na format ng runtime na iyon, bawat isa ay binuo + na-verify laban sa isang totoong install sa isang totoong makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Read-only ang mga adapter; tapat ang bawat isa tungkol sa aktwal na iniimbak ng runtime nito (hal., hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, ise-scope ng runtime switcher ang view ng sessions sa isa para sa malinis na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop na cost attribution

Ang mga runtime sa itaas ay lahat nagsusulat ng sessions sa disk. Ang iyong sariling **production agent** — ang binuo mo gamit ang OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o isang plain na `httpx` loop — ay hindi. Nasasagap pa rin ng zero-config na interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching sa `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang env var na `CLAWMETRY_SOURCE=support-agent`) ay nagta-tag sa bawat call ng isang **pinangalanang source**, kaya lumalabas ang bawat produktong pinapatakbo mo bilang sarili nitong first-class na linyang maaaring atribuhan ang gastos sa card na **🔌 Out-loop sources** ng dashboard sa Overview — calls, providers, latency, error rate bawat agent. Walang naka-set na source? Nasusubaybayan pa rin ang mga call; ang card lang ang mananatiling nakatago.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya nagsi-sync ang mga out-loop source papunta sa cloud dashboard tulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong traces kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa dalawang direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang traces ng iyong agent sa iisang tool.

**I-export** ang bawat session — LLM calls, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o ang sarili mong OTel Collector):

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

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang traces at metrics mula sa kahit ano pa sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na dashboard ng ClawMetry **at** ang iyong data sa anumang backend na ginagamit na ng iyong team — walang lock-in, walang pangalawang agent na kailangang i-install.

## Configuration

Karamihan sa mga tao ay hindi nangangailangan ng anumang config. Awtomatikong nadedetect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mong i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng options: `clawmetry --help`

## Suportadong mga Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na na-configure mo. Ang mga channel lamang na aktwal na naka-setup sa iyong `openclaw.json` ang lalabas sa Flow diagram — awtomatikong itinatago ang mga hindi pa naka-configure.

I-click ang anumang channel node sa Flow para makita ang live na chat bubble view kasama ang bilang ng papasok/paalis na mensahe.

| Channel | Status | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mga mensahe, stats, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Pagdetect ng guild + channel |
| 🟪 **Slack** | ✅ Full | ✅ | Pagdetect ng workspace + channel |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na web UI sessions |
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

> **Awtomatikong pagdetect:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ini-render lamang ang mga channel na aktwal mong na-configure. Walang kailangang manual na setup.

## Docker Deployment

Gusto mong patakbuhin ang ClawMetry sa loob ng container? Walang problema! 🐳

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

> **Tandaan:** Kapag tumatakbo sa Docker, i-mount ang mga direktoryo ng data + log ng iyong agent (hal., `~/.openclaw`, `~/.claude`, `~/.codex`) para awtomatikong madetect ng ClawMetry ang iyong setup.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong naiinstall via pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, o Deep Agents (o naka-mount na volumes para sa Docker)
- Linux o macOS

## Suporta sa NemoClaw / OpenShell

Awtomatikong nadedetect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed na OpenShell containers.

Walang karagdagang configuration na kailangan sa karamihan ng kaso. Awtomatikong tinutuklas ng sync daemon ang mga session file kahit nasaan man ang mga ito, sa `~/.openclaw/` sa host o sa loob ng isang OpenShell container.

### Paano ito gumagana

Nadedetect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Pagdetect ng binary** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makakuha ng impormasyon ng sandbox
2. **Pagdetect ng container** — sini-scan ang tumatakbong Docker containers para sa mga image na `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na na-sync mula sa mga NemoClaw container ay naka-tag ng `runtime=nemoclaw` at metadata na `container_id` sa cloud dashboard, kaya madali mong maiiba ang mga ito sa karaniwang mga session ng OpenClaw.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Nakakaiwas ito sa mga paghihigpit ng network policy ng NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong hahanapin ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell containers.

### Opsyonal: tahasang pangalan ng sandbox

Kung hindi gumana ang awtomatikong pagdetect, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, idagdag ang egress rule na ito sa iyong NemoClaw network policy para maabot nito ang ingest API ng ClawMetry:

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

| Endpoint | Port | Protocol | Kailangan |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oo (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Oo (lokal na dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa pagtuklas ng container session |

Ang sync daemon ay gumagawa lamang ng outbound HTTPS calls papunta sa `ingest.clawmetry.com`. Walang kinakailangang inbound ports.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang project na ito ay tinatest gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng iisang anonymous na "first run" ping papunta sa
`https://app.clawmetry.com/api/install` sa unang pagkakataong patatakbuhin mo ang
`clawmetry` CLI sa isang bagong makina. Ginagamit namin ito para bilangin ang
mga install (ang tanging marketing metric na mayroon kami para sa isang OSS
project) at para malaman kung anong mga agent framework ang naka-install na
ng aming mga user.

**Eksaktong isang POST bawat install**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na iniimbak sa `~/.clawmetry/install_id` | dedup; hindi naka-link sa iyong email o api_key |
| `version` | `0.12.167` | anong mga bersyon ang nasa paligid |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga prayoridad sa suporta ng platform |
| `python` | `3.11.15` | matrix ng suporta ng bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | anong mga agent ang dapat naming i-integrate sa susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga human install sa CI noise |

**Ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code sa server
side mula sa request, pagkatapos ay itatapon ang IP), hostname, username,
workspace path, laman ng file, ang iyong api_key, ang iyong email, anumang PII
o bagay na partikular sa workspace. Ang wire payload ay auditable sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Pag-opt out** (alinman sa mga ito ay permanenteng nagdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ang pagkabigo ng network dito ay hindi kailanman humaharang sa `clawmetry` na
tumakbo — ang ping ay fire-and-forget sa isang daemon thread na may 3s na
timeout.

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
  <sub>Binuo ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
