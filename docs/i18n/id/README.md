<!-- i18n-src:02b789586c7d -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Lihat agen Anda berpikir.** Observabilitas real-time untuk **14 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 10 lainnya. Satu dashboard untuk seluruh armada agen Anda.

> 🌐 **Baca dalam bahasa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900** dan Anda selesai.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Berfungsi dengan 14 runtime agen

ClawMetry dimulai sebagai observabilitas untuk OpenClaw, dan kini mengukur **seluruh armada agen** Anda dalam satu dashboard, mendeteksi setiap runtime di mesin Anda secara otomatis:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw dan NemoClaw gratis di aplikasi open-source; runtime lainnya aktif dengan ClawMetry Cloud atau lisensi Pro self-hosted. Beralih runtime dari header, dan setiap tab (biaya, token, tools, trace) akan menyesuaikan cakupannya ke runtime tersebut. Lihat **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** untuk pembagian gratis/berbayar yang tepat, matriks tingkatan, bentuk `/api/entitlement`, dan CLI `clawmetry license`.

## Apa yang Anda Dapatkan

- **Flow**: Diagram animasi live yang menampilkan pesan mengalir melalui channel, brain, tools, dan kembali
- **Overview**: Health check, activity heatmap, jumlah session, info model
- **Usage**: Pelacakan token dan biaya dengan rincian harian/mingguan/bulanan
- **Sessions**: Session agent yang aktif beserta model, token, aktivitas terakhir
- **Crons**: Tugas terjadwal dengan status, run berikutnya, durasi
- **Logs**: Streaming log real-time dengan kode warna
- **Memory**: Jelajahi SOUL.md, MEMORY.md, AGENTS.md, catatan harian
- **Transcripts**: UI chat-bubble untuk membaca riwayat session
- **Alerts**: Batas anggaran, pemicu tingkat error, deteksi agent offline; diarahkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: Menahan penghapusan destruktif, force push, mutasi DB, sudo, instalasi paket, panggilan network di balik persetujuan satu klik

## Screenshot

