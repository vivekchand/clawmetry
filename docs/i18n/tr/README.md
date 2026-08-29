<!-- i18n-src:d21bea5161e0 -->
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

**Aracınızın düşündüğünü görün.** **30 farklı yapay zeka ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 26 tane daha. Tüm ajan filonuz için tek bir kontrol paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır. Sıfır yapılandırma: zaten sahip olduğunuz ajan çalışma zamanlarını bulur, onları salt okunur olarak okur ve nasıl çalıştıkları konusunda hiçbir şeyi değiştirmez.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ajan çalışma zamanıyla çalışır

**Açık kaynak uygulamada ücretsiz:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Ücretli planda:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Her çalışma zamanı aynı kontrol panelini alır. Aynı anda birden fazlasını çalıştırın; üstteki geçiş anahtarı her sekmeyi seçtiğiniz çalışma zamanına yeniden odaklar.

Kendi ajanınızı bir SDK üzerine mi kurdunuz? Interceptor onun LLM çağrılarını da takip eder. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın adım adım ne yaptığı, tekrar oynatma ile
- **Maliyet ve token'lar**: çalışma zamanı, model, oturum ve gün başına, anomali işaretleriyle
- **Akış**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Beyin (Brain)**: gerçekleştiği anda akan akıl yürütme ve araç çağrısı olay akışı
- **Bağlam patlaması (Context blowout)**: sağlayıcıya göre boyutlandırılmış pencere kullanımı, sıkıştırma (compaction) ile zorlanmış taşma karşılaştırması, artı çalışma zamanı başına *göremediğimiz* şeylerin haritası ([nasıl](docs/CONTEXT_BLOWOUT.md))
- **Bellek ve yetenekler**: her çalışma zamanının gerçekte yüklediği dosyalar ve yetenekler
- **Sağlık ve loglar**: disk, bellek, hata oranları, hız sınırları, canlı log akışı
- **Uyarılar**: bütçe sınırları, hata sıçramaları, ajan çevrimdışı durumu; Slack, Discord, PagerDuty, Telegram, E-postaya yönlendirilir
- **Onaylar**: riskli araç çağrılarını çalışmadan *önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Bağlam patlaması ve izlemenin maliyeti

Herhangi bir ajan karşılaştırma aracına güvenmeden önce yanıtlanmaya değer iki soru.

**Çalışma zamanları arasında bağlam penceresi patlamasını nasıl ele alıyor?**

Bir kullanım yüzdesi, ancak neye bölündüğü kadar dürüsttür. ClawMetry pencereyi
sağlayıcı başına, [okuyabileceğiniz ve PR gönderebileceğiniz bir tablodan](clawmetry/context_windows.py)
boyutlandırır; Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral,
Llama ve GLM'yi kapsar. 26 çalışma zamanının tamamını tek bir sağlayıcının
cetveliyle ölçmez. Bu önemlidir: Anthropic'in 200K'sına karşı puanlanan 300K'lık
bir GPT-5 turu, aslında GPT-5'in 400K'sının %75'indeyken ">%100, patladı" olarak
okunur. Aynı cetvel, gerçekten taşmış 130K'lık bir DeepSeek turunu rahat bir
%65 olarak gizler.

Her pencere kendi kökenini taşır: `model_table`, `explicit_marker`,
`observed_floor` veya modeli bilmediğimizde dürüst bir `default`. Bir tahmine
dayalı gösterge, hiçbir zaman bir arama sonucuna dayalı olanla aynı otoriteyle
görüntülenmez.

ClawMetry sıkıştırma (compaction) olaylarını yalnızca bazı çalışma zamanlarında
görebilir. Bu yüzden `GET /api/context-coverage`, her çalışma zamanı için,
**sıfırın "temiz çalıştı" mı yoksa "kör durumdayız" mı** anlamına geldiğini
bildirir. Gerçekte kör anlamına gelen bir `0`, bunu açıkça belirtir.
[Tam ayrıntı](docs/CONTEXT_BLOWOUT.md)

**Enstrümantasyonun maliyeti nedir?**

| Yol | Ajanınıza eklenen | Varsayılan mı? |
|---|---|---|
| Oturum dosyası izleme (tüm 30 çalışma zamanı) | **0**. Ayrı bir süreç, ajanınızda ClawMetry kodu yok | açık |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | LLM çağrısı başına **+0.44 ms**, ya da 5 saniyelik bir çağrının %0.009'u | kapalı |
| Araç öncesi hook kapısı (ısınmış önbellek) | Kapıdan geçirilen araç çağrısı başına **+44 ms**, 36 ms'lik yorumlayıcı tabanının üzerinde | kapalı |
| Uygulama proxy'si | LLM çağrısı başına **+9.7 ms** | kapalı |

