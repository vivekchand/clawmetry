<!-- i18n-src:02b789586c7d -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Tingnan kung paano nag-iisip ang iyong agent.** Real-time na observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, at 10 pa. Iisang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Zero config. Awtomatikong nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Mabubuksan sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong agent fleet mo** sa iisang dashboard, na awtomatikong nade-detect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

Libre ang OpenClaw at NemoClaw sa open-source app; ang ibang runtime naman ay magagamit sa pamamagitan ng ClawMetry Cloud o isang self-hosted Pro license. Palitan ang runtime mula sa header at bawat tab, kabilang ang cost, tokens, tools, traces, ay mare-rescope papunta sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong hati ng free/paid, tier matrix, hugis ng `/api/entitlement`, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live na animated na diagram na nagpapakita ng daloy ng mga mensahe sa mga channel, brain, tools, at pabalik
- **Overview** — Health check, activity heatmap, bilang ng session, impormasyon ng model
- **Usage** — Pagsubaybay ng token at cost na may pang-araw-araw/linggo-linggo/buwan-buwanang breakdown
- **Sessions** — Aktibong session ng agent kasama ang model, tokens, huling aktibidad
- **Crons** — Naka-iskedyul na trabaho kasama ang status, susunod na takbo, tagal
- **Logs** — Real-time na log streaming na may kulay-kulay
- **Memory** — Mag-browse ng SOUL.md, MEMORY.md, AGENTS.md, at araw-araw na tala
- **Transcripts** — Chat-bubble na UI para sa pagbasa ng kasaysayan ng session
- **Alerts** — Budget cap, error-rate trigger, pag-detect ng offline na agent; nagrurut papunta sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Harangin ang destructive na pagtanggal, force push, pagbabago sa DB, sudo, pag-install ng package, at network call sa likod ng isang-click na pag-apruba

## Mga Screenshot

