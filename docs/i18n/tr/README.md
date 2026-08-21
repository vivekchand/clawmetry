<!-- i18n-src:6795052055e2 -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Aracınızın düşünmesini izleyin.** **26 yapay zeka ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 22 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır. Sıfır yapılandırma: zaten sahip olduğunuz ajan çalışma zamanlarını bulur, onları salt okunur olarak okur ve nasıl çalıştıkları konusunda hiçbir şeyi değiştirmez.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 ajan çalışma zamanıyla çalışır

**Açık kaynak uygulamada ücretsiz:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Ücretli planda:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Her çalışma zamanı aynı gösterge panelini alır. Birden fazlasını aynı anda çalıştırın, başlıktaki geçiş anahtarı her sekmeyi bunlardan birine yeniden kapsayacaktır.

Kendi ajanınızı bir SDK üzerinde mi geliştirdiniz? Interceptor onun LLM çağrılarını da izler. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın adım adım ne yaptığı, yeniden oynatma ile
- **Maliyet ve token'lar**: çalışma zamanı, model, oturum ve gün bazında, anomali işaretleriyle
- **Flow**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Brain**: gerçekleştiği anda akan muhakeme ve araç çağrısı olay akışı
- **Bellek ve beceriler**: her çalışma zamanının gerçekten yüklediği dosyalar ve beceriler
- **Sağlık ve loglar**: disk, bellek, hata oranları, hız sınırları, canlı log akışı
- **Uyarılar**: bütçe sınırları, hata artışları, ajan çevrimdışı olması, Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirilir
- **Onaylar**: riskli araç çağrılarını çalıştırılmadan *önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Ücretsiz** | OpenClaw + NVIDIA NemoClaw + Goose, tam gösterge paneli, yalnızca yerel | $0 |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | düğüm başına $9 / ay |
| **Pro** | Starter + yönetişim: onaylar, araç riski politikaları, değerlendirmeler, anomali tespiti, maliyet optimizasyonu, OTel dışa aktarma | düğüm başına $19 / ay |

Yıllık planlar, Enterprise ve güncel rakamlar
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** adresinde yer alır. Kendi sunucunuzda barındırılan lisans
anahtarları bulut olmadan çalışır (`clawmetry license`). Tam ücretsiz/ücretli ayrımı
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) içindedir.

## Verileriniz makinenizde kalır

ClawMetry yerel oturum dosyalarını ve logları okur. `clawmetry connect` komutunu
çalıştırmadığınız sürece bilgisayarınızdan hiçbir şey çıkmaz. Bunu yaptığınızda bile
anlık görüntü, makinenizden asla ayrılmayan bir anahtarla uçtan uca şifrelenir ve
tarayıcınızda çözülür.

## Kurulum

```bash
pip install clawmetry     # ardından: clawmetry
```

Ya da tek satırlık komut: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows üzerinde Python 3.8+ ve aynı makinede en az bir ajan
çalışma zamanı gerektirir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

## Dokümanlar

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her adaptörün ne okuduğu ve bir çalışma zamanının nasıl ekleneceği |
| [Yetkilendirmeler](docs/ENTITLEMENTS.md) | Ücretsiz ile ücretli, katman matrisi, lisans CLI'si |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Yürütme öncesi geçit kontrolü, risk puanlama, telefon onayları |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri her yere dışa aktarın, her şeyden OTLP alın |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi geliştirdiğiniz ajanlar için maliyet atfı |
| [Sohbet kanalları](docs/CHANNELS.md) | Flow'da gösterilen sohbet adaptörleri |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | İzole (sandboxed) NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | İmaj, compose, birim bağlamaları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynaktan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü açma pingleri ve bunların nasıl kapatılacağı |

## Ekran görüntüleri

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: token'lar, oturumlar, sağlık | **Brain**: canlı ajan olay akışı |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: model ve oturuma göre | **Approvals**: riskli araç çağrılarını geçitleyin |

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

MIT · [@vivekchand](https://github.com/vivekchand) tarafından geliştirildi · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
