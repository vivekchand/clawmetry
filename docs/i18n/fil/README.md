<!-- i18n-src:7cfb63716507 -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Makita ang pag-iisip ng iyong agent.** Real-time observability para sa **14 na AI agent runtime**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, at 10 pa. Isang dashboard para sa buong agent fleet mo.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [higit pa →](docs/i18n/)

Isang command lang. Walang kailangang i-configure. Automatic na nade-detect ang lahat.

```bash
pip install clawmetry && clawmetry
```

Magbubukas sa **http://localhost:8900** at tapos ka na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 14 na agent runtime

Nagsimula ang ClawMetry bilang observability para sa OpenClaw, at ngayon ay sinusukat nito ang **buong agent fleet** mo sa isang dashboard, na automatic na nade-detect ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

Libre ang OpenClaw at NemoClaw sa open-source app; ang ibang mga runtime naman ay bubukas sa ClawMetry Cloud o sa self-hosted Pro license. Palitan ang runtime mula sa header at aayusin ng bawat tab, mula cost, tokens, tools, hanggang sa traces, ang saklaw nito ayon sa runtime na iyon. Tingnan ang **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** para sa eksaktong hati ng libre/bayad, tier matrix, hugis ng `/api/entitlement`, at ang `clawmetry license` CLI.

## Ano ang Makukuha Mo

- **Flow** — Live animated diagram na nagpapakita ng daloy ng mga mensahe sa mga channel, brain, tools, at pabalik
- **Overview** — Health checks, activity heatmap, bilang ng session, impormasyon ng modelo
- **Usage** — Pagsubaybay ng token at cost na may breakdown araw-araw/lingguhan/buwanan
- **Sessions** — Aktibong mga agent session kasama ang modelo, tokens, at huling aktibidad
- **Crons** — Mga naka-iskedyul na trabaho kasama ang status, susunod na run, at tagal
- **Logs** — Real-time log streaming na may kulay-kulay na pag-uuri
- **Memory** — I-browse ang SOUL.md, MEMORY.md, AGENTS.md, at mga araw-araw na tala
- **Transcripts** — Chat-bubble UI para sa pagbasa ng kasaysayan ng session
- **Alerts** — Mga budget cap, error-rate trigger, at pag-detect ng offline na agent; nagtu-route sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Harangin ang mapaminsalang pagbura, force push, DB mutation, sudo, pag-install ng package, at network call sa likod ng isang beses-i-click na sign-off

## Mga Screenshot