### 🧠 Brain — Live na daloy ng agent event
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Buod ng paggamit ng token at session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na feed ng tool call
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Paghahati ng gastos ayon sa model at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Tagabrowse ng file sa workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget cap, error-rate trigger, webhook sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Harangin ang mapanganib na tool call sa likod ng manu-manong pag-apruba; mga patakaran ng proteksyon na suportado ng policy
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution na pagharang para sa Claude Code** — isang command ang mag-i-install ng
PreToolUse hook na nagpapahinto sa mga tumutugmang tool call *bago* ito tumakbo at maghihintay
sa iyong desisyon (isang tap lang mula sa iyong telepono gamit ang
[cloud push notifications](https://app.clawmetry.com/push) na naka-enable):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang pagtanggi (deny) ay haharangin lang ang isang tool call na iyon — mananatili ang session ng agent at maaari itong subukan ng ibang paraan. Ang pag-apruba mula sa iyong telepono ay lalaktawan ang sariling permission prompt ng Claude Code (nasagot mo na ito). Ang mga tool na hindi tumutugma ay ~40ms lang ang gastos at babalik sa normal na daloy ng permission ng Claude Code. Makakatanggap ka rin ng push sa telepono kapag naghihintay sa iyo ang Claude Code mismo (`permission_prompt` / `idle_prompt` na notification).

## Pag-install

**One-liner (rekomendado):**
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

Ang v2 React app ay nasa `frontend/` at nagsi-serve sa `/v2` kapag
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

Buksan ang `http://localhost:5173/v2/`. Ipinoproxy ng Vite ang mga `/api` na request patungo sa
`http://localhost:8900`, kaya makikipag-usap ang React app sa lokal na Flask server
nang walang extra na CORS setup.

Para buuin ang bundle na isasama sa Python package:

```bash
cd frontend
npm run build
```

Isinusulat ang production bundle sa `clawmetry/static/v2/dist/`.

## Runtime / Agent Compatibility

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lang OpenClaw. Bawat runtime na hindi OpenClaw ay may dedikadong reader adapter na nagsasalin ng native session format nito papunta sa unified shapes ng ClawMetry; ito ay ina-ingest ng daemon sa parehong DuckDB store + cloud snapshot, na naka-tag ng runtime, at ipinapakita ng Session replay tab ang isang **runtime switcher** kapag mahigit isa ang naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa kumpletong matrix + gabay sa pagdaragdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa primer ng OpenClaw-family.

| Runtime / Agent | Status | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
| **PicoClaw** | Beta adapter | Flat na `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool calls. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/cost. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool calls + thinking, paggamit ng token. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, model, tool calls, paggamit ng token. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, model. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat project. Transcripts, model, bilang ng token. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool calls, kabuuang token. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool calls, tokens + cost. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool calls, paggamit ng token. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool calls, tokens + cost. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool calls, tokens + cost. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Workflow executions, node runs, AI Agent prompts, model + tokens kung saan ito itinatala ng n8n. |
| **Antigravity** | Beta adapter | Brain JSONL sa ilalim ng `~/.gemini/<flavor>/brain/`. Mga usapan, tool steps, thinking, per-generation na hati ng Gemini token + cost, background-generation na paggamit. |

Ang ibig sabihin ng "Beta adapter" ay may reader ang ClawMetry para sa tunay na on-disk na format ng runtime na iyon, na bawat isa ay binuo + na-verify laban sa isang tunay na install sa isang tunay na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Read-only ang mga adapter; bawat isa ay tapat tungkol sa aktwal na iniimbak ng runtime nito (hal., hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, isa-scope ng runtime switcher ang view ng sessions sa isa para sa malinis na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop na cost attribution

Ang mga runtime sa itaas ay pawang isinusulat ang mga session sa disk. Ang iyong sariling **production agent** — ang binuo mo gamit ang OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o isang plain na `httpx` loop — ay hindi. Nakukuha pa rin ng zero-config na interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching sa `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` na env var) ay nagta-tag sa bawat tawag ng isang **pinangalanang source**, kaya makikita ang bawat produkto na pinapatakbo mo bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** na card ng dashboard sa Overview — mga tawag, providers, latency, error rate bawat agent. Walang naka-set na source? Nasusubaybayan pa rin ang mga tawag; nananatili lang nakatago ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya nagsi-sync din sa cloud dashboard ang mga out-loop source katulad ng lahat, E2E-encrypted.

## OpenTelemetry — walang kinikilingang vendor, ipadala ang iyong mga trace kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa dalawang direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang mga trace ng agent mo sa isang tool lang.

**I-export** ang bawat session — mga LLM call, tools, sub-agents, tokens, cost — bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o ang sarili mong OTel Collector):

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

**I-ingest** — tinatanggap ng built-in na OTLP receiver ang mga trace at metric mula sa iba pa sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na dashboard ng ClawMetry **at** ang data mo sa anumang backend na ginagamit na ng team mo — walang lock-in, walang pangalawang agent na kailangang i-install.

## Configuration

Karamihan sa mga tao ay hindi na kailangan ng anumang config. Awtomatikong nade-detect ng ClawMetry ang iyong workspace, logs, sessions, at crons.

Kung kailangan mo talagang i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng options: `clawmetry --help`

## Mga Suportadong Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat OpenClaw channel na na-configure mo. Tanging ang mga channel na talagang naka-setup sa iyong `openclaw.json` ang lalabas sa Flow diagram — awtomatikong itinatago ang mga hindi pa na-configure.

I-click ang anumang channel node sa Flow para makita ang live na chat bubble view na may bilang ng papasok/palabas na mensahe.

| Channel | Status | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mga mensahe, stats, 10s na refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Pag-detect ng guild + channel |
| 🟪 **Slack** | ✅ Full | ✅ | Pag-detect ng workspace + channel |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na sessions sa web UI |
| 📡 **IRC** | ✅ Full | ✅ | Terminal-style na bubble UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage sa pamamagitan ng BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Sa pamamagitan ng Chat API webhooks |
| 🟣 **MS Teams** | ✅ Full | ✅ | Sa pamamagitan ng Teams bot plugin |
| 🔷 **Mattermost** | ✅ Full | ✅ | Self-hosted na team chat |
| 🟩 **Matrix** | ✅ Full | ✅ | Decentralized, may suporta sa E2EE |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | Decentralized na NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat sa pamamagitan ng IRC connection |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Auto-detection:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ire-render lamang ang mga channel na talagang na-configure mo. Walang kailangang manu-manong setup.

## Docker Deployment

Gustong patakbuhin ang ClawMetry sa loob ng container? Walang problema! 🐳

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

> **Tandaan:** Kapag tumatakbo sa Docker, i-mount ang direktoryo ng data + logs ng iyong agent (hal., `~/.openclaw`, `~/.claude`, `~/.codex`) para awtomatikong madetect ng ClawMetry ang iyong setup.

## Mga Requirement

- Python 3.8+
- Flask (awtomatikong na-install sa pamamagitan ng pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, o Antigravity (o mga naka-mount na volume para sa Docker)
- Linux o macOS

## Suporta sa NemoClaw / OpenShell

Awtomatikong nade-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw) — ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed na OpenShell container.

Karaniwan nang hindi kailangan ng dagdag na configuration. Awtomatikong madidiskubre ng sync daemon ang mga session file kung saan man ito nakatira, sa `~/.openclaw/` sa host o sa loob ng isang OpenShell container.

### Paano ito gumagana

Dine-detect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Binary detection** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Container detection** — sini-scan ang mga tumatakbong Docker container para sa `openshell`, `nemoclaw`, o `ghcr.io/nvidia/` na mga image, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mounts o `docker cp`

Ang mga session file na na-sync mula sa mga container ng NemoClaw ay naka-tag ng `runtime=nemoclaw` at `container_id` na metadata sa cloud dashboard, kaya makikilala mo ang mga ito bukod sa mga karaniwang session ng OpenClaw.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Iniiwasan nito ang mga restriction ng network policy ng NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong madidiskubre ng sync daemon ang mga session sa loob ng anumang tumatakbong OpenShell container.

### Opsyonal: tahasang pangalan ng sandbox

Kung hindi gumana ang auto-detection, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, idagdag ang egress rule na ito sa iyong network policy ng NemoClaw para maabot nito ang ingest API ng ClawMetry:

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
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa pagdiskubre ng container session |

Ang sync daemon ay gumagawa lamang ng outbound HTTPS calls patungo sa `ingest.clawmetry.com`. Walang kinakailangang inbound port.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang proyektong ito ay sinusuri gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng anonymous na install-lifecycle na ping papunta sa
`https://app.clawmetry.com/api/install`: isang `install` na ping sa unang
pagpapatakbo ng `clawmetry` CLI sa isang bagong makina, isang `update` na ping
sa unang takbo pagkatapos mag-upgrade sa bagong bersyon, at isang `onboarded`
na ping kapag natapos mo ang pagpili sa in-dashboard onboarding. Ginagamit namin ito
para bilangin ang mga tunay na install (ang hilaw na bilang ng PyPI download ay ~98% mirrors, CI,
at auto-update na muling pag-download) at para malaman kung aling mga agent framework at
bersyon ang talagang ginagamit.

**Pinakamarami ay isang POST bawat lifecycle event bawat bersyon**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na nakaimbak sa `~/.clawmetry/install_id` | dedup; anonymous hanggang tahasan mong ikonekta ang Cloud sync (ang authenticated na daemon heartbeat ang magdadala nito, na nag-uugnay sa install na ito sa iyong account) |
| `event` | `install` / `update` / `onboarded` | bagong install kumpara sa upgrade ng umiiral na |
| `version` | `0.12.167` | anong mga bersyon ang ginagamit |
| `os` / `os_version` | `Darwin` / `25.3.0` | prayoridad ng suporta sa platform |
| `python` | `3.11.15` | matrix ng suporta sa bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | aling mga agent ang dapat naming i-integrate susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga install ng tao mula sa ingay ng CI |

**Ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code server-side
mula sa request, pagkatapos ay itinatapon ang IP), hostname, username, workspace
path, laman ng file, ang iyong api_key, ang iyong email, anumang PII o
bagay na tungkol sa workspace. Ang wire payload ay maaaring ma-audit sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng magdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Hindi kailanman haharangin ng pagkabigo sa network dito ang pagpapatakbo ng `clawmetry` —
ang ping ay fire-and-forget sa isang daemon thread na may 3 s na timeout.

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
  <strong>🦞 Tingnan kung paano nag-iisip ang iyong agent</strong><br>
  <sub>Ginawa ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
