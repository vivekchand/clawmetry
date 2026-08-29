<!-- i18n-src:d21bea5161e0 -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Lihat cara berpikir agen Anda.** Observabilitas real-time untuk **30 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 lainnya. Satu dasbor untuk seluruh armada agen Anda.

> 🌐 **Baca dalam bahasa lain:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900**. Tanpa konfigurasi: aplikasi ini menemukan
runtime agen yang sudah Anda miliki, membacanya secara read-only, dan tidak mengubah apa pun tentang cara kerjanya.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bekerja dengan 30 runtime agen

**Gratis di aplikasi open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Pada paket berbayar:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Setiap runtime mendapatkan dasbor yang sama. Jalankan beberapa sekaligus dan
pengalih di header akan mengubah cakupan setiap tab ke salah satunya.

Membangun agen Anda sendiri dengan sebuah SDK? Interceptor tetap melacak panggilan LLM-nya
juga. Lihat [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Yang Anda dapatkan

- **Sesi & transkrip**: apa yang dilakukan setiap agen, giliran demi giliran, dengan replay
- **Biaya & token**: per runtime, model, sesi dan hari, dengan penanda anomali
- **Flow**: diagram langsung pesan yang bergerak melalui channel, model dan tool
- **Brain**: aliran peristiwa reasoning dan pemanggilan tool saat terjadi
- **Context blowout**: pemanfaatan window yang disesuaikan per penyedia, kompaksi vs overflow paksa, ditambah peta per runtime tentang apa yang *tidak dapat* kami lihat ([caranya](docs/CONTEXT_BLOWOUT.md))
- **Memory & skill**: file dan skill yang benar-benar dimuat setiap runtime
- **Health & log**: disk, memori, tingkat error, rate limit, aliran log langsung
- **Alert**: batas anggaran, lonjakan error, agen offline, diarahkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Approval**: menjeda pemanggilan tool berisiko *sebelum* dijalankan dan menyetujui dari ponsel Anda ([caranya](docs/APPROVALS.md))

## Context blowout, dan biaya pemantauannya

Dua pertanyaan yang layak dijawab sebelum Anda mempercayai alat perbandingan agen mana pun.

**Bagaimana cara alat ini menangani context-window blowout di berbagai runtime?**

Persentase pemanfaatan hanya sejujur apa yang menjadi pembaginya. ClawMetry
menyesuaikan ukuran window per penyedia dari [tabel yang bisa Anda baca dan
ajukan PR](clawmetry/context_windows.py), mencakup Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama dan GLM. Alat ini tidak mengukur ke-26
runtime dengan penggaris satu vendor. Itu penting: satu giliran GPT-5 300K yang
dinilai terhadap 200K milik Anthropic terbaca ">100%, blown" padahal sebenarnya berada
di 75% dari 400K milik GPT-5. Penggaris yang sama menyembunyikan giliran DeepSeek 130K
yang benar-benar overflow sebagai 65% yang terlihat nyaman.

Setiap window dilengkapi asal-usulnya: `model_table`, `explicit_marker`,
`observed_floor`, atau `default` yang jujur ketika kami tidak mengetahui modelnya. Gauge yang dibangun berdasarkan tebakan
tidak pernah tampil dengan otoritas yang sama seperti yang dibangun berdasarkan
pencarian data.

ClawMetry hanya dapat melihat peristiwa kompaksi pada sebagian runtime. Jadi
`GET /api/context-coverage` melaporkan, per runtime, apakah **angka nol berarti
"berjalan bersih" atau "kami buta"**. `0` yang sebenarnya berarti buta akan mengatakannya demikian.
[Detail lengkap](docs/CONTEXT_BLOWOUT.md)

**Berapa biaya instrumentasinya?**

| Jalur | Ditambahkan ke agen Anda | Default? |
|---|---|---|
| Session-file tailing (semua 30 runtime) | **0**. Proses terpisah, tanpa kode ClawMetry di agen Anda | aktif |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per panggilan LLM, atau 0,009% dari panggilan 5 detik | nonaktif |
| Pre-tool hook gate (warm cache) | **+44 ms** per pemanggilan tool yang di-gate, di atas batas dasar interpreter 36 ms | nonaktif |
| Enforcement proxy | **+9,7 ms** per panggilan LLM | nonaktif |

Biaya host daemon: **2.762 peristiwa/detik** ingest, **710 byte/peristiwa** di disk
(67,7 MB per 100 ribu peristiwa), dan **~12% dari satu core** berkelanjutan pada instalasi
yang sibuk. Angka terakhir itu melebihi anggaran 5-10% yang kami tetapkan sendiri, jadi
ini dipublikasikan sebagai bug yang harus dikejar, bukan disembunyikan dari halaman ini.

Diukur pada Apple M2 Pro dengan `benchmarks/overhead.py`. Harness ini menjalankan
setiap kondisi dalam proses terpisah, bergantian urutannya, dan **menolak
mencetak angka ketika hasil beberapa putaran tidak sepakat soal tandanya**. Jalankan di
mesin Anda sendiri dalam satu menit:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Setiap jalur diukur, termasuk hook gate dan enforcement proxy,
dan harness ini berjalan di Linux, macOS dan Windows di CI. Dua hasil yang perlu
diketahui: proxy berbiaya sekitar tujuh kali lebih besar di Windows dibanding di Linux, dan
daemon saat ini bertahan pada sekitar 12% dari satu core, melebihi anggaran 5-10% kami sendiri.
JSON mentah, metodenya, dan apa yang masih belum terukur ada di
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Harga

| Paket | Yang tercakup | Harga |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dasbor lengkap, hanya lokal | $0 |
| **Starter** | Semua runtime lain di atas, tampilan armada, sinkronisasi cloud | $9 per node / bulan |
| **Pro** | Starter + kontrol dan evaluasi: approval, kebijakan risiko tool, eval, deteksi anomali, cost optimizer, ekspor OTel, log audit tamper-evident | $19 per node / bulan |

Paket tahunan, Enterprise dan angka-angka terkini ada di
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Kunci lisensi self-hosted
berfungsi tanpa cloud (`clawmetry license`). Rincian pasti antara gratis/berbayar ada
di [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Data Anda tetap di mesin Anda

ClawMetry membaca file sesi dan log lokal. **Tidak ada data sesi yang keluar dari perangkat Anda
kecuali Anda menjalankan `clawmetry connect`** — tanpa prompt, balasan, argumen tool, isi
file atau baris log. Ketika Anda memang menghubungkan, snapshot dienkripsi end-to-end
dengan kunci yang tidak pernah meninggalkan mesin Anda, dan didekripsi di browser Anda. Jika
sebuah node tidak memiliki kunci, unggahan dilewati alih-alih dikirim dalam bentuk tidak terenkripsi, dan tidak ada
respons server yang bisa mematikan itu.

Dua hal tetap berjalan secara default sebelum Anda terhubung, keduanya opt-out dan tidak
membawa data sesi: ping instalasi anonim dan pemeriksaan versi terhadap
PyPI. Instalasi default juga mencari alamat IP publik Anda sekali untuk baris banner
saat startup. Setiap tujuan, apa yang dibawanya dan cara mematikannya tercantum di
[docs/EGRESS.md](docs/EGRESS.md); instalasi self-hosted, yang dialihkan, dan air-gapped
tidak melakukan panggilan keluar diskresioner sama sekali.

Proses dekripsi terjadi di browser Anda, dalam kode yang kami sajikan untuk Anda. Itu dulunya
sekadar janji; sekarang menjadi sesuatu yang bisa Anda periksa. Setiap baris yang menyentuh kunci Anda
berada dalam satu file yang bisa dibaca, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
yang dikirim di dalam wheel dan disajikan apa adanya, dipatok dengan hash Subresource
Integrity. Untuk memastikan browser menjalankan apa yang kami terbitkan:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Yang tidak dibuktikan oleh itu: kami yang menyajikan halaman yang memuat file tersebut, jadi kami bisa saja
menyajikan halaman yang berbeda. Hash integritas melindungi Anda dari CDN yang disusupi,
bukan dari vendor. Yang Anda peroleh adalah bahwa penggantian apa pun harus
disengaja, terlihat di sumber halaman, dan berbeda dari artefak di PyPI
yang bisa diambil siapa saja. Melakukan self-hosting atau tetap lokal-saja menghilangkan
ketergantungan itu sepenuhnya.

## Instalasi

```bash
pip install clawmetry     # lalu: clawmetry
```

Atau perintah satu baris: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Membutuhkan Python 3.8+ di macOS, Linux atau Windows, dan setidaknya satu runtime agen di
mesin yang sama. Instruksi Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentasi

| | |
|---|---|
| [Kompatibilitas runtime](docs/compatibility.md) | Apa yang dibaca setiap adapter, dan cara menambahkan runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Window per penyedia, kompaksi vs overflow, cakupan per runtime |
| [Overhead](docs/OVERHEAD.md) | Biaya instrumentasi, terukur, dengan harness untuk mereproduksinya |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis vs berbayar, matriks tier, license CLI |
| [Approval & kebijakan](docs/APPROVALS.md) | Gating pra-eksekusi, penilaian risiko, approval via ponsel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Ekspor trace ke mana saja, ingest OTLP dari apa saja |
| [Pelacakan SDK](docs/SDK_TRACKING.md) | Atribusi biaya untuk agen yang Anda bangun sendiri |
| [Channel chat](docs/CHANNELS.md) | Adapter chat yang ditampilkan di Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Setup NVIDIA NemoClaw yang di-sandbox |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Arsitektur](ARCHITECTURE.md) · [Pengembangan](docs/DEVELOPMENT.md) | Cara kerjanya di dalam; menjalankan dari source |
| [Telemetri](docs/TELEMETRY.md) | Ping instalasi anonim dan pembukaan desktop, dan cara mematikannya |

## Tangkapan layar

Setiap angka di bawah ini berasal dari satu mesin sungguhan, read-only, tanpa apa pun yang di-seed.

**Aplikasi ini memberi tahu Anda ketika ada yang salah, bukan sekadar apa yang terjadi.**
Dua banner anomali di bagian atas: pengeluaran berjalan 7x rata-rata harian, dan
lonjakan biaya 4,2x. Di bawahnya, 324 dari 667 sesi terbaru membawa sinyal
pemborosan, dirinci berdasarkan penyebabnya.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Aplikasi ini menunjukkan ke mana uang mengalir, di setiap jendela waktu.**
$252,47 hari ini, $513,15 minggu ini, $1.312,92 bulan ini, masing-masing dengan token
di baliknya dan berapa banyak yang sudah tercakup langganan Anda. Di bawahnya, sekitar
$1.128/bulan dirinci sebagai dapat dipulihkan dan $17.256/bulan sudah dihemat oleh
penggunaan ulang cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Aplikasi ini menggambarkan bagaimana sebuah pesan menjadi jawaban.**
Diagram flow langsung: Anda, channel tempat pesan tiba, gateway, model yang
sedang menjawab saat ini, dan setiap tool yang dipakainya. Node menyala saat pekerjaan
bergerak melalui mereka.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Setiap agen di mesin, dalam satu tabel.**
Apa yang dijalankannya, berapa biayanya dalam 24 jam terakhir dan sepanjang masa hidupnya, kapan
terakhir terlihat, siapa pemiliknya, dan apakah langganan menutupi
tagihannya. 14 agen di sini, 3 sesi sedang bekerja, 13 diam.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Aplikasi ini menunjukkan ke mana waktu dan uang sebuah giliran mengalir, tool demi tool.**
Satu giliran dari sesi sungguhan: 11 tool dalam 11,2 menit seharga $1,16. Setiap
panggilan Bash dan panggilan model mendapatkan batangnya sendiri di timeline, sehingga perintah yang berjalan
selama 4,1 menit dan yang berjalan selama 226ms bisa dibedakan sekilas mata.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Aplikasi ini menilai pekerjaannya, bukan sekadar pengeluarannya.**
Nilai A minggu ini: 54 tugas selesai dengan bersih, 2 yang bermasalah berbiaya $48,57, dan
proses yang aktivitasnya terlalu sedikit untuk dinilai dikeluarkan dari penilaian alih-alih
dihitung sebagai keberhasilan. Setiap proses bermasalah ditautkan ke trace-nya.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Aplikasi ini menunjukkan mengapa context window terus terisi.**
715K dari window 1M token pada giliran terbaru, puncak 83,3%, 4 kompaksi
yang semuanya terpicu secara proaktif alih-alih karena overflow, ditambah utilisasi
setiap giliran di baliknya.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Deteksi berjalan tanpa Anda perlu mengonfigurasi apa pun.**
Detektor bawaan aktif sejak instalasi: agen menjadi diam, feed telemetri
berhenti, lonjakan biaya, lonjakan token, error meningkat, lonjakan error, ambang
anggaran, tanda tangan ancaman cocok, temuan tool keamanan, postur keamanan
berubah. Aturan Anda sendiri bersifat opsional di atasnya.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Menahan panggilan berisiko bersifat opt-in, dan dikirimkan dalam keadaan nonaktif.**
Recursive delete, force push, sudo, secret, instalasi paket dan panggilan keluar
masing-masing mendapatkan aturan yang bisa Anda aktifkan. Sampai Anda melakukannya, ClawMetry mengamati dan
tidak mengubah apa pun. Setelah salah satunya aktif, panggilan yang cocok menunggu di sini (atau di ponsel Anda)
untuk disetujui atau ditolak.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Lebih lanjut, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lisensi

MIT · Dibuat oleh [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