### 🧠 Brain — Live na daloy ng agent event
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Paggamit ng token at buod ng session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time feed ng tool call
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Breakdown ng cost ayon sa modelo at session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — File browser ng workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at audit log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget cap, error-rate trigger, mga webhook sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Harangin ang mapanganib na tool call sa likod ng manual sign-off; mga panuntunang protektado ng patakaran
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pre-execution blocking para sa Claude Code** — isang command lang ang mag-iinstall ng
PreToolUse hook na magpapahinto sa mga tumutugmang tool call *bago* pa sila
tumakbo at maghihintay ng iyong desisyon (isang tap lang mula sa iyong telepono na may
[cloud push notifications](https://app.clawmetry.com/push) na pinagana):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ang isang deny ay hinaharang lamang ang isang tool call na iyon — mananatili ang session
ng agent at maaari itong sumubok ng ibang paraan. Ang pag-apruba mula sa iyong telepono ay
nilalaktawan ang sariling permission prompt ng Claude Code (sinagot mo na ito). Makakakuha ka rin ng
push sa telepono kapag ang Claude Code mismo ay naghihintay sa iyo (mga notipikasyong
`permission_prompt` / `idle_prompt`).

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

## Pag-develop ng v2 Frontend

Ang v2 React app ay nasa `frontend/` at naise-serve sa `/v2` kapag
sinimulan ang Flask server nang naka-enable ang v2.

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

Buksan ang `http://localhost:5173/v2/`. Ipoproxy ni Vite ang mga `/api` request patungo sa
`http://localhost:8900`, kaya makakausap ng React app ang lokal na Flask server
nang walang dagdag na CORS setup.

Para i-build ang bundle na kasama sa Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isinusulat sa `clawmetry/static/v2/dist/`.

## Compatibility ng Runtime / Agent

Sinusubaybayan ng ClawMetry ang maraming AI-agent runtime, hindi lang ang OpenClaw. Ang bawat runtime na hindi OpenClaw ay may dedikadong reader adapter na nagsasalin ng native session format nito patungo sa mga pinag-isang hugis ng ClawMetry; ini-ingest ito ng daemon papunta sa parehong DuckDB store + cloud snapshot, na naka-tag ayon sa runtime, at ipinapakita ng Session replay tab ang isang **runtime switcher** kapag mahigit isa ang naroroon. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix + gabay sa pagdaragdag ng mga runtime, at ang [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa primer ng OpenClaw-family.

Ginagamit ang [Perplexity's numbat](https://github.com/perplexityai/numbat) na agent-security tool? Ini-ingest ng ClawMetry ang mga natuklasan at desisyon sa pagpapatupad nito nang walang dagdag na setup, tingnan ang [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference runtime, awtomatikong nade-detect |
| **PicoClaw** | Beta adapter | Patag na JSONL ng `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcripts, modelo, tool call. |
| **NanoClaw** | Beta adapter | Per-session SQLite (`data/v2-sessions`). Transcripts + bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, modelo, tokens/cost. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, modelo, tool call + thinking, paggamit ng token. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, modelo, tool call, paggamit ng token. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, modelo. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat proyekto. Transcripts, modelo, bilang ng token. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, modelo, tool call, kabuuang token. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, modelo, tool call, tokens + cost. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, modelo, tool call, paggamit ng token. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, modelo, tool call, tokens + cost. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, modelo, tool call, tokens + cost. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Mga workflow execution, node run, AI Agent prompt, modelo + tokens kung saan itinatala ito ng n8n. |
| **Antigravity** | Beta adapter | Brain JSONL sa ilalim ng `~/.gemini/<flavor>/brain/`. Mga usapan, tool step, thinking, per-generation na hati ng Gemini token + cost, background-generation na paggamit. |
| **GitHub Copilot** | Beta adapter | Copilot CLI `events.jsonl` sa ilalim ng `~/.copilot/session-state/` + ang `session-store.db` na per-call usage ledger. Mga usapan, tool call, pag-route ng modelo, cache-aware na hati ng token, cost ng AI-credit na sinisingil ng vendor. |
| **Grok** | Beta adapter | xAI Grok Build CLI (Rust binary sa ilalim ng `~/.grok/bin/grok`): global event log `~/.grok/logs/unified.jsonl` + per-session `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Mga usapan, per-turn na hati ng token, pag-route ng modelo, at ang outbound repo payload ng CLI na naka-stage sa ilalim ng `~/.grok/upload_queue/` para makita mo ang lumabas sa iyong makina. |

Ang ibig sabihin ng "Beta adapter" ay nagbibigay ang ClawMetry ng reader para sa aktwal na on-disk format ng runtime na iyon, na bawat isa ay binuo + na-verify laban sa aktwal na install sa aktwal na makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Read-only ang mga adapter; tapat ang bawat isa tungkol sa aktwal na itinatago ng runtime nito (hal., hindi isinusulat ng PicoClaw/NanoClaw/Cursor ang token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, sinasaklaw ng runtime switcher ang view ng mga session sa isa para sa malinis na deep-dive.

## Subaybayan ang anumang SDK agent — out-loop na cost attribution

Isinusulat ng mga runtime sa itaas ang mga session sa disk. Ang sarili mong **production agent**, ang binuo mo gamit ang OpenAI Agents SDK, LangChain, ang Vercel AI SDK, LlamaIndex, E2B, o isang plain na `httpx` loop, ay hindi. Nahuhuli pa rin ng zero-config interceptor ng ClawMetry ang mga LLM call nito (cost, tokens, latency, errors) sa pamamagitan ng monkey-patching ng `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang env var na `CLAWMETRY_SOURCE=support-agent`) ay nagta-tag sa bawat call ng isang **pinangalanang source**, kaya lumalabas ang bawat produktong pinapatakbo mo bilang sarili nitong first-class, cost-attributable na linya sa **🔌 Out-loop sources** card ng dashboard sa Overview, mga call, provider, latency, error rate bawat agent. Walang naka-set na source? Sinusubaybayan pa rin ang mga call; nananatili lang nakatago ang card.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong data layer na pinapakain ng mga runtime adapter (DuckDB → cloud snapshot), kaya nagsi-sync ang out-loop sources sa cloud dashboard katulad ng lahat ng iba pa, E2E-encrypted.

## OpenTelemetry — vendor-neutral, ipadala ang iyong traces kahit saan

Nagsasalita ang ClawMetry ng **OpenTelemetry** sa magkabilang direksyon, gamit ang **GenAI semantic conventions**, kaya hindi kailanman naka-lock ang mga trace ng iyong agent sa isang tool lang.

**I-export** ang bawat session, mga LLM call, tools, sub-agent, tokens, cost, bilang OTLP/HTTP GenAI spans papunta sa anumang collector (Datadog, Grafana, Honeycomb, o sa sarili mong OTel Collector):

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

Makukuha mo ang zero-config, local-first na dashboard ng ClawMetry **at** ang iyong data sa anumang backend na ginagamit na ng iyong team, walang lock-in, walang pangalawang agent na kailangang i-install.

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

## Mga Sinusuportahang Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat channel ng OpenClaw na na-configure mo. Ang mga channel lamang na aktwal na naka-setup sa iyong `openclaw.json` ang lalabas sa Flow diagram, awtomatikong nakatago ang mga hindi pa na-configure.

I-click ang anumang channel node sa Flow para makita ang live chat bubble view na may bilang ng papasok/papalabas na mensahe.

| Channel | Status | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Mga mensahe, istatistika, 10s refresh |
| 💬 **iMessage** | ✅ Full | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Full | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Pag-detect ng guild + channel |
| 🟪 **Slack** | ✅ Full | ✅ | Pag-detect ng workspace + channel |
| 🌐 **Webchat** | ✅ Full | ✅ | Built-in na session ng web UI |
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

> **Auto-detection:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at ire-render lamang ang mga channel na aktwal mong na-configure. Walang kailangang manual na setup.

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

> **Tala:** Kapag pinapatakbo sa Docker, i-mount ang direktoryo ng data + log ng iyong agent (hal., `~/.openclaw`, `~/.claude`, `~/.codex`) para awtomatikong madetect ng ClawMetry ang iyong setup.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong naka-install sa pamamagitan ng pip)
- Isang AI agent runtime sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, o QM (o mga naka-mount na volume para sa Docker)
- Linux o macOS

## Suporta para sa NemoClaw / OpenShell

Awtomatikong nade-detect ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw), ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga agent sa loob ng sandboxed na OpenShell container.

Sa karamihan ng kaso, hindi na kailangan ng dagdag na configuration. Awtomatikong tinutuklas ng sync daemon ang mga session file kung nasa `~/.openclaw/` man ito sa host o sa loob ng isang OpenShell container.

### Paano ito gumagana

Dinidetect ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Pag-detect ng binary** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para kumuha ng impormasyon tungkol sa sandbox
2. **Pag-detect ng container** — sinasaliksik ang mga tumatakbong Docker container para sa `openshell`, `nemoclaw`, o mga imahe ng `ghcr.io/nvidia/`, pagkatapos ay binabasa ang mga session sa pamamagitan ng volume mount o `docker cp`

Ang mga session file na na-sync mula sa mga container ng NemoClaw ay naka-tag ng `runtime=nemoclaw` at metadata ng `container_id` sa cloud dashboard, kaya makikilala mo ang mga ito bukod sa karaniwang mga session ng OpenClaw sa isang sulyap.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Iniiwasan nito ang mga paghihigpit ng network policy ng NemoClaw.

```bash
# On the host (outside the sandbox)
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

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, magdagdag ng egress rule na ito sa iyong network policy ng NemoClaw para maabot nito ang ingest API ng ClawMetry:

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
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa pagtuklas ng container session |

Ang sync daemon ay gumagawa lamang ng outbound HTTPS call papunta sa `ingest.clawmetry.com`. Walang kinakailangang inbound port.

---

## Cloud Deployment

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa SSH tunnels, reverse proxy, at Docker.

## Testing

Ang proyektong ito ay tinetest gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng anonymous na install-lifecycle na mga ping sa
`https://app.clawmetry.com/api/install`: isang `install` ping sa unang
pagkakataon na pinapatakbo mo ang `clawmetry` CLI sa isang bagong makina, isang `update` ping
sa unang run pagkatapos mag-upgrade sa bagong bersyon, at isang `onboarded`
ping kapag natapos mo ang pagpili sa in-dashboard onboarding. Ginagamit namin ito
para bilangin ang aktwal na mga install (ang hilaw na numero ng PyPI download ay ~98% mirrors, CI,
at auto-update na muling pag-download) at para malaman kung aling agent frameworks at
mga bersyon ang aktwal na ginagamit.

**Hindi hihigit sa isang POST bawat lifecycle event bawat bersyon**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na naka-store sa `~/.clawmetry/install_id` | dedup; anonymous hanggang tahasan mong ikonekta ang Cloud sync (ang authenticated daemon heartbeat ang magdadala nito, iuugnay ang install na ito sa iyong account) |
| `event` | `install` / `update` / `onboarded` | bagong install kumpara sa upgrade ng umiiral na |
| `version` | `0.12.167` | anong mga bersyon ang ginagamit |
| `os` / `os_version` | `Darwin` / `25.3.0` | prayoridad sa suporta ng platform |
| `python` | `3.11.15` | matrix ng suporta sa bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | kung anong mga agent ang dapat naming isama sunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga tunay na install ng tao sa ingay ng CI |

**Ang HINDI namin ipinapadala**: IP (kinukuha ng cloud ang country code server-side
mula sa request, pagkatapos ay itinatapon ang IP), hostname, username, path ng workspace,
laman ng file, ang iyong api_key, ang iyong email, anumang PII o
partikular sa workspace. Ang wire payload ay auditable sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng magdi-disable nito):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Hindi kailanman haharangin ng network failure dito ang `clawmetry` sa pagtakbo, ang
ping ay fire-and-forget sa isang daemon thread na may 3 s na timeout.

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
  <strong>🦞 Makita ang pag-iisip ng iyong agent</strong><br>
  <sub>Binuo ni <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
