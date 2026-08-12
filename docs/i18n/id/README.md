<!-- i18n-src:7cfb63716507 -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Lihat agen Anda berpikir.** Observabilitas real-time untuk **14 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 10 lainnya. Satu dashboard untuk seluruh armada agen Anda.

> 🌐 **Baca ini dalam:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900** dan selesai.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Bekerja dengan 14 runtime agen

ClawMetry dimulai sebagai observabilitas untuk OpenClaw, dan kini mengukur **seluruh armada agen Anda** dalam satu dashboard, secara otomatis mendeteksi setiap runtime di mesin Anda:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw dan NemoClaw gratis di aplikasi open-source; runtime lainnya aktif dengan ClawMetry Cloud atau lisensi Pro self-hosted. Beralih runtime dari header, dan setiap tab (biaya, token, alat, trace) akan menyesuaikan cakupan ke runtime tersebut. Lihat **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** untuk pembagian gratis/berbayar yang tepat, matriks tier, bentuk `/api/entitlement`, dan CLI `clawmetry license`.

## Apa yang Anda Dapatkan

- **Flow** — Diagram animasi langsung yang menampilkan pesan mengalir melalui channel, brain, alat, dan kembali
- **Overview** — Pemeriksaan kesehatan, heatmap aktivitas, jumlah sesi, info model
- **Usage** — Pelacakan token dan biaya dengan rincian harian/mingguan/bulanan
- **Sessions** — Sesi agen aktif dengan model, token, aktivitas terakhir
- **Crons** — Pekerjaan terjadwal dengan status, run berikutnya, durasi
- **Logs** — Streaming log real-time dengan kode warna
- **Memory** — Jelajahi SOUL.md, MEMORY.md, AGENTS.md, catatan harian
- **Transcripts** — UI gelembung obrolan untuk membaca riwayat sesi
- **Alerts** — Batas anggaran, pemicu tingkat kesalahan, deteksi agen offline; diarahkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Menahan penghapusan destruktif, force push, mutasi database, sudo, instalasi paket, panggilan jaringan di balik satu klik persetujuan

## Tangkapan Layar