### 🧠 Brain: Stream event agent secara live
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: Penggunaan token & ringkasan session
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: Feed pemanggilan tool real-time
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: Rincian biaya berdasarkan model & session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: Penjelajah file workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: Postur & log audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: Batas anggaran, pemicu tingkat error, webhook ke Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: Menahan pemanggilan tool berisiko di balik persetujuan manual; aturan proteksi berbasis kebijakan
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pemblokiran pra-eksekusi untuk Claude Code**: satu perintah menginstal hook
PreToolUse yang menjeda pemanggilan tool yang cocok *sebelum* dijalankan dan menunggu
keputusan Anda (satu ketukan dari ponsel Anda dengan
[notifikasi push cloud](https://app.clawmetry.com/push) diaktifkan):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Penolakan (deny) hanya memblokir satu pemanggilan tool tersebut; agent tetap
mempertahankan session-nya dan dapat mencoba pendekatan lain. Menyetujui dari
ponsel Anda melewati prompt izin bawaan Claude Code (Anda sudah menjawabnya).
Tool yang tidak cocok hanya memakan waktu ~40ms dan diteruskan ke alur izin
normal Claude Code. Anda juga akan menerima push ke ponsel saat Claude Code
sendiri sedang menunggu Anda (notifikasi `permission_prompt` / `idle_prompt`).

## Instalasi

**Satu baris perintah (direkomendasikan):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Dari source:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Pengembangan Frontend v2

Aplikasi React v2 berada di `frontend/` dan disajikan di `/v2` ketika server
Flask dijalankan dengan v2 diaktifkan.

Gunakan dua terminal saat melakukan pengembangan:

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

Buka `http://localhost:5173/v2/`. Vite mem-proxy request `/api` ke
`http://localhost:8900`, sehingga aplikasi React dapat berkomunikasi dengan
server Flask lokal tanpa perlu setup CORS tambahan.

Untuk membangun bundle yang dikirim bersama paket Python:

```bash
cd frontend
npm run build
```

Bundle produksi ditulis ke `clawmetry/static/v2/dist/`.

## Kompatibilitas Runtime / Agent

ClawMetry mengamati banyak runtime AI-agent, tidak hanya OpenClaw. Setiap runtime selain OpenClaw dilengkapi adapter reader khusus yang menerjemahkan format session native-nya ke dalam bentuk terpadu ClawMetry; daemon menyerap (ingest) data tersebut ke DuckDB store + cloud snapshot yang sama, ditandai dengan runtime-nya, dan tab Session replay menampilkan **runtime switcher** ketika ada lebih dari satu runtime. Lihat [`docs/compatibility.md`](docs/compatibility.md) untuk matriks lengkap + panduan menambahkan runtime, dan [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) untuk pengantar keluarga OpenClaw.

| Runtime / Agent | Status | Catatan |
|---|---|---|
| **OpenClaw** | Native | Runtime referensi, terdeteksi otomatis |
| **PicoClaw** | Adapter beta | JSONL `providers.Message` flat (`~/.picoclaw/workspace/sessions`). Transcript, model, pemanggilan tool. |
| **NanoClaw** | Adapter beta | SQLite per-session (`data/v2-sessions`). Transcript + jumlah pesan. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transcript, model, token/biaya. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcript, model, pemanggilan tool + thinking, penggunaan token. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transcript, model, pemanggilan tool, penggunaan token. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transcript chat/composer, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` per project. Transcript, model, jumlah token. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transcript, model, pemanggilan tool, total token. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transcript, model, pemanggilan tool, token + biaya. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transcript, model, pemanggilan tool, penggunaan token. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transcript, model, pemanggilan tool, token + biaya. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transcript, model, pemanggilan tool, token + biaya. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Eksekusi workflow, run node, prompt AI Agent, model + token jika dicatat oleh n8n. |
| **Antigravity** | Adapter beta | Brain JSONL di bawah `~/.gemini/<flavor>/brain/`. Percakapan, langkah tool, thinking, rincian token Gemini per generasi + biaya, burn dari background-generation. |

"Adapter beta" berarti ClawMetry menyediakan reader untuk format on-disk asli runtime tersebut, masing-masing dibangun + diverifikasi terhadap instalasi nyata di mesin nyata (lihat `tests/fixtures/runtimes/<rt>/`). Adapter bersifat read-only; masing-masing jujur soal apa yang benar-benar disimpan oleh runtime-nya (misalnya PicoClaw/NanoClaw/Cursor tidak menulis biaya token ke disk). Saat beberapa runtime berjalan di satu node, runtime switcher membatasi tampilan sessions ke satu runtime untuk deep-dive yang bersih.

## Lacak agent SDK apa pun (atribusi biaya out-loop)

Semua runtime di atas menulis session ke disk. **Production agent** Anda sendiri (yang Anda bangun di atas OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, atau loop `httpx` biasa) tidak melakukannya. Interceptor zero-config milik ClawMetry tetap menangkap pemanggilan LLM-nya (biaya, token, latensi, error) dengan melakukan monkey-patch pada `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (atau env var `CLAWMETRY_SOURCE=support-agent`) menandai setiap panggilan dengan **named source**, sehingga setiap produk yang Anda jalankan muncul sebagai baris tersendiri yang first-class dan dapat diatribusikan biayanya di kartu **🔌 Out-loop sources** pada Overview di dashboard (panggilan, provider, latensi, tingkat error per agent). Tidak mengatur source? Panggilan tetap dilacak; kartunya saja yang tetap disembunyikan.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ini adalah data layer yang sama yang diisi oleh adapter runtime (DuckDB → cloud snapshot), sehingga out-loop sources tersinkronisasi ke dashboard cloud sama seperti yang lainnya, terenkripsi E2E.

## OpenTelemetry (netral vendor, kirim trace Anda ke mana saja)

ClawMetry berbicara **OpenTelemetry** dalam dua arah, menggunakan **GenAI semantic conventions**, sehingga trace agent Anda tidak pernah terkunci pada satu tool saja.

**Export** setiap session (pemanggilan LLM, tools, sub-agent, token, biaya) sebagai OTLP/HTTP GenAI span ke collector apa pun (Datadog, Grafana, Honeycomb, atau OTel Collector Anda sendiri):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth header dan poll interval adalah env var opsional:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest**: OTLP receiver bawaan menerima trace dan metric dari sumber lain apa pun di `/v1/traces` dan `/v1/metrics` (`pip install clawmetry[otel]` untuk ingest protobuf).

Anda mendapatkan dashboard ClawMetry yang zero-config dan local-first **dan** data Anda di backend apa pun yang sudah dijalankan tim Anda, tanpa lock-in, tanpa perlu menginstal agent kedua.

## Konfigurasi

Kebanyakan orang tidak memerlukan konfigurasi apa pun. ClawMetry mendeteksi workspace, log, session, dan cron Anda secara otomatis.

Jika Anda memang perlu melakukan kustomisasi:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Semua opsi: `clawmetry --help`

## Channel yang Didukung

ClawMetry menampilkan aktivitas live untuk setiap channel OpenClaw yang telah Anda konfigurasikan. Hanya channel yang benar-benar diatur di `openclaw.json` Anda yang muncul di diagram Flow; yang belum dikonfigurasi otomatis disembunyikan.

Klik node channel mana pun di Flow untuk melihat tampilan chat bubble live dengan jumlah pesan masuk/keluar.

| Channel | Status | Live Popup | Catatan |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Lengkap | ✅ | Pesan, statistik, refresh 10 detik |
| 💬 **iMessage** | ✅ Lengkap | ✅ | Membaca `~/Library/Messages/chat.db` langsung |
| 💚 **WhatsApp** | ✅ Lengkap | ✅ | Melalui WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Lengkap | ✅ | Melalui signal-cli |
| 🟣 **Discord** | ✅ Lengkap | ✅ | Deteksi guild + channel |
| 🟪 **Slack** | ✅ Lengkap | ✅ | Deteksi workspace + channel |
| 🌐 **Webchat** | ✅ Lengkap | ✅ | Session web UI bawaan |
| 📡 **IRC** | ✅ Lengkap | ✅ | UI bubble bergaya terminal |
| 🍏 **BlueBubbles** | ✅ Lengkap | ✅ | iMessage melalui REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Lengkap | ✅ | Melalui webhook Chat API |
| 🟣 **MS Teams** | ✅ Lengkap | ✅ | Melalui plugin bot Teams |
| 🔷 **Mattermost** | ✅ Lengkap | ✅ | Chat tim self-hosted |
| 🟩 **Matrix** | ✅ Lengkap | ✅ | Terdesentralisasi, dukungan E2EE |
| 🟢 **LINE** | ✅ Lengkap | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Lengkap | ✅ | DM NIP-04 terdesentralisasi |
| 🟣 **Twitch** | ✅ Lengkap | ✅ | Chat melalui koneksi IRC |
| 🔷 **Feishu/Lark** | ✅ Lengkap | ✅ | Langganan event WebSocket |
| 🔵 **Zalo** | ✅ Lengkap | ✅ | Zalo Bot API |

> **Deteksi otomatis:** ClawMetry membaca `~/.openclaw/openclaw.json` Anda dan hanya me-render channel yang benar-benar Anda konfigurasikan. Tidak diperlukan setup manual.

## Deployment Docker

Ingin menjalankan ClawMetry dalam container? Tidak masalah! 🐳

**Quick start dengan Docker:**

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

**Contoh Docker Compose:**

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

> **Catatan:** Saat menjalankan di Docker, mount direktori data + log agent Anda (misalnya `~/.openclaw`, `~/.claude`, `~/.codex`) agar ClawMetry dapat mendeteksi setup Anda secara otomatis.

## Persyaratan

- Python 3.8+
- Flask (terinstal otomatis via pip)
- Runtime agent AI di mesin yang sama: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, atau Antigravity (atau volume yang di-mount untuk Docker)
- Linux atau macOS

## Dukungan NemoClaw / OpenShell

ClawMetry secara otomatis mendeteksi [NemoClaw](https://github.com/NVIDIA/NemoClaw), wrapper keamanan enterprise dari NVIDIA untuk OpenClaw yang menjalankan agent di dalam container OpenShell yang disandbox.

Tidak diperlukan konfigurasi tambahan dalam kebanyakan kasus. Sync daemon secara otomatis menemukan file session baik yang berada di `~/.openclaw/` pada host maupun di dalam container OpenShell.

### Cara kerjanya

ClawMetry mendeteksi NemoClaw dengan dua cara:

1. **Deteksi biner**: memeriksa keberadaan CLI `nemoclaw` dan menjalankan `nemoclaw status` untuk mendapatkan info sandbox
2. **Deteksi container**: memindai container Docker yang berjalan untuk image `openshell`, `nemoclaw`, atau `ghcr.io/nvidia/`, lalu membaca session melalui volume mount atau `docker cp`

File session yang disinkronkan dari container NemoClaw ditandai dengan metadata `runtime=nemoclaw` dan `container_id` di dashboard cloud, sehingga Anda dapat membedakannya dari session OpenClaw standar sekilas saja.

### Setup yang direkomendasikan: sync daemon di HOST

Untuk pengalaman terbaik, jalankan sync daemon ClawMetry pada **mesin host** (bukan di dalam sandbox). Ini menghindari pembatasan network policy NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync daemon akan secara otomatis menemukan session di dalam container OpenShell mana pun yang sedang berjalan.

### Opsional: nama sandbox eksplisit

Jika deteksi otomatis tidak berhasil, arahkan ClawMetry ke sandbox yang tepat:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Menjalankan di dalam sandbox (lanjutan)

Jika Anda harus menjalankan sync daemon **di dalam** sandbox OpenShell, tambahkan aturan egress ini ke network policy NemoClaw Anda agar dapat menjangkau ingest API ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Terapkan dengan:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Port dan endpoint

| Endpoint | Port | Protokol | Wajib |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ya (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Ya (UI dashboard lokal) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Untuk penemuan session container |

Sync daemon hanya melakukan panggilan HTTPS outbound ke `ingest.clawmetry.com`. Tidak diperlukan port inbound.

---

## Deployment Cloud

Lihat **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** untuk SSH tunnel, reverse proxy, dan Docker.

## Pengujian

Proyek ini diuji dengan BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry mengirim ping install-lifecycle anonim ke
`https://app.clawmetry.com/api/install`: satu ping `install` pada pertama
kali Anda menjalankan CLI `clawmetry` di mesin baru, satu ping `update`
pada run pertama setelah upgrade ke versi baru, dan satu ping `onboarded`
saat Anda menyelesaikan pilihan onboarding di dashboard. Kami menggunakan
ini untuk menghitung install yang sebenarnya (angka unduhan PyPI mentah
sekitar 98%-nya adalah mirror, CI, dan unduhan ulang auto-update) dan
untuk mengetahui framework serta versi agent apa yang sebenarnya
digunakan di lapangan.

**Maksimal satu POST per lifecycle event per versi**, berisi:

| Field | Contoh | Alasan |
|---|---|---|
| `install_id` | random UUID stored at `~/.clawmetry/install_id` | dedup; anonim hingga Anda secara eksplisit menghubungkan Cloud sync (heartbeat daemon yang terautentikasi kemudian membawanya, menghubungkan install ini ke akun Anda) |
| `event` | `install` / `update` / `onboarded` | install baru vs upgrade dari yang sudah ada |
| `version` | `0.12.167` | versi apa saja yang digunakan di lapangan |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioritas dukungan platform |
| `python` | `3.11.15` | matriks dukungan versi Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | agent mana yang harus kami integrasikan berikutnya |
| `is_ci` / `ci_provider` | `true` / `github_actions` | memisahkan install manusia dari noise CI |

**Yang TIDAK kami kirim**: IP (cloud menurunkan kode negara secara
server-side dari request, lalu membuang IP-nya), hostname, username,
path workspace, isi file, api_key Anda, email Anda, atau apa pun yang
bersifat PII atau spesifik-workspace. Payload yang dikirim dapat diaudit
di [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Opt out** (salah satu dari berikut ini akan menonaktifkannya secara permanen):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Kegagalan network di sini tidak pernah memblokir `clawmetry` untuk
berjalan; ping bersifat fire-and-forget pada daemon thread dengan
timeout 3 detik.

## Riwayat Star

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lisensi

MIT

---

<p align="center">
  <strong>🦞 Lihat agen Anda berpikir</strong><br>
  <sub>Dibuat oleh <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bagian dari ekosistem <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