Daemon barındırma maliyeti: **2.762 olay/saniye** alım, olay başına diskte
**710 bayt** (100 bin olay için 67.7 MB) ve meşgul bir kurulumda sürdürülen
**bir çekirdeğin ~%12'si**. Bu son sayı, bizim kendi belirttiğimiz %5-10
bütçesinin üzerinde, bu yüzden sayfadan çıkarılmak yerine peşinden koşulacak
bir hata olarak yayınlanıyor.

Bir Apple M2 Pro üzerinde `benchmarks/overhead.py` ile ölçüldü. Test düzeneği
her koşulu ayrı bir süreçte çalıştırır, sıralarını değiştirir ve **turlar
işaretinde anlaşamadığında bir sayı yazdırmayı reddeder**. Kendi
makinenizde bir dakikada çalıştırın:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Hook kapıları ve uygulama proxy'si dahil her yol ölçülür ve test düzeneği CI'da
Linux, macOS ve Windows üzerinde çalışır. Bilinmeye değer iki sonuç: proxy,
Windows'ta Linux'a göre yaklaşık yedi kat daha maliyetli ve daemon şu anda
bizim kendi %5-10 bütçemizin üzerinde, bir çekirdeğin yaklaşık %12'sini
sürdürüyor. Ham JSON, yöntem ve hâlâ ölçülmemiş olan şeyler
[docs/OVERHEAD.md](docs/OVERHEAD.md) içinde.

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Ücretsiz** | OpenClaw + NVIDIA NemoClaw + Goose, tam kontrol paneli, yalnızca yerel | 0 $ |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | Düğüm başına ayda 9 $ |
| **Pro** | Starter + kontrol ve değerlendirme: onaylar, araç riski politikaları, değerlendirmeler (evals), anomali tespiti, maliyet optimize edici, OTel dışa aktarımı, kurcalamaya karşı kanıtlanabilir denetim günlüğü | Düğüm başına ayda 19 $ |

Yıllık planlar, Enterprise ve güncel rakamlar **[clawmetry.com/pricing](https://clawmetry.com/pricing)**
adresinde. Kendi sunucunuzda barındırılan lisans anahtarları bulut olmadan
çalışır (`clawmetry license`). Ücretsiz/ücretli ayrımının tam hali
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) içinde.

## Verileriniz makinenizde kalır

ClawMetry yerel oturum dosyalarını ve logları okur. **`clawmetry connect`
çalıştırmadığınız sürece hiçbir oturum verisi makinenizden çıkmaz** — istem,
yanıt, araç argümanları, dosya içeriği ya da log satırı yok. Bağlandığınızda,
anlık görüntü, makinenizden asla ayrılmayan bir anahtarla uçtan uca şifrelenir
ve tarayıcınızda çözülür. Bir düğümün anahtarı yoksa, yükleme açık metin
olarak gönderilmek yerine atlanır ve hiçbir sunucu yanıtı bunu kapatamaz.

Bağlanmadan önce varsayılan olarak çalışan iki şey var, ikisi de opt-out ve
hiçbiri oturum verisi taşımıyor: anonim bir kurulum pingi ve PyPI'ye karşı bir
sürüm kontrolü. Varsayılan bir kurulum ayrıca başlangıç banner satırı için
genel IP'nizi bir kez sorgular. Her hedef, neyi taşıdığı ve nasıl
kapatılacağı [docs/EGRESS.md](docs/EGRESS.md) içinde listelenmiştir; kendi
sunucunuzda barındırılan, yeniden yönlendirilmiş ve hava boşluklu (air-gapped)
kurulumlar hiçbir isteğe bağlı giden çağrı yapmaz.

Şifre çözme, size sunduğumuz kod içinde, tarayıcınızda gerçekleşir. Bu eskiden
bir vaatti; artık kontrol edebileceğiniz bir şey. Anahtarınıza dokunan her
satır tek bir okunabilir dosyada yaşıyor,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js); bu dosya
wheel paketinin içinde gönderilir ve bir Subresource Integrity hash'i ile
sabitlenmiş şekilde olduğu gibi sunulur. Tarayıcının yayınladığımız şeyi
çalıştırdığını doğrulamak için:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Bunun kanıtlamadığı şey şu: dosyayı yükleyen sayfayı biz sunuyoruz, yani farklı
bir sayfa da sunabiliriz. Bütünlük hash'leri sizi ele geçirilmiş bir CDN'den
korur, satıcıdan değil. Kazandığınız şey, herhangi bir değişikliğin kasıtlı,
sayfa kaynağında görünür ve herkesin PyPI'den indirebileceği bir yapıttan
farklı olması gerektiğidir. Kendi sunucunuzda barındırmak veya yalnızca yerel
kalmak bu bağımlılığı tamamen ortadan kaldırır.

## Kurulum

```bash
pip install clawmetry     # sonra: clawmetry
```

Ya da tek satırlık kurulum: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows'ta Python 3.8+ ve aynı makinede en az bir ajan
çalışma zamanı gerektirir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