### 🧠 Brain — Aliran event agen langsung
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Penggunaan token & ringkasan sesi
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Umpan panggilan alat real-time
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Rincian biaya berdasarkan model & sesi
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Penjelajah file workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postur & log audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Batas anggaran, pemicu tingkat kesalahan, webhook ke Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Menahan panggilan alat berisiko di balik persetujuan manual; aturan perlindungan berbasis kebijakan
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pemblokiran pra-eksekusi untuk Claude Code** — satu perintah menginstal
hook PreToolUse yang menjeda panggilan alat yang cocok *sebelum* dijalankan dan menunggu
keputusan Anda (satu ketukan dari ponsel Anda dengan
[notifikasi push cloud](https://app.clawmetry.com/push) diaktifkan):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Sebuah deny hanya memblokir satu panggilan alat tersebut, agen tetap mempertahankan sesinya dan dapat
mencoba pendekatan lain. Menyetujui dari ponsel Anda melewati prompt izin
milik Claude Code sendiri (Anda sudah menjawabnya). Alat yang tidak cocok memakan biaya ~40ms dan
kembali ke alur izin normal Claude Code. Anda juga mendapatkan push ke ponsel saat Claude Code sendiri
sedang menunggu Anda (notifikasi `permission_prompt` /
`idle_prompt`).

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

Aplikasi React v2 berada di `frontend/` dan disajikan di `/v2` ketika
server Flask dijalankan dengan v2 diaktifkan.

Gunakan dua terminal saat mengembangkan:

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

Buka `http://localhost:5173/v2/`. Vite mem-proxy permintaan `/api` ke
`http://localhost:8900`, sehingga aplikasi React dapat berkomunikasi dengan server Flask lokal
tanpa pengaturan CORS tambahan.

Untuk membangun bundle yang dikirim bersama paket Python:

```bash
cd frontend
npm run build
```

Bundle produksi ditulis ke `clawmetry/static/v2/dist/`.

## Kompatibilitas Runtime / Agen

ClawMetry mengamati banyak runtime agen AI, tidak hanya OpenClaw. Setiap runtime selain OpenClaw dilengkapi adapter pembaca khusus yang menerjemahkan format sesi native-nya ke dalam bentuk terpadu ClawMetry; daemon menyerapnya ke dalam DuckDB store dan snapshot cloud yang sama, ditandai dengan runtime-nya, dan tab Session replay menampilkan **pengalih runtime** ketika lebih dari satu hadir. Lihat [`docs/compatibility.md`](docs/compatibility.md) untuk matriks lengkap + panduan menambahkan runtime, dan [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) untuk primer keluarga OpenClaw.

Menjalankan alat keamanan agen [numbat milik Perplexity](https://github.com/perplexityai/numbat)? ClawMetry menyerap temuan dan keputusan penegakannya secara langsung, lihat [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agen | Status | Catatan |
|---|---|---|
| **OpenClaw** | Native | Runtime referensi, terdeteksi otomatis |
| **PicoClaw** | Adapter beta | JSONL `providers.Message` datar (`~/.picoclaw/workspace/sessions`). Transkrip, model, panggilan alat. |
| **NanoClaw** | Adapter beta | SQLite per-sesi (`data/v2-sessions`). Transkrip + jumlah pesan. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transkrip, model, token/biaya. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrip, model, panggilan alat + pemikiran, penggunaan token. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transkrip, model, panggilan alat, penggunaan token. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transkrip chat/composer, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` per proyek. Transkrip, model, jumlah token. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transkrip, model, panggilan alat, total token. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transkrip, model, panggilan alat, token + biaya. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transkrip, model, panggilan alat, penggunaan token. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transkrip, model, panggilan alat, token + biaya. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transkrip, model, panggilan alat, token + biaya. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Eksekusi workflow, run node, prompt AI Agent, model + token bila dicatat oleh n8n. |
| **Antigravity** | Adapter beta | Brain JSONL di bawah `~/.gemini/<flavor>/brain/`. Percakapan, langkah alat, pemikiran, rincian token Gemini per generasi + biaya, pembakaran generasi latar belakang. |
| **GitHub Copilot** | Adapter beta | Copilot CLI `events.jsonl` di bawah `~/.copilot/session-state/` + buku besar penggunaan per-panggilan `session-store.db`. Percakapan, panggilan alat, perutean model, rincian token yang sadar cache, biaya kredit-AI yang ditagih vendor. |
| **Grok** | Adapter beta | xAI Grok Build CLI (biner Rust di bawah `~/.grok/bin/grok`): log event global `~/.grok/logs/unified.jsonl` + per-sesi `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Percakapan, rincian token per giliran, perutean model, dan payload repo keluar dari CLI yang dipentaskan di `~/.grok/upload_queue/` sehingga Anda dapat melihat apa yang keluar dari mesin Anda. |

"Adapter beta" berarti ClawMetry mengirimkan pembaca untuk format asli di disk milik runtime tersebut, masing-masing dibangun + diverifikasi terhadap instalasi nyata pada mesin nyata (lihat `tests/fixtures/runtimes/<rt>/`). Adapter bersifat read-only; masing-masing jujur tentang apa yang benar-benar disimpan oleh runtime-nya (misalnya PicoClaw/NanoClaw/Cursor tidak menulis biaya token ke disk). Ketika beberapa runtime berjalan pada satu node, pengalih runtime membatasi tampilan sesi ke satu runtime untuk deep-dive yang bersih.

## Melacak agen SDK apa pun — atribusi biaya out-loop

Runtime-runtime di atas semuanya menulis sesi ke disk. **Agen produksi** Anda sendiri, yang Anda bangun di atas OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, atau loop `httpx` biasa, tidak melakukannya. Interceptor tanpa-konfigurasi milik ClawMetry tetap menangkap panggilan LLM-nya (biaya, token, latensi, kesalahan) dengan melakukan monkey-patch pada `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (atau variabel lingkungan `CLAWMETRY_SOURCE=support-agent`) menandai setiap panggilan dengan **sumber bernama**, sehingga setiap produk yang Anda jalankan muncul sebagai baris tersendiri kelas satu yang dapat diatribusikan biayanya di kartu **🔌 Out-loop sources** pada Overview dashboard, panggilan, provider, latensi, tingkat kesalahan per agen. Tidak ada sumber yang diatur? Panggilan tetap dilacak; kartu tersebut hanya tetap tersembunyi.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ini adalah lapisan data yang sama yang diberi makan oleh adapter runtime (DuckDB → snapshot cloud), sehingga sumber out-loop tersinkron ke dashboard cloud sama seperti hal lainnya, terenkripsi E2E.

## OpenTelemetry — netral vendor, kirim trace Anda ke mana saja

ClawMetry berbicara **OpenTelemetry** dalam dua arah, menggunakan **konvensi semantik GenAI**, sehingga trace agen Anda tidak pernah terkunci pada satu alat.

**Ekspor** setiap sesi (panggilan LLM, alat, sub-agen, token, biaya) sebagai span GenAI OTLP/HTTP ke collector mana pun (Datadog, Grafana, Honeycomb, atau OTel Collector Anda sendiri):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Header autentikasi dan interval polling adalah variabel lingkungan opsional:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Serap** — receiver OTLP bawaan menerima trace dan metrik dari hal lain apa pun di `/v1/traces` dan `/v1/metrics` (`pip install clawmetry[otel]` untuk penyerapan protobuf).

Anda mendapatkan dashboard ClawMetry yang tanpa konfigurasi, lokal-first, **dan** data Anda di backend apa pun yang sudah digunakan tim Anda, tanpa penguncian vendor, tanpa perlu menginstal agen kedua.

## Konfigurasi

Kebanyakan orang tidak memerlukan konfigurasi apa pun. ClawMetry secara otomatis mendeteksi workspace, log, sesi, dan cron Anda.

Jika Anda perlu menyesuaikan:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Semua opsi: `clawmetry --help`

## Channel yang Didukung

ClawMetry menampilkan aktivitas langsung untuk setiap channel OpenClaw yang Anda konfigurasikan. Hanya channel yang benar-benar diatur di `openclaw.json` Anda yang muncul di diagram Flow; yang belum dikonfigurasi otomatis disembunyikan.

Klik node channel mana pun di Flow untuk melihat tampilan gelembung obrolan langsung dengan jumlah pesan masuk/keluar.

| Channel | Status | Popup Langsung | Catatan |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Penuh | ✅ | Pesan, statistik, refresh 10 detik |
| 💬 **iMessage** | ✅ Penuh | ✅ | Membaca `~/Library/Messages/chat.db` secara langsung |
| 💚 **WhatsApp** | ✅ Penuh | ✅ | Melalui WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Penuh | ✅ | Melalui signal-cli |
| 🟣 **Discord** | ✅ Penuh | ✅ | Deteksi guild + channel |
| 🟪 **Slack** | ✅ Penuh | ✅ | Deteksi workspace + channel |
| 🌐 **Webchat** | ✅ Penuh | ✅ | Sesi UI web bawaan |
| 📡 **IRC** | ✅ Penuh | ✅ | UI gelembung gaya terminal |
| 🍏 **BlueBubbles** | ✅ Penuh | ✅ | iMessage melalui REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Penuh | ✅ | Melalui webhook Chat API |
| 🟣 **MS Teams** | ✅ Penuh | ✅ | Melalui plugin bot Teams |
| 🔷 **Mattermost** | ✅ Penuh | ✅ | Chat tim self-hosted |
| 🟩 **Matrix** | ✅ Penuh | ✅ | Terdesentralisasi, dukungan E2EE |
| 🟢 **LINE** | ✅ Penuh | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Penuh | ✅ | DM NIP-04 terdesentralisasi |
| 🟣 **Twitch** | ✅ Penuh | ✅ | Chat melalui koneksi IRC |
| 🔷 **Feishu/Lark** | ✅ Penuh | ✅ | Langganan event WebSocket |
| 🔵 **Zalo** | ✅ Penuh | ✅ | Zalo Bot API |

> **Deteksi otomatis:** ClawMetry membaca `~/.openclaw/openclaw.json` Anda dan hanya merender channel yang benar-benar Anda konfigurasikan. Tidak diperlukan pengaturan manual.

## Deployment Docker

Ingin menjalankan ClawMetry dalam kontainer? Tidak masalah! 🐳

**Mulai cepat dengan Docker:**

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

> **Catatan:** Saat menjalankan di Docker, mount direktori data + log agen Anda (misalnya `~/.openclaw`, `~/.claude`, `~/.codex`) sehingga ClawMetry dapat mendeteksi pengaturan Anda secara otomatis.

## Persyaratan

- Python 3.8+
- Flask (terinstal otomatis melalui pip)
- Runtime agen AI pada mesin yang sama: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, atau QM (atau volume yang di-mount untuk Docker)
- Linux atau macOS

## Dukungan NemoClaw / OpenShell

ClawMetry secara otomatis mendeteksi [NemoClaw](https://github.com/NVIDIA/NemoClaw), wrapper keamanan enterprise milik NVIDIA untuk OpenClaw yang menjalankan agen di dalam kontainer OpenShell yang di-sandbox.

Tidak diperlukan konfigurasi tambahan dalam kebanyakan kasus. Daemon sinkronisasi secara otomatis menemukan file sesi baik yang berada di `~/.openclaw/` pada host maupun di dalam kontainer OpenShell.

### Cara kerjanya

ClawMetry mendeteksi NemoClaw dengan dua cara:

1. **Deteksi biner** — memeriksa CLI `nemoclaw` dan menjalankan `nemoclaw status` untuk mendapatkan info sandbox
2. **Deteksi kontainer** — memindai kontainer Docker yang berjalan untuk image `openshell`, `nemoclaw`, atau `ghcr.io/nvidia/`, lalu membaca sesi melalui volume mount atau `docker cp`

File sesi yang disinkronkan dari kontainer NemoClaw ditandai dengan `runtime=nemoclaw` dan metadata `container_id` di dashboard cloud, sehingga Anda dapat membedakannya dari sesi OpenClaw standar sekilas.

### Pengaturan yang direkomendasikan: daemon sinkronisasi pada HOST

Untuk pengalaman terbaik, jalankan daemon sinkronisasi ClawMetry pada **mesin host** (bukan di dalam sandbox). Ini menghindari batasan kebijakan jaringan NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon sinkronisasi akan secara otomatis menemukan sesi di dalam kontainer OpenShell mana pun yang sedang berjalan.

### Opsional: nama sandbox eksplisit

Jika deteksi otomatis tidak berfungsi, arahkan ClawMetry ke sandbox yang tepat:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Menjalankan di dalam sandbox (lanjutan)

Jika Anda harus menjalankan daemon sinkronisasi **di dalam** sandbox OpenShell, tambahkan aturan egress ini ke kebijakan jaringan NemoClaw Anda agar dapat menjangkau API ingest ClawMetry:

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

| Endpoint | Port | Protokol | Diperlukan |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ya (daemon sinkronisasi → cloud) |
| `localhost:8900` | 8900 | HTTP | Ya (UI dashboard lokal) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Untuk penemuan sesi kontainer |

Daemon sinkronisasi hanya melakukan panggilan HTTPS keluar ke `ingest.clawmetry.com`. Tidak ada port masuk yang diperlukan.

---

## Deployment Cloud

Lihat **[Panduan Pengujian Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** untuk tunnel SSH, reverse proxy, dan Docker.

## Pengujian

Proyek ini diuji dengan BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry mengirimkan ping siklus-hidup instalasi anonim ke
`https://app.clawmetry.com/api/install`: satu ping `install` pada saat pertama kali
Anda menjalankan CLI `clawmetry` di mesin baru, satu ping `update`
pada run pertama setelah upgrade ke versi baru, dan satu ping `onboarded`
saat Anda menyelesaikan pilihan onboarding di dalam dashboard. Kami menggunakan ini
untuk menghitung instalasi nyata (angka unduhan PyPI mentah sekitar 98% adalah mirror, CI,
dan unduhan ulang auto-update) dan untuk mempelajari kerangka kerja agen dan
versi mana yang benar-benar digunakan di lapangan.

**Paling banyak satu POST per event siklus-hidup per versi**, berisi:

| Field | Contoh | Alasan |
|---|---|---|
| `install_id` | UUID acak yang disimpan di `~/.clawmetry/install_id` | dedup; anonim hingga Anda secara eksplisit menghubungkan sinkronisasi Cloud (heartbeat daemon terautentikasi kemudian membawanya, menautkan instalasi ini ke akun Anda) |
| `event` | `install` / `update` / `onboarded` | instalasi baru vs upgrade dari yang sudah ada |
| `version` | `0.12.167` | versi apa saja yang digunakan di lapangan |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioritas dukungan platform |
| `python` | `3.11.15` | matriks dukungan versi Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | agen mana yang harus kami integrasikan selanjutnya |
| `is_ci` / `ci_provider` | `true` / `github_actions` | memisahkan instalasi manusia dari noise CI |

**Yang TIDAK kami kirim**: IP (cloud menurunkan kode negara secara server-side
dari permintaan, lalu membuang IP-nya), hostname, username, path workspace,
isi file, api_key Anda, email Anda, apa pun yang bersifat PII atau
spesifik workspace. Payload wire dapat diaudit di
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Opt out** (salah satu dari ini menonaktifkannya secara permanen):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Kegagalan jaringan di sini tidak pernah memblokir `clawmetry` agar tetap berjalan; ping
tersebut bersifat fire-and-forget pada thread daemon dengan timeout 3 detik.

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
