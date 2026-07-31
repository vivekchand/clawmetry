<!-- i18n-src:8252f6b1d31d -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Lihat cara berpikir agen Anda.** Observabilitas real-time untuk **14 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 10 lainnya. Satu dashboard untuk seluruh armada agen Anda.

> 🌐 **Baca dalam bahasa ini:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900** dan Anda selesai.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Bekerja dengan 14 runtime agen

ClawMetry dimulai sebagai alat observabilitas untuk OpenClaw, dan kini mengukur **seluruh armada agen** Anda dalam satu dashboard, mendeteksi setiap runtime di mesin Anda secara otomatis:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw dan NemoClaw gratis di aplikasi open-source; runtime lainnya aktif dengan ClawMetry Cloud atau lisensi Pro yang dihosting sendiri. Ganti runtime dari header dan setiap tab, biaya, token, tools, trace, akan menyesuaikan cakupannya ke runtime tersebut. Lihat **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** untuk pembagian gratis/berbayar yang tepat, matriks tier, bentuk `/api/entitlement`, dan CLI `clawmetry license`.

## Apa yang Anda Dapatkan

- **Flow** — Diagram animasi langsung yang menunjukkan pesan mengalir melalui channel, otak (brain), tools, dan kembali lagi
- **Overview** — Pemeriksaan kesehatan, heatmap aktivitas, jumlah sesi, info model
- **Usage** — Pelacakan token dan biaya dengan rincian harian/mingguan/bulanan
- **Sessions** — Sesi agen aktif dengan model, token, aktivitas terakhir
- **Crons** — Tugas terjadwal dengan status, jalan berikutnya, durasi
- **Logs** — Streaming log real-time dengan kode warna
- **Memory** — Jelajahi SOUL.md, MEMORY.md, AGENTS.md, catatan harian
- **Transcripts** — UI gelembung obrolan untuk membaca riwayat sesi
- **Alerts** — Batas anggaran, pemicu tingkat error, deteksi agen offline; diarahkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Menahan penghapusan destruktif, force push, mutasi DB, sudo, instalasi paket, panggilan jaringan di balik persetujuan satu klik

## Tangkapan Layar

