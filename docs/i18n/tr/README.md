<!-- i18n-src:dc34072b2955 -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Aracınızın düşünme biçimini görün.** **23 yapay zeka ajanı çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 19 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dilde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır. Sıfır yapılandırma: zaten sahip olduğunuz ajan çalışma zamanlarını bulur, onları salt okunur olarak okur ve nasıl çalıştıkları konusunda hiçbir şeyi değiştirmez.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23 ajan çalışma zamanıyla çalışır

**Açık kaynak uygulamada ücretsiz:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**Ücretli planda:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Her çalışma zamanı aynı gösterge panelini alır. Birden fazlasını aynı anda çalıştırın ve üstteki geçiş anahtarı her sekmeyi bunlardan birine yeniden odaklar.

Kendi ajanınızı bir SDK üzerinde mi oluşturdunuz? İzleyici (interceptor) onun LLM çağrılarını da takip eder. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın ne yaptığı, tur tur, tekrar oynatma ile
- **Maliyet ve token'lar**: çalışma zamanı, model, oturum ve gün bazında, anomali işaretleriyle
- **Akış**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Beyin**: gerçekleştiği anda akan muhakeme ve araç çağrısı olay akışı
- **Bellek ve beceriler**: her çalışma zamanının gerçekte yüklediği dosyalar ve beceriler
- **Sağlık ve günlükler**: disk, bellek, hata oranları, hız sınırları, canlı günlük akışı
- **Uyarılar**: bütçe sınırları, hata artışları, ajan çevrimdışı durumu; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirilir
- **Onaylar**: riskli araç çağrılarını çalışmadan *önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Ücretsiz** | OpenClaw + NVIDIA NemoClaw, tam gösterge paneli, yalnızca yerel | $0 |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | ay başına düğüm başına $9 |
| **Pro** | Starter + yönetişim: onaylar, araç risk politikaları, değerlendirmeler, anomali tespiti, maliyet optimize edici, OTel dışa aktarma | ay başına düğüm başına $19 |

Yıllık planlar, Kurumsal ve güncel rakamlar
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** adresinde bulunur. Kendi kendine barındırılan lisans
anahtarları bulut olmadan çalışır (`clawmetry license`). Ücretsiz/ücretli ayrımının tam detayı
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) içinde.

## Verileriniz kendi makinenizde kalır

ClawMetry yerel oturum dosyalarını ve günlükleri okur. `clawmetry connect` komutunu
çalıştırmadığınız sürece hiçbir şey makinenizden çıkmaz. O durumda bile anlık görüntü,
hiçbir zaman makinenizden ayrılmayan bir anahtarla uçtan uca şifrelenir ve
tarayıcınızda şifresi çözülür.

## Kurulum

```bash
pip install clawmetry     # ardından: clawmetry
```

Veya tek satırlık komut: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows'ta Python 3.8+ ve aynı makinede en az bir ajan çalışma
zamanı gerekir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

## Dokümantasyon

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her bağdaştırıcının (adapter) neyi okuduğu ve bir çalışma zamanının nasıl ekleneceği |
| [Yetkilendirmeler](docs/ENTITLEMENTS.md) | Ücretsiz ve ücretli, katman matrisi, lisans CLI'si |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Çalıştırma öncesi kapı kontrolü, risk puanlama, telefon onayları |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri (traces) her yere dışa aktarın, herhangi bir yerden OTLP alın |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi oluşturduğunuz ajanlar için maliyet ilişkilendirmesi |
| [Sohbet kanalları](docs/CHANNELS.md) | Akış'ta (Flow) gösterilen sohbet bağdaştırıcıları |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Korumalı alan (sandboxed) NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | İmaj, compose, birim (volume) bağlamaları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynak koddan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü açılış sinyalleri ve bunların nasıl kapatılacağı |

## Ekran görüntüleri

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Genel Bakış**: token'lar, oturumlar, sağlık | **Beyin**: canlı ajan olay akışı |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Maliyet**: model ve oturuma göre | **Onaylar**: riskli araç çağrılarını kapıla |

Çalışma zamanı başına daha fazlası: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Yıldız Geçmişi

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lisans

MIT · [@vivekchand](https://github.com/vivekchand) tarafından yapıldı · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
