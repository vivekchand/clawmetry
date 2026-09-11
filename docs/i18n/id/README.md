<!-- i18n-src:12b97259721e -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Sebuah agent bisa melakukan ratusan tool call tanpa membuat kemajuan.** ClawMetry
membaca file sesi yang sudah ditulis oleh coding agent Anda, dan menyatukan linimasa,
tool call, serta data token dan biaya apa pun yang diekspos oleh runtime ke dalam satu
tampilan — sehingga Anda bisa membedakan proses panjang yang sedang berjalan baik dari yang macet.

Bekerja dengan **31 AI agent runtime** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 27 lainnya. Satu dashboard untuk seluruh armada agent Anda. ([daftar lengkap](SUPPORTED_RUNTIMES.txt), dihasilkan dari katalog.)

> 🌐 **Baca dalam bahasa lain:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900**. Tanpa konfigurasi: ia menemukan agent runtime
yang sudah Anda miliki, membacanya secara read-only, dan tidak mengubah apa pun dari cara kerjanya.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Sebelum Anda memasang

| | |
|---|---|
| **Apa yang dilakukannya** | Membaca file sesi dan log yang sudah ditulis oleh agent Anda. Tanpa SDK, tanpa perubahan kode, tanpa instrumentasi di aplikasi Anda. |
| **Apa yang Anda lihat** | Linimasa sesi, pemutaran ulang per tool, rincian token dan biaya, serta sinyal trajektori (looping, kegagalan berulang) — per runtime. |
| **Apa yang gratis** | `pip install clawmetry` membaca **OpenClaw, NVIDIA NemoClaw, dan Goose** tanpa akun, tanpa key, dan tanpa panggilan jaringan. 27 lainnya — Claude Code, Codex, Cursor, dan sisanya — dibaca oleh pendamping closed-source `clawmetry-pro`, yang hadir bersama uji coba 7 hari atau sebuah paket — lihat [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) untuk rincian pembagiannya secara pasti. |
| **Cara memulai** | `pip install clawmetry && clawmetry`, lalu buka localhost:8900. Belum ada agent di mesin ini? `clawmetry --sample` akan terbuka dengan tiga sesi sintetis berlabel. |
| **Apa yang keluar dari mesin Anda** | Tidak ada data sesi, kecuali Anda menjalankan `clawmetry connect`. Dua hal yang berjalan secara default, keduanya opt-out dan tidak membawa konten sesi: ping instalasi anonim dan pemeriksaan versi PyPI. Setiap tujuan diinventarisasi di [docs/EGRESS.md](docs/EGRESS.md), disusun ulang dari hasil penangkapan lalu lintas jaringan, bukan dari membaca komentar kode. |

Ada dua batasan yang perlu diketahui sebelum Anda menilai hasilnya: runtime mengekspos
data yang sangat berbeda (sebagian tidak mempublikasikan biaya sama sekali —
[matriksnya](docs/compatibility.md) menunjukkan yang mana, per runtime), dan mengamati
suatu tindakan tidak sama dengan mampu memblokirnya ([kontrol mana yang nyata, per runtime](docs/APPROVALS.md)).


## Bekerja dengan 31 agent runtime

**Gratis di aplikasi open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Pada paket berbayar:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Setiap runtime mendapatkan dashboard yang sama. Jalankan beberapa sekaligus dan
pengalih di header akan menyesuaikan ulang setiap tab ke salah satunya.

