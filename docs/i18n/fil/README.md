<!-- i18n-src:48548997be76 -->
> Filipino translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Panoorin ang iyong ahente habang nag-iisip.** Real-time na obserbasyon para sa **12 na runtime ng AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex at 8 pa. Isang dashboard para sa iyong buong fleet ng mga ahente.

> 🌐 **Basahin ito sa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Isang utos. Walang konfigurasyong kailangan. Awtomatikong nakita ang lahat.

```bash
pip install clawmetry && clawmetry
```

Magbubukas sa **http://localhost:8900** at tapos na.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Gumagana sa 12 na runtime ng ahente

Nagsimula ang ClawMetry bilang obserbasyon para sa OpenClaw, at ngayon sinusukat nito ang iyong **buong fleet ng mga ahente** sa isang dashboard, awtomatikong nakikita ang bawat runtime sa iyong makina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

Ang OpenClaw at NemoClaw ay libre sa open-source na app; ang ibang mga runtime ay nagagamit sa ClawMetry Cloud o sa isang self-hosted Pro na lisensya. Palitan ang runtime mula sa header at ang bawat tab — gastos, mga token, mga tool, mga trace — ay muling isaklaw sa runtime na iyon.

## Ano ang Makukuha Mo

- **Flow** — Live na animated na diagram na nagpapakita ng mga mensaheng dumadaan sa mga channel, brain, mga tool, at pabalik
- **Overview** — Mga pagsusuri sa kalusugan, activity heatmap, bilang ng mga sesyon, impormasyon ng modelo
- **Usage** — Pagsubaybay ng token at gastos na may araw-araw/linggo-linggo/buwanang pagkakahati
- **Sessions** — Mga aktibong sesyon ng ahente na may modelo, mga token, at huling aktibidad
- **Crons** — Mga nakatakdang trabaho na may katayuan, susunod na takbo, at tagal
- **Logs** — Mga may kulay na real-time na streaming ng log
- **Memory** — Mag-browse ng SOUL.md, MEMORY.md, AGENTS.md, mga tala sa araw-araw
- **Transcripts** — Chat-bubble na UI para sa pagbabasa ng mga kasaysayan ng sesyon
- **Alerts** — Mga limitasyon sa badyet, mga trigger ng rate ng error, pagtuklas ng ahenteng offline; nagpapadala sa Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Pigilan ang mapanganib na mga pagbubura, force push, mga mutasyon ng DB, sudo, pag-install ng package, at mga tawag sa network sa likod ng isang pag-apruba sa pamamagitan ng isang click

## Mga Screenshot

### 🧠 Brain — Live na stream ng mga kaganapan ng ahente
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Paggamit ng token at buod ng sesyon
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Real-time na feed ng mga tawag sa tool
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Pagkakahati ng gastos ayon sa modelo at sesyon
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Browser ng mga file sa workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura at log ng pag-audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Mga limitasyon sa badyet, mga trigger ng rate ng error, mga webhook sa Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Pigilan ang mga mapanganib na tawag sa tool sa likod ng manu-manong pag-apruba; mga patakaran ng proteksyon na sinusuportahan ng polisiya
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## Pag-unlad ng v2 Frontend

Ang v2 React app ay nasa `frontend/` at inihahain sa `/v2` kapag sinimulan ang Flask server na may v2 na pinagana.

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

Buksan ang `http://localhost:5173/v2/`. Ang Vite ay nagpapasa ng mga kahilingan sa `/api` sa `http://localhost:8900`, kaya ang React app ay makakausap sa lokal na Flask server nang walang karagdagang setup ng CORS.

Para buuin ang bundle na kasama ng Python package:

```bash
cd frontend
npm run build
```

Ang production bundle ay isusulat sa `clawmetry/static/v2/dist/`.

## Compatibility ng Runtime / Ahente

Sinusubaybayan ng ClawMetry ang maraming runtime ng AI agent, hindi lamang OpenClaw. Ang bawat non-OpenClaw runtime ay may kasamang dedikadong adapter ng reader na nagsasalin ng katutubong format ng sesyon nito sa mga pinag-isang hugis ng ClawMetry; iniingestion ng daemon ang mga ito sa parehong DuckDB store at cloud snapshot, na may tag ng runtime, at ipinapakita ng Session replay tab ang **runtime switcher** kapag nagkaroon ng higit sa isa. Tingnan ang [`docs/compatibility.md`](docs/compatibility.md) para sa buong matrix at gabay sa pagdaragdag ng mga runtime, at [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) para sa primer ng pamilya ng OpenClaw.

