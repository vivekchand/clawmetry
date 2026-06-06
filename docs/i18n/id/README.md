<!-- i18n-src:48548997be76 -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Lihat agen Anda berpikir.** Observabilitas real-time untuk **12 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 8 lainnya. Satu dasbor untuk seluruh armada agen Anda.

> 🌐 **Baca dalam bahasa:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi segalanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900** dan selesai.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Kompatibel dengan 12 runtime agen

ClawMetry awalnya dibuat sebagai observabilitas untuk OpenClaw, dan kini mengukur **seluruh armada agen Anda** dalam satu dasbor, mendeteksi setiap runtime di mesin Anda secara otomatis:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw dan NemoClaw tersedia gratis di aplikasi sumber terbuka; runtime lainnya aktif dengan ClawMetry Cloud atau lisensi Pro yang di-host sendiri. Ganti runtime dari header dan setiap tab — biaya, token, alat, trace — akan disesuaikan dengan runtime tersebut.

## Apa yang Anda Dapatkan

- **Flow** — Diagram animasi langsung yang menampilkan pesan mengalir melalui saluran, otak, alat, dan kembali lagi
- **Overview** — Pemeriksaan kesehatan, peta panas aktivitas, jumlah sesi, info model
- **Usage** — Pelacakan token dan biaya dengan rincian harian/mingguan/bulanan
- **Sessions** — Sesi agen aktif beserta model, token, dan aktivitas terakhir
- **Crons** — Pekerjaan terjadwal dengan status, jadwal berikutnya, durasi
- **Logs** — Streaming log real-time dengan kode warna
- **Memory** — Telusuri SOUL.md, MEMORY.md, AGENTS.md, catatan harian
- **Transcripts** — Antarmuka gelembung obrolan untuk membaca riwayat sesi
- **Alerts** — Batas anggaran, pemicu tingkat kesalahan, deteksi agen offline; dikirim ke Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Kunci penghapusan berbahaya, force push, mutasi DB, sudo, instalasi paket, panggilan jaringan di balik persetujuan satu klik

## Tangkapan Layar

### 🧠 Brain — Aliran peristiwa agen langsung
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Penggunaan token & ringkasan sesi
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Umpan panggilan alat real-time
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Rincian biaya per model & sesi
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Penjelajah file ruang kerja
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postur & log audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Batas anggaran, pemicu tingkat kesalahan, webhook ke Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Kunci panggilan alat berisiko di balik persetujuan manual; aturan perlindungan berbasis kebijakan
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalasi

**Satu perintah (direkomendasikan):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Dari sumber:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Pengembangan Frontend v2

Aplikasi React v2 berada di `frontend/` dan disajikan di `/v2` ketika server Flask dijalankan dengan v2 diaktifkan.

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

Buka `http://localhost:5173/v2/`. Vite mem-proxy permintaan `/api` ke `http://localhost:8900`, sehingga aplikasi React dapat berkomunikasi dengan server Flask lokal tanpa pengaturan CORS tambahan.

Untuk membangun bundel yang disertakan dalam paket Python:

```bash
cd frontend
npm run build
```

Bundel produksi ditulis ke `clawmetry/static/v2/dist/`.

## Kompatibilitas Runtime / Agen

ClawMetry mengamati banyak runtime agen AI, tidak hanya OpenClaw. Setiap runtime non-OpenClaw dilengkapi adaptor pembaca khusus yang menerjemahkan format sesi aslinya ke dalam bentuk terpadu ClawMetry; daemon mengolahnya ke dalam penyimpanan DuckDB yang sama beserta snapshot cloud, ditandai dengan runtime, dan tab pemutaran ulang Sesi menampilkan **pemilih runtime** ketika lebih dari satu runtime tersedia. Lihat [`docs/compatibility.md`](docs/compatibility.md) untuk matriks lengkap dan panduan menambahkan runtime, serta [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) untuk panduan keluarga OpenClaw.