### 🧠 Brain — Aliran event agen secara langsung
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Penggunaan token & ringkasan sesi
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Umpan panggilan tool real-time
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Rincian biaya per model & sesi
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Penjelajah berkas workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postur & log audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Batas anggaran, pemicu tingkat error, webhook ke Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Menahan panggilan tool berisiko di balik persetujuan manual; aturan proteksi berbasis kebijakan
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Pemblokiran pra-eksekusi untuk Claude Code** — satu perintah memasang
hook PreToolUse yang menjeda panggilan tool yang cocok *sebelum* dijalankan dan menunggu
keputusan Anda (satu ketukan dari ponsel Anda dengan
[notifikasi push cloud](https://app.clawmetry.com/push) diaktifkan):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Sebuah deny hanya memblokir satu panggilan tool itu, agen tetap mempertahankan sesinya dan bisa
mencoba pendekatan lain. Menyetujui dari ponsel Anda melewati prompt izin
Claude Code sendiri (Anda sudah menjawabnya). Tool yang tidak cocok hanya memakan waktu ~40ms dan
diteruskan ke alur izin normal Claude Code. Anda juga mendapatkan push ke ponsel saat
Claude Code sendiri sedang menunggu Anda (notifikasi `permission_prompt` /
`idle_prompt`).

## Instalasi

**One-liner (disarankan):**
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

ClawMetry mengamati banyak runtime agen AI, bukan hanya OpenClaw. Setiap runtime selain OpenClaw dilengkapi dengan adapter pembaca khusus yang menerjemahkan format sesi aslinya ke dalam bentuk terpadu ClawMetry; daemon menyerapnya ke dalam DuckDB store + snapshot cloud yang sama, ditandai dengan runtime-nya, dan tab Session replay menampilkan **pengalih runtime** ketika lebih dari satu runtime hadir. Lihat [`docs/compatibility.md`](docs/compatibility.md) untuk matriks lengkap + panduan menambahkan runtime, dan [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) untuk pengantar keluarga OpenClaw.

| Runtime / Agen | Status | Catatan |
|---|---|---|
| **OpenClaw** | Native | Runtime referensi, terdeteksi otomatis |
| **PicoClaw** | Adapter beta | JSONL `providers.Message` datar (`~/.picoclaw/workspace/sessions`). Transcript, model, panggilan tool. |
| **NanoClaw** | Adapter beta | SQLite per-sesi (`data/v2-sessions`). Transcript + jumlah pesan. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transcript, model, token/biaya. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcript, model, panggilan tool + thinking, penggunaan token. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transcript, model, panggilan tool, penggunaan token. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transcript chat/composer, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` per proyek. Transcript, model, jumlah token. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transcript, model, panggilan tool, total token. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transcript, model, panggilan tool, token + biaya. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transcript, model, panggilan tool, penggunaan token. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transcript, model, panggilan tool, token + biaya. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transcript, model, panggilan tool, token + biaya. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Eksekusi workflow, jalannya node, prompt AI Agent, model + token bila dicatat oleh n8n. |

"Adapter beta" berarti ClawMetry menyediakan pembaca untuk format asli di disk milik runtime tersebut, masing-masing dibangun + diverifikasi terhadap instalasi nyata di mesin nyata (lihat `tests/fixtures/runtimes/<rt>/`). Adapter bersifat read-only; masing-masing jujur soal apa yang benar-benar disimpan oleh runtime-nya (misalnya PicoClaw/NanoClaw/Cursor tidak menulis biaya token ke disk). Ketika beberapa runtime berjalan di satu node, pengalih runtime membatasi cakupan tampilan sesi ke satu runtime untuk deep-dive yang bersih.

## Lacak agen SDK apa pun — atribusi biaya out-loop

Runtime di atas semuanya menulis sesi ke disk. Agen **produksi** Anda sendiri, yang Anda bangun di atas OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, atau loop `httpx` biasa, tidak melakukannya. Interceptor tanpa konfigurasi milik ClawMetry tetap menangkap panggilan LLM-nya (biaya, token, latensi, error) dengan melakukan monkey-patching pada `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (atau variabel lingkungan `CLAWMETRY_SOURCE=support-agent`) menandai setiap panggilan dengan **sumber bernama**, sehingga setiap produk yang Anda jalankan muncul sebagai baris tersendiri yang bisa diatribusikan biayanya di kartu **🔌 Out-loop sources** pada Overview dashboard, panggilan, provider, latensi, tingkat error per agen. Belum mengatur sumber? Panggilan tetap dilacak; kartunya saja yang tetap tersembunyi.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ini adalah lapisan data yang sama yang dipasok oleh adapter runtime (DuckDB → snapshot cloud), sehingga sumber out-loop tersinkron ke dashboard cloud sama seperti yang lainnya, dengan enkripsi E2E.

## OpenTelemetry — netral vendor, kirim trace Anda ke mana saja

ClawMetry berbicara dalam **OpenTelemetry** di kedua arah, menggunakan **konvensi semantik GenAI**, sehingga trace agen Anda tidak pernah terkunci pada satu tool saja.

**Ekspor** setiap sesi, panggilan LLM, tools, sub-agen, token, biaya, sebagai span GenAI OTLP/HTTP ke collector mana pun (Datadog, Grafana, Honeycomb, atau OTel Collector Anda sendiri):

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

**Impor** — receiver OTLP bawaan menerima trace dan metrik dari sumber lain di `/v1/traces` dan `/v1/metrics` (`pip install clawmetry[otel]` untuk ingest protobuf).

Anda mendapatkan dashboard ClawMetry yang tanpa konfigurasi, lokal-utama, **sekaligus** data Anda di backend apa pun yang sudah digunakan tim Anda, tanpa penguncian vendor, tanpa perlu memasang agen kedua.

## Konfigurasi

Kebanyakan orang tidak memerlukan konfigurasi apa pun. ClawMetry mendeteksi workspace, log, sesi, dan cron Anda secara otomatis.

Jika Anda memang perlu menyesuaikannya:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Semua opsi: `clawmetry --help`

## Channel yang Didukung

ClawMetry menampilkan aktivitas langsung untuk setiap channel OpenClaw yang Anda konfigurasikan. Hanya channel yang benar-benar disiapkan di `openclaw.json` Anda yang muncul di diagram Flow, yang belum dikonfigurasi otomatis disembunyikan.

Klik node channel mana pun di Flow untuk melihat tampilan gelembung obrolan langsung dengan jumlah pesan masuk/keluar.

| Channel | Status | Popup Langsung | Catatan |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | Pesan, statistik, refresh 10 detik |
| 💬 **iMessage** | ✅ Full | ✅ | Membaca `~/Library/Messages/chat.db` langsung |
| 💚 **WhatsApp** | ✅ Full | ✅ | Melalui WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Full | ✅ | Melalui signal-cli |
| 🟣 **Discord** | ✅ Full | ✅ | Deteksi guild + channel |
| 🟪 **Slack** | ✅ Full | ✅ | Deteksi workspace + channel |
| 🌐 **Webchat** | ✅ Full | ✅ | Sesi UI web bawaan |
| 📡 **IRC** | ✅ Full | ✅ | UI gelembung gaya terminal |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Full | ✅ | Melalui webhook Chat API |
| 🟣 **MS Teams** | ✅ Full | ✅ | Melalui plugin bot Teams |
| 🔷 **Mattermost** | ✅ Full | ✅ | Obrolan tim self-hosted |
| 🟩 **Matrix** | ✅ Full | ✅ | Terdesentralisasi, dukungan E2EE |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | DM NIP-04 terdesentralisasi |
| 🟣 **Twitch** | ✅ Full | ✅ | Chat melalui koneksi IRC |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | Langganan event WebSocket |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **Deteksi otomatis:** ClawMetry membaca `~/.openclaw/openclaw.json` Anda dan hanya menampilkan channel yang benar-benar Anda konfigurasikan. Tidak perlu pengaturan manual.

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

> **Catatan:** Saat berjalan di Docker, pasang direktori data + log agen Anda (misalnya `~/.openclaw`, `~/.claude`, `~/.codex`) agar ClawMetry dapat mendeteksi pengaturan Anda secara otomatis.

## Persyaratan

- Python 3.8+
- Flask (terpasang otomatis melalui pip)
- Runtime agen AI di mesin yang sama: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, atau n8n (atau volume yang dipasang untuk Docker)
- Linux atau macOS

## Dukungan NemoClaw / OpenShell

ClawMetry secara otomatis mendeteksi [NemoClaw](https://github.com/NVIDIA/NemoClaw), pembungkus keamanan tingkat enterprise milik NVIDIA untuk OpenClaw yang menjalankan agen di dalam kontainer OpenShell yang di-sandbox.

Konfigurasi tambahan tidak diperlukan pada sebagian besar kasus. Daemon sinkronisasi secara otomatis menemukan berkas sesi baik yang berada di `~/.openclaw/` pada host maupun di dalam kontainer OpenShell.

### Cara kerjanya

ClawMetry mendeteksi NemoClaw dengan dua cara:

1. **Deteksi biner** — memeriksa CLI `nemoclaw` dan menjalankan `nemoclaw status` untuk mendapatkan informasi sandbox
2. **Deteksi kontainer** — memindai kontainer Docker yang sedang berjalan untuk image `openshell`, `nemoclaw`, atau `ghcr.io/nvidia/`, lalu membaca sesi melalui volume mount atau `docker cp`

Berkas sesi yang disinkronkan dari kontainer NemoClaw ditandai dengan `runtime=nemoclaw` dan metadata `container_id` di dashboard cloud, sehingga Anda bisa membedakannya dari sesi OpenClaw standar sekilas saja.

### Pengaturan yang disarankan: daemon sinkronisasi di HOST

Untuk pengalaman terbaik, jalankan daemon sinkronisasi ClawMetry di **mesin host** (bukan di dalam sandbox). Ini menghindari batasan kebijakan jaringan NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon sinkronisasi akan otomatis menemukan sesi di dalam kontainer OpenShell mana pun yang sedang berjalan.

### Opsional: nama sandbox eksplisit

Jika deteksi otomatis tidak berhasil, arahkan ClawMetry ke sandbox yang tepat:

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

| Endpoint | Port | Protokol | Wajib |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ya (daemon sinkronisasi → cloud) |
| `localhost:8900` | 8900 | HTTP | Ya (UI dashboard lokal) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Untuk penemuan sesi kontainer |

Daemon sinkronisasi hanya melakukan panggilan HTTPS keluar ke `ingest.clawmetry.com`. Tidak ada port masuk yang diperlukan.

---

## Deployment Cloud

Lihat **[Panduan Pengujian Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** untuk SSH tunnel, reverse proxy, dan Docker.

## Pengujian

Proyek ini diuji dengan BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry mengirim ping siklus-hidup instalasi anonim ke
`https://app.clawmetry.com/api/install`: satu ping `install` saat pertama
kali Anda menjalankan CLI `clawmetry` di mesin baru, satu ping `update`
pada jalan pertama setelah meng-upgrade ke versi baru, dan satu ping `onboarded`
saat Anda menyelesaikan pilihan onboarding di dalam dashboard. Kami menggunakan ini
untuk menghitung instalasi nyata (angka unduhan PyPI mentah ~98% adalah mirror, CI,
dan unduhan ulang auto-update) dan untuk mempelajari framework agen serta
versi apa yang benar-benar digunakan di lapangan.

**Maksimal satu POST per event siklus-hidup per versi**, berisi:

| Field | Contoh | Alasan |
|---|---|---|
| `install_id` | UUID acak yang disimpan di `~/.clawmetry/install_id` | dedup; anonim sampai Anda secara eksplisit menghubungkan sinkronisasi Cloud (heartbeat daemon yang terautentikasi kemudian membawanya, menautkan instalasi ini ke akun Anda) |
| `event` | `install` / `update` / `onboarded` | instalasi baru vs upgrade dari yang sudah ada |
| `version` | `0.12.167` | versi apa yang beredar di lapangan |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioritas dukungan platform |
| `python` | `3.11.15` | matriks dukungan versi Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | agen mana yang harus kami integrasikan selanjutnya |
| `is_ci` / `ci_provider` | `true` / `github_actions` | memisahkan instalasi manusia dari noise CI |

**Apa yang TIDAK kami kirim**: IP (cloud menurunkan kode negara di sisi
server dari permintaan, lalu membuang IP-nya), hostname, username, path
workspace, isi berkas, api_key Anda, email Anda, apa pun yang bersifat PII atau
khusus workspace. Payload jalur kabelnya bisa diaudit di
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Opt out** (salah satu dari ini akan menonaktifkannya secara permanen):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Kegagalan jaringan di sini tidak akan pernah menghalangi `clawmetry` untuk berjalan, ping
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
  <strong>🦞 Lihat cara berpikir agen Anda</strong><br>
  <sub>Dibangun oleh <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bagian dari ekosistem <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
