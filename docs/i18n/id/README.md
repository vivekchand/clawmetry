<!-- i18n-src:6795052055e2 -->
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

**Lihat pemikiran agen Anda.** Observabilitas real-time untuk **26 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 22 lainnya. Satu dashboard untuk seluruh armada agen Anda.

> 🌐 **Baca ini dalam:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900**. Tanpa konfigurasi: alat ini menemukan runtime agen
yang sudah Anda miliki, membacanya secara read-only, dan tidak mengubah apa pun tentang cara kerjanya.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Bekerja dengan 26 runtime agen

**Gratis di aplikasi open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Pada paket berbayar:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Setiap runtime mendapatkan dashboard yang sama. Jalankan beberapa sekaligus dan pengalih
header akan menyesuaikan cakupan setiap tab ke salah satunya.

Membuat agen Anda sendiri di atas sebuah SDK? Interceptor juga melacak panggilan LLM-nya.
Lihat [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Apa yang Anda dapatkan

- **Sesi & transkrip**: apa yang dilakukan setiap agen, giliran demi giliran, dengan replay
- **Biaya & token**: per runtime, model, sesi, dan hari, dengan penanda anomali
- **Flow**: diagram langsung pesan yang bergerak melalui channel, model, dan tool
- **Brain**: aliran peristiwa penalaran dan pemanggilan tool saat terjadi
- **Memory & skill**: file dan skill yang benar-benar dimuat oleh setiap runtime
- **Health & log**: disk, memori, tingkat error, batas laju, aliran log langsung
- **Alert**: batas anggaran, lonjakan error, agen offline, dialihkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Approval**: menjeda pemanggilan tool yang berisiko *sebelum* dijalankan dan menyetujuinya dari ponsel Anda ([cara kerjanya](docs/APPROVALS.md))

## Harga

| Paket | Cakupan | Harga |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard lengkap, hanya lokal | $0 |
| **Starter** | Semua runtime lain di atas, tampilan armada, sinkronisasi cloud | $9 per node / bulan |
| **Pro** | Starter + governance: approval, kebijakan risiko tool, evals, deteksi anomali, cost optimizer, ekspor OTel | $19 per node / bulan |

Paket tahunan, Enterprise, dan angka terkini ada di
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Kunci lisensi self-hosted
berfungsi tanpa cloud (`clawmetry license`). Pembagian gratis/berbayar yang persis ada
di [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Data Anda tetap di mesin Anda

ClawMetry membaca file sesi dan log lokal. Tidak ada yang meninggalkan mesin Anda kecuali
Anda menjalankan `clawmetry connect`. Bahkan saat itu pun, snapshot dienkripsi end-to-end
dengan kunci yang tidak pernah meninggalkan mesin Anda, dan didekripsi di browser Anda.

## Instalasi

```bash
pip install clawmetry     # lalu: clawmetry
```

Atau perintah satu baris: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Membutuhkan Python 3.8+ di macOS, Linux, atau Windows, dan setidaknya satu runtime agen di
mesin yang sama. Petunjuk Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentasi

| | |
|---|---|
| [Kompatibilitas runtime](docs/compatibility.md) | Apa yang dibaca setiap adapter, dan cara menambahkan runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis vs berbayar, matriks tier, license CLI |
| [Approval & kebijakan](docs/APPROVALS.md) | Gating pra-eksekusi, penilaian risiko, approval via ponsel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Ekspor trace ke mana saja, ingest OTLP dari apa saja |
| [Pelacakan SDK](docs/SDK_TRACKING.md) | Atribusi biaya untuk agen yang Anda buat sendiri |
| [Chat channel](docs/CHANNELS.md) | Adapter chat yang ditampilkan di Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Setup NVIDIA NemoClaw yang di-sandbox |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Arsitektur](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Cara kerjanya di dalam; menjalankan dari source |
| [Telemetri](docs/TELEMETRY.md) | Ping instalasi dan pembukaan desktop yang anonim, dan cara menonaktifkannya |

## Tangkapan layar

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: token, sesi, health | **Brain**: aliran peristiwa agen secara langsung |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: berdasarkan model dan sesi | **Approvals**: menggerbang pemanggilan tool berisiko |

Lebih banyak, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Riwayat Star

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