| Runtime / Ahente | Katayuan | Mga Tala |
|---|---|---|
| **OpenClaw** | Native | Reference na runtime, awtomatikong nakita |
| **PicoClaw** | Beta adapter | Flat na `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Mga transcript, modelo, tawag sa tool. |
| **NanoClaw** | Beta adapter | Bawat sesyon na SQLite (`data/v2-sessions`). Mga transcript at bilang ng mensahe. |
| **Hermes** | Beta adapter | SQLite na `~/.hermes/state.db`. Mga transcript, modelo, token/gastos. |
| **Claude Code** | Beta adapter | JSONL na `~/.claude/projects/.../<id>.jsonl`. Mga transcript, modelo, mga tawag sa tool at pag-iisip, paggamit ng token. |
| **Codex** | Beta adapter | Rollout JSONL na `~/.codex/sessions/...`. Mga transcript, modelo, mga tawag sa tool, paggamit ng token. |
| **Cursor** | Beta adapter | SQLite na `state.vscdb`. Mga transcript ng chat/composer, modelo. |
| **Aider** | Beta adapter | `.aider.chat.history.md` bawat proyekto. Mga transcript, modelo, bilang ng token. |
| **Goose** | Beta adapter | SQLite na `~/.local/share/goose`. Mga transcript, modelo, mga tawag sa tool, kabuuang token. |
| **opencode** | Beta adapter | SQLite na `~/.local/share/opencode`. Mga transcript, modelo, mga tawag sa tool, token at gastos. |
| **Qwen Code** | Beta adapter | JSONL na `~/.qwen/projects/.../chats`. Mga transcript, modelo, mga tawag sa tool, paggamit ng token. |

Ang "Beta adapter" ay nangangahulugang ang ClawMetry ay may kasamang reader para sa katutubong format ng runtime na iyon sa disk, ang bawat isa ay binuo at na-verify laban sa totoong pag-install sa totoong makina (tingnan ang `tests/fixtures/runtimes/<rt>/`). Ang mga adapter ay read-only lamang; ang bawat isa ay tapat tungkol sa kung ano talaga ang naitatago ng runtime nito sa disk (hal. ang PicoClaw/NanoClaw/Cursor ay hindi nagsusulat ng token cost sa disk). Kapag maraming runtime ang tumatakbo sa isang node, ang runtime switcher ay nagtatakda ng saklaw ng view ng mga sesyon sa isa para sa malinaw na malalim na pagsisiyasat.

## Subaybayan ang anumang SDK agent — out-loop na pagbibigay-kredito ng gastos

Ang mga runtime sa itaas ay nagsusulat ng mga sesyon sa disk. Ang iyong sariling **production agent** na iyong binuo sa OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o isang plain na `httpx` loop ay hindi. Ang zero-config interceptor ng ClawMetry ay nakukuha pa rin ang mga tawag nito sa LLM (gastos, mga token, latency, mga error) sa pamamagitan ng monkey-patching ng `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

Ang `set_source()` (o ang `CLAWMETRY_SOURCE=support-agent` env var) ay naglalagay ng tag sa bawat tawag ng isang **pinangalanang pinagmulan**, kaya ang bawat produktong pinapatakbo mo ay lilitaw bilang sariling first-class na linya na may pagbibigay-kredito ng gastos sa **🔌 Out-loop sources** na card sa Overview ng dashboard — mga tawag, mga provider, latency, rate ng error bawat ahente. Walang itinakdang pinagmulan? Ang mga tawag ay nananatiling sinusubaybayan; ang card lamang ang mananatiling nakatago.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ito ang parehong layer ng data na pinapakain ng mga runtime adapter (DuckDB patungo sa cloud snapshot), kaya ang mga out-loop na pinagmulan ay nag-sync sa cloud dashboard tulad ng lahat ng iba pa, na may end-to-end na encryption.

## OpenTelemetry — vendor-neutral, ipadala ang iyong mga trace kahit saan

Ang ClawMetry ay gumagamit ng **OpenTelemetry** sa magkabilang direksyon, gamit ang **GenAI semantic conventions**, kaya ang iyong mga trace ng ahente ay hindi kailanman nakaka-lock sa isang tool.