| Runtime / Agen | Status | Catatan |
|---|---|---|
| **OpenClaw** | Native | Runtime referensi, terdeteksi otomatis |
| **PicoClaw** | Adaptor Beta | JSONL `providers.Message` datar (`~/.picoclaw/workspace/sessions`). Transkrip, model, panggilan alat. |
| **NanoClaw** | Adaptor Beta | SQLite per sesi (`data/v2-sessions`). Transkrip + jumlah pesan. |
| **Hermes** | Adaptor Beta | SQLite `~/.hermes/state.db`. Transkrip, model, token/biaya. |
| **Claude Code** | Adaptor Beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrip, model, panggilan alat + pemikiran, penggunaan token. |
| **Codex** | Adaptor Beta | JSONL rollout `~/.codex/sessions/...`. Transkrip, model, panggilan alat, penggunaan token. |
| **Cursor** | Adaptor Beta | SQLite `state.vscdb`. Transkrip obrolan/komposer, model. |
| **Aider** | Adaptor Beta | `.aider.chat.history.md` per proyek. Transkrip, model, jumlah token. |
| **Goose** | Adaptor Beta | SQLite `~/.local/share/goose`. Transkrip, model, panggilan alat, total token. |
| **opencode** | Adaptor Beta | SQLite `~/.local/share/opencode`. Transkrip, model, panggilan alat, token + biaya. |
| **Qwen Code** | Adaptor Beta | JSONL `~/.qwen/projects/.../chats`. Transkrip, model, panggilan alat, penggunaan token. |

"Adaptor Beta" berarti ClawMetry menyertakan pembaca untuk format on-disk runtime tersebut, masing-masing dibangun dan diverifikasi terhadap instalasi nyata di mesin nyata (lihat `tests/fixtures/runtimes/<rt>/`). Adaptor bersifat hanya-baca; setiap adaptor jujur tentang apa yang sebenarnya disimpan oleh runtime-nya (misalnya PicoClaw/NanoClaw/Cursor tidak menulis biaya token ke disk). Ketika beberapa runtime berjalan di satu node, pemilih runtime membatasi tampilan sesi ke satu runtime untuk penyelidikan mendalam yang lebih bersih.

## Lacak agen SDK apa pun — atribusi biaya di luar loop