Membangun agent Anda sendiri di atas sebuah SDK? Interceptor juga melacak panggilan
LLM-nya. Lihat [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Apa yang Anda dapatkan

- **Sesi & transkrip**: apa yang dilakukan setiap agent, giliran demi giliran, dengan pemutaran ulang
- **Biaya & token**: per runtime, model, sesi, dan hari, dengan penanda anomali
- **Flow**: diagram langsung pesan yang bergerak melalui channel, model, dan tool
- **Brain**: aliran event penalaran dan tool call saat terjadi
- **Ledakan konteks (context blowout)**: pemanfaatan window yang diukur per provider, kompaksi vs overflow paksa, plus peta per-runtime tentang apa yang *tidak bisa* kita lihat ([caranya](docs/CONTEXT_BLOWOUT.md))
- **Memori & skill**: file dan skill yang sebenarnya dimuat oleh setiap runtime
- **Kesehatan & log**: disk, memori, tingkat error, rate limit, aliran log langsung
- **Alert**: batas anggaran, lonjakan error, agent offline, diarahkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Persetujuan (Approvals)**: menjeda tool call berisiko *sebelum* dijalankan dan menyetujuinya dari ponsel Anda ([caranya](docs/APPROVALS.md))

## Ledakan konteks, dan biaya pemantauannya

Dua pertanyaan yang layak dijawab sebelum Anda mempercayai alat pembanding agent mana pun.

**Bagaimana cara menanganinya untuk ledakan context window di berbagai runtime?**

Persentase pemanfaatan hanya sejujur pembaginya. ClawMetry mengukur ukuran
window per provider dari [sebuah tabel yang bisa Anda baca dan
ajukan PR-nya](clawmetry/context_windows.py), mencakup Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama, dan GLM. Ia tidak mengukur ke-31
runtime dengan penggaris satu vendor saja. Ini penting: giliran 300K GPT-5 yang
dinilai memakai standar 200K milik Anthropic terbaca ">100%, meledak" padahal
sebenarnya berada di 75% dari 400K milik GPT-5. Penggaris yang sama menyembunyikan
giliran DeepSeek 130K yang sungguh-sungguh overflow sebagai angka nyaman 65%.

Setiap window dikirim dengan asal-usulnya (provenance): `model_table`, `explicit_marker`,
`observed_floor`, atau `default` yang jujur ketika kita tidak tahu modelnya. Meteran
yang dibangun di atas tebakan tidak pernah tampil dengan otoritas yang sama seperti
yang dibangun di atas pencarian data.

ClawMetry hanya bisa melihat event kompaksi pada sebagian runtime. Jadi
`GET /api/context-coverage` melaporkan, per runtime, apakah angka nol berarti
**"berjalan bersih" atau "kita buta"**. Sebuah `0` yang sebenarnya berarti buta akan
mengatakannya demikian. [Detail lengkap](docs/CONTEXT_BLOWOUT.md)

**Berapa biaya instrumentasinya?**

| Jalur | Ditambahkan ke agent Anda | Default? |
|---|---|---|
| Tailing file sesi (semua 31 runtime) | **0**. Proses terpisah, tanpa kode ClawMetry di agent Anda | aktif |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 md** per panggilan LLM, atau 0,009% dari panggilan 5 detik | nonaktif |
| Gerbang hook pre-tool (cache hangat) | **+44 md** per tool call yang digerbangi, di atas lantai interpreter 36 md | nonaktif |
| Proxy penegakan (enforcement proxy) | **+9,7 md** per panggilan LLM | nonaktif |

Biaya host daemon: **2.762 event/detik** ingest, **710 byte/event** di disk
(67,7 MB per 100 ribu event), dan **~12% dari satu core** secara berkelanjutan pada
instalasi yang sibuk. Angka terakhir itu melebihi anggaran 5-10% yang kami tetapkan
sendiri, sehingga dipublikasikan sebagai bug yang perlu dikejar, bukan disembunyikan dari halaman ini.

Diukur pada Apple M2 Pro dengan `benchmarks/overhead.py`. Harness menjalankan
setiap kondisi dalam proses terpisah, mengganti-ganti urutannya, dan **menolak
mencetak angka jika ronde-ronde tersebut tidak sepakat pada tandanya**. Jalankan
di mesin Anda sendiri dalam satu menit:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Setiap jalur diukur, termasuk gerbang hook dan proxy penegakan, dan harness
berjalan di Linux, macOS, dan Windows di CI. Dua hasil yang layak diketahui:
proxy berbiaya sekitar tujuh kali lebih mahal di Windows dibanding Linux, dan
daemon saat ini bertahan pada sekitar 12% dari satu core, melebihi anggaran 5-10%
milik kami sendiri. JSON mentah, metodenya, dan apa yang masih belum terukur
ada di [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Harga

| Paket | Cakupan | Harga |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard lengkap, hanya lokal | $0 |
| **Starter** | Semua runtime lain di atas, tampilan armada, sinkronisasi cloud | $9 per node / bulan |
| **Pro** | Starter + kontrol dan evaluasi: persetujuan, kebijakan risiko tool, evaluasi, deteksi anomali, pengoptimal biaya, ekspor OTel, log audit tahan-rusak (tamper-evident) | $19 per node / bulan |

Paket tahunan, Enterprise, dan angka terkini ada di
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Key lisensi self-hosted
bekerja tanpa cloud (`clawmetry license`). Pembagian gratis/berbayar yang pasti ada di
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Data Anda tetap berada di mesin Anda

ClawMetry membaca file sesi dan log lokal. **Tidak ada data sesi yang keluar dari
mesin Anda kecuali Anda menjalankan `clawmetry connect`** — tanpa prompt, balasan,
argumen tool, isi file, atau baris log. Ketika Anda terhubung, snapshot dienkripsi
end-to-end dengan key yang tidak pernah meninggalkan mesin Anda, dan didekripsi di
browser Anda. Jika sebuah node tidak memiliki key, unggahan dilewati alih-alih
dikirim dalam bentuk polos, dan tidak ada respons server yang dapat mematikan itu.

Dua hal berjalan secara default sebelum Anda terhubung, keduanya opt-out dan
tidak membawa data sesi: ping instalasi anonim dan pemeriksaan versi terhadap
PyPI. Instalasi default juga mencari IP publik Anda sekali untuk baris banner
saat startup. Setiap tujuan, apa yang dibawanya, dan cara mematikannya tercantum
di [docs/EGRESS.md](docs/EGRESS.md); instalasi self-hosted, yang dialihkan ulang,
dan yang air-gapped tidak melakukan panggilan keluar diskresioner sama sekali.

Dekripsi terjadi di browser Anda, dalam kode yang kami kirimkan kepada Anda. Dulu
itu hanyalah janji; sekarang itu sesuatu yang bisa Anda periksa. Setiap baris yang
menyentuh key Anda berada dalam satu file yang bisa dibaca,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
yang dikirim di dalam wheel dan disajikan apa adanya (verbatim), dipatok dengan
hash Subresource Integrity. Untuk memastikan browser menjalankan apa yang kami publikasikan:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Apa yang tidak dibuktikan oleh itu: kami menyajikan halaman yang memuat file
tersebut, jadi kami bisa saja menyajikan halaman yang berbeda. Hash integritas
melindungi Anda dari CDN yang disusupi, bukan dari vendor itu sendiri. Yang Anda
peroleh adalah bahwa setiap penggantian harus disengaja, terlihat di sumber
halaman, dan berbeda dari artefak di PyPI yang bisa diambil siapa saja. Melakukan
self-hosting atau tetap hanya-lokal menghilangkan ketergantungan ini sepenuhnya.

## Instalasi

```bash
pip install clawmetry     # lalu: clawmetry
```

Atau perintah satu baris: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Membutuhkan Python 3.8+ di macOS, Linux, atau Windows, dan setidaknya satu agent
runtime di mesin yang sama. Petunjuk Docker: [docs/DOCKER.md](docs/DOCKER.md).

Atau biarkan agent yang menyiapkannya untuk Anda. Skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
mengajarkan Claude Code, Codex, Cursor, Gemini CLI, Copilot, atau OpenCode untuk
memasang ClawMetry, melaporkan apa yang sedang dilakukan dan dihabiskan oleh agent
di mesin tersebut, menghentikan satu sesi atas permintaan, dan menahan tool call
berisiko untuk persetujuan:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentasi

| | |
|---|---|
| [Kompatibilitas runtime](docs/compatibility.md) | Apa yang dibaca setiap adapter, dan cara menambahkan runtime |
| [Ledakan konteks](docs/CONTEXT_BLOWOUT.md) | Window per provider, kompaksi vs overflow, cakupan per-runtime |
| [Overhead](docs/OVERHEAD.md) | Biaya instrumentasi, terukur, dengan harness untuk mereproduksinya |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis vs berbayar, matriks tier, CLI lisensi |
| [Persetujuan & kebijakan](docs/APPROVALS.md) | Gating pra-eksekusi, penilaian risiko, persetujuan dari ponsel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Ekspor trace ke mana saja, ingest OTLP dari apa saja |
| [Bawa agent Anda sendiri](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain dari ujung ke ujung, dengan contoh yang bisa dijalankan |
| [Pelacakan SDK](docs/SDK_TRACKING.md) | Atribusi biaya untuk agent yang Anda bangun sendiri |
| [Channel obrolan](docs/CHANNELS.md) | Adapter chat yang ditampilkan di Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Penyiapan NVIDIA NemoClaw yang disandbox |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Arsitektur](ARCHITECTURE.md) · [Pengembangan](docs/DEVELOPMENT.md) | Cara kerjanya di dalam; menjalankan dari sumber |
| [Telemetri](docs/TELEMETRY.md) | Ping instalasi anonim dan pembukaan desktop, serta cara mematikannya |

## Tangkapan layar

Setiap angka di bawah ini berasal dari satu mesin nyata, read-only, tanpa ada yang direkayasa.

**Ia memberi tahu Anda saat sesuatu salah, bukan hanya apa yang terjadi.**
Dua banner anomali di bagian atas: pengeluaran berjalan 7x rata-rata harian, dan
lonjakan biaya 4,2x. Di bawahnya, 324 dari 667 sesi terbaru membawa sinyal
pemborosan, dirinci berdasarkan penyebabnya.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Ia menunjukkan ke mana uang itu pergi, di setiap jendela waktu.**
$252,47 hari ini, $513,15 minggu ini, $1.312,92 bulan ini, masing-masing dengan
token di baliknya dan seberapa besar bagian yang sudah ditanggung oleh langganan
Anda. Di bawahnya, sekitar $1.128/bulan dirinci sebagai dapat dipulihkan dan
$17.256/bulan sudah dihemat berkat penggunaan ulang cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Ia menggambarkan bagaimana sebuah pesan menjadi sebuah jawaban.**
Diagram flow langsung: Anda, channel tempat pesan itu tiba, gateway, model yang
sedang menjawab saat ini, dan setiap tool yang ia gunakan. Node menyala saat
pekerjaan bergerak melaluinya.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Setiap agent di mesin, dalam satu tabel.**
Apa yang dijalankannya, berapa biayanya dalam 24 jam terakhir dan sepanjang
masa pakainya, kapan terakhir terlihat, siapa pemiliknya, dan apakah sebuah
langganan menanggung tagihannya. 14 agent di sini, 3 sesi sedang bekerja, 13 diam.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Ia menunjukkan ke mana waktu dan uang sebuah giliran (turn) pergi, tool demi tool.**
Satu giliran dari sesi nyata: 11 tool dalam 11,2 menit seharga $1,16. Setiap
panggilan Bash dan panggilan model mendapatkan batangnya sendiri di linimasa,
sehingga perintah yang berjalan 4,1 menit dan yang berjalan 226 md bisa dibedakan sekilas.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ia menilai hasil kerjanya, bukan sekadar pengeluarannya.**
Nilai A minggu ini: 54 tugas selesai dengan bersih, 2 yang bermasalah menghabiskan
$48,57, dan proses dengan aktivitas terlalu sedikit untuk dinilai dikeluarkan dari
penilaian alih-alih dihitung sebagai keberhasilan. Setiap proses bermasalah tertaut
ke trace-nya.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Ia menunjukkan mengapa context window terus terisi penuh.**
715K dari window 1 juta token pada giliran terbaru, puncak 83,3%, 4 kompaksi yang
semuanya terpicu secara proaktif alih-alih akibat overflow, dan pemanfaatan setiap
giliran di baliknya.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Deteksi berjalan tanpa Anda perlu mengonfigurasi apa pun.**
Detektor bawaan aktif sejak instalasi: agent diam, feed telemetri berhenti,
lonjakan biaya, ledakan token, error meningkat, lonjakan error, ambang anggaran,
tanda tangan ancaman cocok, temuan tool keamanan, perubahan postur keamanan.
Aturan Anda sendiri bersifat opsional sebagai tambahan.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Menahan panggilan berisiko bersifat opt-in, dan dikirim dalam keadaan nonaktif.**
Penghapusan rekursif, force push, sudo, secret, instalasi paket, dan panggilan
keluar masing-masing mendapatkan aturan yang bisa Anda aktifkan. Sampai Anda
melakukannya, ClawMetry mengamati dan tidak mengubah apa pun. Setelah salah
satunya aktif, panggilan yang cocok akan menunggu di sini (atau di ponsel Anda)
untuk disetujui atau ditolak.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Lebih banyak lagi, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Pengakuan

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Riwayat Bintang

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
