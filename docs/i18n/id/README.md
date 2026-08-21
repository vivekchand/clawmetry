<!-- i18n-src:dc34072b2955 -->
> Bahasa Indonesia translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Lihat pemikiran agen Anda.** Observabilitas real-time untuk **23 runtime agen AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 19 lainnya. Satu dashboard untuk seluruh armada agen Anda.

> 🌐 **Baca dalam bahasa lain:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [lainnya →](docs/i18n/)

Satu perintah. Tanpa konfigurasi. Mendeteksi semuanya secara otomatis.

```bash
pip install clawmetry && clawmetry
```

Terbuka di **http://localhost:8900**. Tanpa konfigurasi: aplikasi ini menemukan
runtime agen yang sudah Anda miliki, membacanya secara read-only, dan tidak mengubah apa pun tentang cara kerjanya.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Bekerja dengan 23 runtime agen

**Gratis di aplikasi open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**Pada paket berbayar:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Setiap runtime mendapat dashboard yang sama. Jalankan beberapa sekaligus dan
pengalih di header akan mengarahkan ulang setiap tab ke salah satunya.

Membuat agen Anda sendiri dengan sebuah SDK? Interceptor juga melacak panggilan LLM-nya.
Lihat [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Apa yang Anda dapatkan

- **Sesi & transkrip**: apa yang dilakukan setiap agen, giliran demi giliran, dengan replay
- **Biaya & token**: per runtime, model, sesi dan hari, dengan penanda anomali
- **Flow**: diagram langsung dari pesan yang bergerak melalui channel, model dan tool
- **Brain**: aliran peristiwa penalaran dan pemanggilan tool saat terjadi
- **Memory & skills**: file dan skill yang benar-benar dimuat oleh setiap runtime
- **Health & logs**: disk, memori, tingkat error, batas laju, aliran log langsung
- **Alerts**: batas anggaran, lonjakan error, agen-offline, diarahkan ke Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: jeda pemanggilan tool berisiko *sebelum* dijalankan dan setujui dari ponsel Anda ([caranya](docs/APPROVALS.md))

## Harga

| Paket | Yang dicakup | Harga |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw, dashboard lengkap, hanya lokal | $0 |
| **Starter** | Semua runtime lain di atas, tampilan armada, sinkronisasi cloud | $9 per node / bulan |
| **Pro** | Starter + tata kelola: approvals, kebijakan risiko tool, evaluasi, deteksi anomali, pengoptimal biaya, ekspor OTel | $19 per node / bulan |

Paket tahunan, Enterprise dan angka terbaru ada di
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Kunci lisensi self-hosted
bekerja tanpa cloud (`clawmetry license`). Pembagian gratis/berbayar yang tepat ada
di [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Data Anda tetap di mesin Anda

ClawMetry membaca file sesi dan log lokal. Tidak ada yang keluar dari perangkat Anda kecuali
Anda menjalankan `clawmetry connect`. Bahkan saat itu terjadi, snapshot dienkripsi end-to-end
dengan kunci yang tidak pernah meninggalkan mesin Anda, dan didekripsi di browser Anda.

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
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis vs berbayar, matriks tingkat, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pengendalian pra-eksekusi, penilaian risiko, persetujuan lewat ponsel |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Ekspor trace ke mana saja, ingest OTLP dari mana saja |
| [SDK tracking](docs/SDK_TRACKING.md) | Atribusi biaya untuk agen yang Anda bangun sendiri |
| [Chat channels](docs/CHANNELS.md) | Adapter chat yang ditampilkan di Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Setup NVIDIA NemoClaw yang tersandbox |
| [Docker](docs/DOCKER.md) | Image, compose, volume mount |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | Cara kerjanya di dalam; menjalankan dari source |
| [Telemetry](docs/TELEMETRY.md) | Ping instalasi dan pembukaan desktop yang anonim, dan cara mematikannya |

## Tangkapan layar

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: token, sesi, kesehatan | **Brain**: aliran peristiwa agen secara langsung |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: berdasarkan model dan sesi | **Approvals**: menjaga pemanggilan tool berisiko |

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