Runtime di atas semuanya menulis sesi ke disk. **Agen produksi Anda sendiri** — yang Anda bangun di OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, atau loop `httpx` biasa — tidak melakukannya. Interceptor tanpa konfigurasi ClawMetry tetap menangkap panggilan LLM-nya (biaya, token, latensi, kesalahan) dengan cara monkey-patching `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (atau variabel lingkungan `CLAWMETRY_SOURCE=support-agent`) menandai setiap panggilan dengan **sumber bernama**, sehingga setiap produk yang Anda jalankan muncul sebagai baris tersendiri yang dapat diatribusikan biayanya di kartu **🔌 Sumber out-loop** pada Overview — panggilan, penyedia, latensi, tingkat kesalahan per agen. Tidak ada sumber yang disetel? Panggilan tetap dilacak; kartu hanya tidak ditampilkan.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Ini adalah lapisan data yang sama yang digunakan adaptor runtime (DuckDB ke snapshot cloud), sehingga sumber out-loop tersinkronisasi ke dasbor cloud sama seperti yang lainnya, dienkripsi end-to-end.

## OpenTelemetry — netral vendor, kirim trace ke mana saja

ClawMetry mendukung **OpenTelemetry** di kedua arah, menggunakan **konvensi semantik GenAI**, sehingga trace agen Anda tidak pernah terkunci pada satu alat.

**Ekspor** setiap sesi — panggilan LLM, alat, sub-agen, token, biaya — sebagai span GenAI OTLP/HTTP ke kolektor mana pun (Datadog, Grafana, Honeycomb, atau OTel Collector Anda sendiri):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Header auth dan interval polling adalah variabel lingkungan opsional:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Terima** — penerima OTLP bawaan menerima trace dan metrik dari sumber lain di `/v1/traces` dan `/v1/metrics` (`pip install clawmetry[otel]` untuk penerimaan protobuf).

Anda mendapatkan dasbor ClawMetry tanpa konfigurasi yang mengutamakan lokal **dan** data Anda di backend apa pun yang sudah digunakan tim Anda — tanpa keterikatan vendor, tanpa agen kedua yang harus diinstal.

## Konfigurasi

Kebanyakan pengguna tidak memerlukan konfigurasi apa pun. ClawMetry mendeteksi ruang kerja, log, sesi, dan cron Anda secara otomatis.

Jika Anda perlu menyesuaikan:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Semua opsi: `clawmetry --help`

## Saluran yang Didukung

ClawMetry menampilkan aktivitas langsung untuk setiap saluran OpenClaw yang telah Anda konfigurasi. Hanya saluran yang benar-benar diatur dalam `openclaw.json` Anda yang muncul di diagram Flow — saluran yang tidak dikonfigurasi disembunyikan secara otomatis.

Klik node saluran mana pun di Flow untuk melihat tampilan gelembung obrolan langsung dengan jumlah pesan masuk/keluar.

| Saluran | Status | Popup Langsung | Catatan |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Penuh | ✅ | Pesan, statistik, refresh 10 detik |
| 💬 **iMessage** | ✅ Penuh | ✅ | Membaca `~/Library/Messages/chat.db` langsung |
| 💚 **WhatsApp** | ✅ Penuh | ✅ | Melalui WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Penuh | ✅ | Melalui signal-cli |
| 🟣 **Discord** | ✅ Penuh | ✅ | Deteksi guild + saluran |
| 🟪 **Slack** | ✅ Penuh | ✅ | Deteksi workspace + saluran |
| 🌐 **Webchat** | ✅ Penuh | ✅ | Sesi UI web bawaan |
| 📡 **IRC** | ✅ Penuh | ✅ | Antarmuka gelembung bergaya terminal |
| 🍏 **BlueBubbles** | ✅ Penuh | ✅ | iMessage melalui BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Penuh | ✅ | Melalui webhook Chat API |
| 🟣 **MS Teams** | ✅ Penuh | ✅ | Melalui plugin bot Teams |
| 🔷 **Mattermost** | ✅ Penuh | ✅ | Obrolan tim yang di-host sendiri |
| 🟩 **Matrix** | ✅ Penuh | ✅ | Terdesentralisasi, dukungan E2EE |
| 🟢 **LINE** | ✅ Penuh | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Penuh | ✅ | DM NIP-04 terdesentralisasi |
| 🟣 **Twitch** | ✅ Penuh | ✅ | Obrolan melalui koneksi IRC |
| 🔷 **Feishu/Lark** | ✅ Penuh | ✅ | Langganan peristiwa WebSocket |
| 🔵 **Zalo** | ✅ Penuh | ✅ | Zalo Bot API |

> **Deteksi otomatis:** ClawMetry membaca `~/.openclaw/openclaw.json` Anda dan hanya merender saluran yang benar-benar telah Anda konfigurasi. Tidak diperlukan pengaturan manual.

## Penerapan Docker

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

> **Catatan:** Saat menjalankan di Docker, pasang direktori data + log agen Anda (misalnya `~/.openclaw`, `~/.claude`, `~/.codex`) agar ClawMetry dapat mendeteksi pengaturan Anda secara otomatis.

## Persyaratan

- Python 3.8+
- Flask (terinstal otomatis melalui pip)
- Runtime agen AI di mesin yang sama: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, atau PicoClaw (atau volume yang di-mount untuk Docker)
- Linux atau macOS

## Dukungan NemoClaw / OpenShell

ClawMetry secara otomatis mendeteksi [NemoClaw](https://github.com/NVIDIA/NemoClaw) — pembungkus keamanan enterprise NVIDIA untuk OpenClaw yang menjalankan agen di dalam kontainer OpenShell yang di-sandbox.

Dalam kebanyakan kasus, tidak diperlukan konfigurasi tambahan. Daemon sinkronisasi secara otomatis menemukan file sesi baik yang berada di `~/.openclaw/` pada host maupun di dalam kontainer OpenShell.

### Cara kerjanya

ClawMetry mendeteksi NemoClaw dengan dua cara:

1. **Deteksi biner** — memeriksa CLI `nemoclaw` dan menjalankan `nemoclaw status` untuk mendapatkan info sandbox
2. **Deteksi kontainer** — memindai kontainer Docker yang berjalan untuk citra `openshell`, `nemoclaw`, atau `ghcr.io/nvidia/`, lalu membaca sesi melalui mount volume atau `docker cp`

File sesi yang disinkronkan dari kontainer NemoClaw ditandai dengan metadata `runtime=nemoclaw` dan `container_id` di dasbor cloud, sehingga Anda dapat membedakannya dari sesi OpenClaw standar sekilas.

### Pengaturan yang direkomendasikan: daemon sinkronisasi di HOST

Untuk pengalaman terbaik, jalankan daemon sinkronisasi ClawMetry di **mesin host** (bukan di dalam sandbox). Ini menghindari pembatasan kebijakan jaringan NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon sinkronisasi akan secara otomatis menemukan sesi di dalam kontainer OpenShell yang berjalan.

### Opsional: nama sandbox eksplisit

Jika deteksi otomatis tidak berhasil, arahkan ClawMetry ke sandbox yang tepat:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Menjalankan di dalam sandbox (lanjutan)

Jika Anda harus menjalankan daemon sinkronisasi **di dalam** sandbox OpenShell, tambahkan aturan egress ini ke kebijakan jaringan NemoClaw agar dapat menjangkau API ingest ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Ya (daemon sinkronisasi ke cloud) |
| `localhost:8900` | 8900 | HTTP | Ya (UI dasbor lokal) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Untuk penemuan sesi kontainer |

Daemon sinkronisasi hanya melakukan panggilan HTTPS keluar ke `ingest.clawmetry.com`. Tidak diperlukan port masuk.

---

## Penerapan Cloud

Lihat **[Panduan Pengujian Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** untuk tunnel SSH, reverse proxy, dan Docker.

## Pengujian

Proyek ini diuji dengan BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry mengirimkan satu ping anonim "pertama kali dijalankan" ke `https://app.clawmetry.com/api/install` saat pertama kali Anda menjalankan CLI `clawmetry` di mesin baru. Kami menggunakannya untuk menghitung instalasi (satu-satunya metrik pemasaran yang kami miliki untuk proyek OSS) dan untuk mengetahui framework agen mana yang diinstal pengguna kami.