**I-export** ang bawat sesyon — mga tawag sa LLM, mga tool, sub-ahente, mga token, gastos — bilang mga OTLP/HTTP GenAI span sa anumang collector (Datadog, Grafana, Honeycomb, o ang iyong sariling OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Ang mga auth header at agwat ng polling ay mga opsyonal na env var:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — ang built-in na OTLP receiver ay tumatanggap ng mga trace at metric mula sa kahit anong bagay sa `/v1/traces` at `/v1/metrics` (`pip install clawmetry[otel]` para sa protobuf ingest).

Makukuha mo ang zero-config, local-first na ClawMetry dashboard **at** ang iyong data sa anumang backend na pinapatakbo na ng iyong koponan, nang walang lock-in at walang pangalawang ahenteng i-install.

## Konfigurasyong

Karamihan sa mga tao ay hindi nangangailangan ng anumang konfigurasyong. Awtomatikong nakikita ng ClawMetry ang iyong workspace, mga log, mga sesyon, at mga cron.

Kung kailangan mong i-customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Lahat ng opsyon: `clawmetry --help`

## Mga Sinusuportahang Channel

Ipinapakita ng ClawMetry ang live na aktibidad para sa bawat channel ng OpenClaw na iyong na-configure. Ang mga channel lamang na aktwal na na-set up sa iyong `openclaw.json` ang lilitaw sa diagram ng Flow, ang mga hindi na-configure ay awtomatikong itinatago.

I-click ang anumang node ng channel sa Flow para makita ang live na chat bubble view na may bilang ng mga papasok at papalabas na mensahe.

| Channel | Katayuan | Live Popup | Mga Tala |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Buong | ✅ | Mga mensahe, stats, 10s refresh |
| 💬 **iMessage** | ✅ Buong | ✅ | Direktang binabasa ang `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Buong | ✅ | Sa pamamagitan ng WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Buong | ✅ | Sa pamamagitan ng signal-cli |
| 🟣 **Discord** | ✅ Buong | ✅ | Pagtuklas ng guild at channel |
| 🟪 **Slack** | ✅ Buong | ✅ | Pagtuklas ng workspace at channel |
| 🌐 **Webchat** | ✅ Buong | ✅ | Mga built-in na sesyon ng web UI |
| 📡 **IRC** | ✅ Buong | ✅ | Terminal-style na bubble UI |
| 🍏 **BlueBubbles** | ✅ Buong | ✅ | iMessage sa pamamagitan ng BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Buong | ✅ | Sa pamamagitan ng mga webhook ng Chat API |
| 🟣 **MS Teams** | ✅ Buong | ✅ | Sa pamamagitan ng Teams bot plugin |
| 🔷 **Mattermost** | ✅ Buong | ✅ | Self-hosted na team chat |
| 🟩 **Matrix** | ✅ Buong | ✅ | Desentralisado, suporta sa E2EE |
| 🟢 **LINE** | ✅ Buong | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Buong | ✅ | Desentralisadong NIP-04 DM |
| 🟣 **Twitch** | ✅ Buong | ✅ | Chat sa pamamagitan ng koneksyon ng IRC |
| 🔷 **Feishu/Lark** | ✅ Buong | ✅ | Subscription sa kaganapan ng WebSocket |
| 🔵 **Zalo** | ✅ Buong | ✅ | Zalo Bot API |

> **Awtomatikong pagtuklas:** Binabasa ng ClawMetry ang iyong `~/.openclaw/openclaw.json` at inirerender lamang ang mga channel na aktwal mong na-configure. Walang manu-manong setup na kailangan.

## Pag-deploy gamit ang Docker

Gusto mo bang patakbuhin ang ClawMetry sa isang container? Walang problema! 🐳

**Mabilis na pagsisimula gamit ang Docker:**

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

> **Tandaan:** Kapag tumatakbo sa Docker, i-mount ang direktoryo ng data at log ng iyong ahente (hal. `~/.openclaw`, `~/.claude`, `~/.codex`) para awtomatikong matuklasan ng ClawMetry ang iyong setup.

## Mga Kinakailangan

- Python 3.8+
- Flask (awtomatikong ini-install sa pamamagitan ng pip)
- Isang runtime ng AI agent sa parehong makina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, o PicoClaw (o mga naka-mount na volume para sa Docker)
- Linux o macOS

## Suporta para sa NemoClaw / OpenShell

Awtomatikong nakita ng ClawMetry ang [NemoClaw](https://github.com/NVIDIA/NemoClaw), ang enterprise security wrapper ng NVIDIA para sa OpenClaw na nagpapatakbo ng mga ahente sa loob ng mga naka-sandbox na OpenShell container.

Sa karamihan ng mga kaso, hindi kailangan ng karagdagang konfigurasyong. Awtomatikong nahahanap ng sync daemon ang mga file ng sesyon kahit nasa `~/.openclaw/` sa host o sa loob ng isang OpenShell container.

### Paano ito gumagana

Nakikita ng ClawMetry ang NemoClaw sa dalawang paraan:

1. **Pagtuklas ng binary** — sinusuri ang `nemoclaw` CLI at pinapatakbo ang `nemoclaw status` para makuha ang impormasyon ng sandbox
2. **Pagtuklas ng container** — siniscan ang mga tumatakbong Docker container para sa mga image na `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, pagkatapos ay binabasa ang mga sesyon sa pamamagitan ng mga volume mount o `docker cp`

Ang mga file ng sesyon na na-sync mula sa mga NemoClaw container ay may tag na `runtime=nemoclaw` at metadata ng `container_id` sa cloud dashboard, para madali mong matukoy ang mga ito mula sa mga karaniwang sesyon ng OpenClaw.

### Inirerekomendang setup: sync daemon sa HOST

Para sa pinakamahusay na karanasan, patakbuhin ang sync daemon ng ClawMetry sa **host machine** (hindi sa loob ng sandbox). Iniiwan nito ang mga paghihigpit ng network policy ng NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Awtomatikong mahahanap ng sync daemon ang mga sesyon sa loob ng anumang tumatakbong OpenShell container.

### Opsyonal: tahasang pangalan ng sandbox

Kung hindi gumagana ang awtomatikong pagtuklas, ituro ang ClawMetry sa tamang sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Pagpapatakbo sa loob ng sandbox (advanced)

Kung kailangan mong patakbuhin ang sync daemon **sa loob** ng OpenShell sandbox, idagdag ang egress rule na ito sa iyong network policy ng NemoClaw para maabot nito ang ClawMetry ingest API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Ilapat gamit ang:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Mga port at endpoint

| Endpoint | Port | Protocol | Kailangan |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Oo (sync daemon patungo sa cloud) |
| `localhost:8900` | 8900 | HTTP | Oo (lokal na dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Para sa pagtuklas ng sesyon ng container |

Ang sync daemon ay gumagawa lamang ng papalabas na mga tawag sa HTTPS sa `ingest.clawmetry.com`. Walang kailangang papasok na port.

---

## Pag-deploy sa Cloud

Tingnan ang **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** para sa mga SSH tunnel, reverse proxy, at Docker.

## Pagsubok

Ang proyektong ito ay sinubukan gamit ang BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

Nagpapadala ang ClawMetry ng isang anonymous na "first run" na ping sa
`https://app.clawmetry.com/api/install` sa unang pagkakataon na patakbuhin mo ang
`clawmetry` CLI sa isang bagong makina. Ginagamit namin ito para bilangin ang mga pag-install (ang
tanging sukatan ng marketing na mayroon kami para sa isang OSS na proyekto) at para malaman kung aling
mga framework ng ahente ang naka-install ng aming mga gumagamit.

**Eksaktong isang POST bawat pag-install**, na naglalaman ng:

| Field | Halimbawa | Bakit |
|---|---|---|
| `install_id` | random UUID na nakaimbak sa `~/.clawmetry/install_id` | dedup; hindi naka-link sa iyong email o api_key |
| `version` | `0.12.167` | kung anong mga bersyon ang nasa labas |
| `os` / `os_version` | `Darwin` / `25.3.0` | mga priyoridad ng suporta sa platform |
| `python` | `3.11.15` | matrix ng suporta sa bersyon ng Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | kung aling mga ahente ang dapat naming isama sa susunod |
| `is_ci` / `ci_provider` | `true` / `github_actions` | paghihiwalay ng mga pag-install ng tao mula sa ingay ng CI |

**Ang hindi namin ipinapadala**: IP (ang cloud ay nagkukuha ng country code sa server-side
mula sa kahilingan, pagkatapos ay itatapon ang IP), hostname, username, path ng workspace,
mga nilalaman ng file, ang iyong api_key, ang iyong email, anumang PII o
espesipikong impormasyon ng workspace. Ang wire payload ay maaaring masuri sa
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Mag-opt out** (alinman sa mga ito ay permanenteng hindi ito pinagana):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ang isang pagkabigo sa network dito ay hindi kailanman pumipigil sa `clawmetry` na tumakbo, ang
ping ay fire-and-forget sa isang daemon thread na may 3 segundo na timeout.

## Kasaysayan ng Bituin

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
  <sub>Ginawa ng <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bahagi ng ecosystem ng <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