## Belgeler

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her adaptörün neyi okuduğu ve bir çalışma zamanı nasıl eklenir |
| [Bağlam patlaması](docs/CONTEXT_BLOWOUT.md) | Sağlayıcı başına pencereler, sıkıştırma ile taşma karşılaştırması, çalışma zamanı başına kapsam |
| [Ek yük (Overhead)](docs/OVERHEAD.md) | Enstrümantasyonun maliyeti, ölçülmüş şekilde, yeniden üretmek için test düzeneğiyle birlikte |
| [Haklar (Entitlements)](docs/ENTITLEMENTS.md) | Ücretsiz ile ücretli, katman matrisi, lisans CLI'ı |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Çalıştırma öncesi kapılama, risk puanlama, telefon onayları |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri (traces) herhangi bir yere dışa aktarın, herhangi bir yerden OTLP alın |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi kurduğunuz ajanlar için maliyet ilişkilendirmesi |
| [Sohbet kanalları](docs/CHANNELS.md) | Akışta (Flow) gösterilen sohbet adaptörleri |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandbox'lanmış NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | İmaj, compose, birim (volume) bağlamaları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynaktan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü açılış pingleri, ve bunların nasıl kapatılacağı |

## Ekran görüntüleri

Aşağıdaki her sayı, hiçbir şey seed edilmeden, salt okunur olarak gerçek bir
makineden alınmıştır.

**Bir şeyin yanlış olduğunu, sadece ne olduğunu değil, size söyler.**
Üstte iki anomali banner'ı: harcamanın günlük ortalamanın 7 katı çalışması ve
4.2 kat maliyet sıçraması. Bunların altında, son 667 oturumdan 324'ü, nedenine
göre ayrıştırılmış bir israf sinyali taşıyor.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Paranın nereye gittiğini, her pencerede gösterir.**
Bugün 252.47 $, bu hafta 513.15 $, bu ay 1.312.92 $, her biri arkasındaki
token'lar ve aboneliğinizin bunun ne kadarını zaten karşıladığıyla birlikte.
Altında, kurtarılabilir olarak ayrıştırılmış yaklaşık 1.128 $/ay ve önbellek
yeniden kullanımıyla zaten tasarruf edilmiş 17.256 $/ay.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Bir mesajın nasıl bir yanıta dönüştüğünü çizer.**
Canlı akış diyagramı: siz, mesajın ulaştığı kanal, ağ geçidi (gateway), şu
anda yanıt veren model ve başvurduğu her araç. Düğümler, iş üzerlerinden
geçtikçe yanar.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Makinedeki her ajan, tek bir tabloda.**
Ne çalıştırdığı, son 24 saatte ve yaşam boyu ne kadara mal olduğu, en son ne
zaman görüldüğü, kime ait olduğu ve bir aboneliğin faturayı karşılayıp
karşılamadığı. Burada 14 ajan, 3 oturum çalışıyor, 13'ü sessiz.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Bir turun zamanının ve parasının nereye gittiğini araç araç gösterir.**
Gerçek bir oturumun bir turu: 11.2 dakikada 11 araç, 1.16 $'a. Her Bash
çağrısı ve model çağrısı zaman çizelgesinde kendi çubuğunu alır, böylece 4.1
dakika süren komut ile 226 ms süren komut bir bakışta ayırt edilir.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Sadece harcamayı değil, işin kendisini de not verir.**
Bu hafta bir A notu: 54 görev temiz döndü, 2 sorunlu görev 48.57 $'a mal oldu
ve değerlendirilemeyecek kadar az etkinliği olan çalışmalar, kazanç olarak
sayılmak yerine notun dışında bırakıldı. Her sorunlu çalışma kendi izine
(trace) bağlanır.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Bağlam penceresinin neden sürekli dolduğunu gösterir.**
1M token'lık pencerenin en son turda 715K'sı, %83.3 zirve, hepsi bir taşma
üzerine değil proaktif olarak tetiklenen 4 sıkıştırma ve bunun arkasındaki her
turun kullanım oranı.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tespit, siz hiçbir şey yapılandırmadan çalışır.**
Yerleşik dedektörler kurulumdan itibaren açıktır: ajan sessizleşti, telemetri
akışı durdu, maliyet sıçraması, token patlaması, hatalar artıyor, hata
sıçraması, bütçe eşiği, tehdit imzası eşleşti, güvenlik aracı bulgusu,
güvenlik duruşu değişti. Kendi kurallarınız bunun üzerine isteğe bağlıdır.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Riskli bir çağrıyı bekletmek isteğe bağlıdır ve kapalı olarak gönderilir.**
Özyinelemeli silmeler, zorla push'lar, sudo, gizli anahtarlar (secrets), paket
kurulumları ve giden çağrıların her biri açabileceğiniz bir kural alır. Siz
açana kadar ClawMetry izler ve hiçbir şeyi değiştirmez. Biri açıldığında,
eşleşen çağrılar burada (ya da telefonunuzda) onay veya ret için bekler.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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