**Tepat satu POST per instalasi**, berisi:

| Kolom | Contoh | Alasan |
|---|---|---|
| `install_id` | UUID acak yang disimpan di `~/.clawmetry/install_id` | deduplikasi; tidak terhubung ke email atau api_key Anda |
| `version` | `0.12.167` | versi apa yang beredar |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioritas dukungan platform |
| `python` | `3.11.15` | matriks dukungan versi Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | agen mana yang harus kami integrasikan berikutnya |
| `is_ci` / `ci_provider` | `true` / `github_actions` | memisahkan instalasi manusia dari noise CI |

**Yang TIDAK kami kirim**: IP (cloud mengambil kode negara di sisi server dari permintaan, lalu membuang IP), nama host, nama pengguna, jalur ruang kerja, isi file, api_key Anda, email Anda, apa pun yang bersifat PII atau spesifik ruang kerja. Muatan jaringan dapat diaudit di [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Nonaktifkan** (salah satu dari ini menonaktifkannya secara permanen):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Kegagalan jaringan di sini tidak pernah memblokir `clawmetry` agar tidak berjalan — ping bersifat fire-and-forget pada thread daemon dengan batas waktu 3 detik.

## Riwayat Bintang

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
  <sub>Dibangun oleh <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Bagian dari ekosistem <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
