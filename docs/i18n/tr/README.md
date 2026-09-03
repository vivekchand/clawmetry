<!-- i18n-src:9767c8001c9c -->
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

**Aracınızın düşündüğünü görün.** **30 yapay zeka ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 26 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

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

Her çalışma zamanı aynı gösterge panelini alır. Birden fazlasını aynı anda çalıştırın, başlıktaki geçiş anahtarı her sekmeyi seçtiğiniz çalışma zamanına yeniden kapsar.

Kendi ajanınızı bir SDK üzerinde mi kurdunuz? Interceptor onun LLM çağrılarını da izler. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın ne yaptığı, tur tur, tekrar oynatma ile
- **Maliyet ve token'lar**: çalışma zamanı, model, oturum ve gün bazında, anomali işaretleriyle
- **Akış**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Beyin**: gerçekleştiği anda muhakeme ve araç çağrısı olay akışı
- **Bağlam taşması**: sağlayıcı bazında boyutlandırılmış pencere kullanımı, sıkıştırma (compaction) ile zorlanmış taşma karşılaştırması, artı çalışma zamanı bazında *göremediğimiz* şeylerin bir haritası ([nasıl](docs/CONTEXT_BLOWOUT.md))
- **Bellek ve yetenekler**: her çalışma zamanının gerçekten yüklediği dosyalar ve yetenekler
- **Sağlık ve günlükler**: disk, bellek, hata oranları, hız sınırları, canlı günlük akışı
- **Uyarılar**: bütçe sınırları, hata artışları, ajan çevrimdışı, Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirilir
- **Onaylar**: riskli araç çağrılarını çalışmadan *önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Bağlam taşması ve izlemenin maliyeti

Herhangi bir ajan karşılaştırma aracına güvenmeden önce yanıtlanmaya değer iki soru.

**Çalışma zamanları arasında bağlam penceresi taşmasını nasıl ele alıyor?**

Kullanım yüzdesi, ancak neye böldüğü kadar dürüst olabilir. ClawMetry, penceriyi
[okuyabileceğiniz ve PR gönderebileceğiniz bir tablodan](clawmetry/context_windows.py)
sağlayıcı bazında boyutlandırır; Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi,
Qwen, Mistral, Llama ve GLM'yi kapsar. 26 çalışma zamanının tamamını tek bir
sağlayıcının cetveliyle ölçmez. Bu önemlidir: Anthropic'in 200K'sine karşı
puanlanan 300K'lik bir GPT-5 turu, aslında GPT-5'in 400K'sinin %75'inde
olmasına rağmen ">%100, patlamış" okunur. Aynı cetvel, gerçekten taşmış 130K'lik
bir DeepSeek turunu rahat bir %65 olarak gizler.

Her pencere kendi kökenini taşır: `model_table`, `explicit_marker`,
`observed_floor` veya modeli bilmediğimizde dürüst bir `default`. Bir tahmine
dayalı gösterge, asla bir arama sonucuna dayalı olanla aynı otoriteyle
görüntülenmez.

ClawMetry bazı çalışma zamanlarında yalnızca sıkıştırma (compaction) olaylarını
görebilir. Bu nedenle `GET /api/context-coverage`, her çalışma zamanı için
**sıfırın "temiz çalıştı" mı yoksa "körüz" mü** anlamına geldiğini bildirir.
Aslında kör anlamına gelen bir `0` bunu belirtir.
[Tüm ayrıntılar](docs/CONTEXT_BLOWOUT.md)

**Enstrümantasyonun maliyeti ne?**

| Yol | Ajanınıza eklenen | Varsayılan mı? |
|---|---|---|
| Oturum dosyası takibi (30 çalışma zamanının tümü) | **0**. Ayrı süreç, ajanınızda ClawMetry kodu yok | açık |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | LLM çağrısı başına **+0.44 ms**, ya da 5 saniyelik bir çağrının %0.009'u | kapalı |
| Araç öncesi hook kapısı (sıcak önbellek) | Kapılı araç çağrısı başına **+44 ms**, 36 ms'lik yorumlayıcı tabanının üzerinde | kapalı |
| Uygulama proxy'si | LLM çağrısı başına **+9.7 ms** | kapalı |

Daemon barındırma maliyeti: saniyede **2.762 olay** alım hızı, olay başına
diskte **710 byte** (100 bin olay için 67,7 MB) ve yoğun bir kurulumda
sürekli olarak **bir çekirdeğin ~%12'si**. Bu son rakam kendi belirttiğimiz
%5-10 bütçenin üzerinde olduğu için, sayfadan çıkarılmak yerine peşine
düşülecek bir hata olarak yayınlanıyor.

Apple M2 Pro üzerinde `benchmarks/overhead.py` ile ölçülmüştür. Test seti her
koşulu ayrı bir süreçte çalıştırır, sıralarını değiştirir ve **turlar işaretin
yönü konusunda uyuşmadığında bir sayı yazdırmayı reddeder**. Kendi makinenizde
bir dakikada çalıştırın:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Hook kapıları ve uygulama proxy'si dahil her yol ölçülür ve test seti CI'da
Linux, macOS ve Windows üzerinde çalışır. Bilinmeye değer iki sonuç: proxy
Windows'ta Linux'a göre yaklaşık yedi kat daha maliyetli ve daemon şu anda
kendi %5-10 bütçemizin üzerinde, bir çekirdeğin yaklaşık %12'sini sürekli
kullanıyor. Ham JSON, yöntem ve hâlâ ölçülmemiş olanlar
[docs/OVERHEAD.md](docs/OVERHEAD.md) içinde.

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, tam gösterge paneli, yalnızca yerel | $0 |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | düğüm başına $9 / ay |
| **Pro** | Starter + kontrol ve değerlendirme: onaylar, araç risk politikaları, değerlendirmeler, anomali tespiti, maliyet optimize edici, OTel dışa aktarma, kurcalamaya karşı dayanıklı denetim günlüğü | düğüm başına $19 / ay |

Yıllık planlar, Kurumsal ve güncel rakamlar
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** adresinde. Kendi
sunucunuzda barındırılan lisans anahtarları bulut olmadan çalışır
(`clawmetry license`). Ücretsiz/ücretli ayrımının tam hali
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) içinde.

## Verileriniz makinenizde kalır

ClawMetry yerel oturum dosyalarını ve günlükleri okur. **`clawmetry connect`
çalıştırmadığınız sürece hiçbir oturum verisi makinenizden çıkmaz** — istem
yok, yanıt yok, araç argümanı yok, dosya içeriği ya da günlük satırı yok.
Bağlandığınızda ise anlık görüntü, makinenizden hiç çıkmayan bir anahtarla
uçtan uca şifrelenir ve tarayıcınızda çözülür. Bir düğümün anahtarı yoksa,
yükleme açık metin olarak gönderilmek yerine atlanır ve hiçbir sunucu yanıtı
bunu kapatamaz.

Bağlanmadan önce varsayılan olarak iki şey çalışır, ikisi de opt-out ve
hiçbiri oturum verisi taşımaz: anonim bir kurulum pingi ve PyPI'ye karşı bir
sürüm kontrolü. Varsayılan bir kurulum ayrıca başlangıç banner satırı için
genel IP adresinizi bir kez arar. Her hedef, taşıdığı şey ve nasıl
kapatılacağı [docs/EGRESS.md](docs/EGRESS.md) içinde listelenmiştir; kendi
sunucusunda barındırılan, yeniden yönlendirilmiş ve hava boşluklu (air-gapped)
kurulumlar hiçbir isteğe bağlı giden çağrı yapmaz.

Şifre çözme, size sunduğumuz kod içinde, tarayıcınızda gerçekleşir. Bu bir
zamanlar bir vaatti; şimdi kontrol edebileceğiniz bir şey. Anahtarınıza dokunan
her satır, wheel içinde gönderilen ve bir Subresource Integrity hash'iyle
sabitlenerek olduğu gibi sunulan okunabilir tek bir dosyada yaşıyor:
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js). Tarayıcının
yayınladığımız şeyi çalıştırdığını doğrulamak için:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Bunun kanıtlamadığı şey: dosyayı yükleyen sayfayı biz sunuyoruz, dolayısıyla
farklı bir sayfa sunabiliriz. Integrity hash'leri sizi ele geçirilmiş bir
CDN'den korur, satıcıdan değil. Kazandığınız şey, herhangi bir değişikliğin
kasıtlı, sayfa kaynağında görünür ve herkesin PyPI'den indirebileceği bir
yapıttan farklı olması gerektiğidir. Kendi sunucunuzda barındırmak veya
yalnızca yerel kalmak bu bağımlılığı tamamen ortadan kaldırır.

## Kurulum

```bash
pip install clawmetry     # ardından: clawmetry
```

Ya da tek satırlık kurulum: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows'ta Python 3.8+ ve aynı makinede en az bir ajan
çalışma zamanı gerektirir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

## Dokümanlar

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her adaptörün ne okuduğu ve bir çalışma zamanı nasıl eklenir |
| [Bağlam taşması](docs/CONTEXT_BLOWOUT.md) | Sağlayıcı bazında pencereler, sıkıştırma ile taşma karşılaştırması, çalışma zamanı bazında kapsama |
| [Ek yük (Overhead)](docs/OVERHEAD.md) | Enstrümantasyonun maliyeti, ölçülmüş, yeniden üretmek için test seti ile |
| [Yetkilendirmeler](docs/ENTITLEMENTS.md) | Ücretsiz ve ücretli, katman matrisi, lisans CLI'sı |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Yürütme öncesi kapılama, risk puanlama, telefon onayları |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri (traces) her yere dışa aktarın, herhangi bir yerden OTLP alın |
| [Kendi ajanınızı getirin](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain uçtan uca, çalıştırılabilir örneklerle |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi oluşturduğunuz ajanlar için maliyet atfı |
| [Sohbet kanalları](docs/CHANNELS.md) | Akış'ta gösterilen sohbet adaptörleri |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandbox'lı NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | İmaj, compose, birim (volume) bağlamaları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynaktan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü açma pingleri, ve bunların nasıl kapatılacağı |

## Ekran görüntüleri

Aşağıdaki her rakam, hiçbir şey ekilmeden, salt okunur olarak gerçek bir
makineden alınmıştır.

**Bir şeyin yanlış olduğunu söyler, sadece ne olduğunu değil.**
Üstte iki anomali banner'ı: harcama günlük ortalamanın 7 katı çalışıyor ve
4,2 kat maliyet artışı. Altlarında, son 667 oturumun 324'ü bir israf sinyali
taşıyor, nedenine göre ayrıntılandırılmış.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Paranın nereye gittiğini her pencerede gösterir.**
Bugün $252,47, bu hafta $513,15, bu ay $1.312,92; her biri arkasındaki
token'lar ve aboneliğinizin bunun ne kadarını zaten karşıladığı ile birlikte.
Altında, kurtarılabilir olarak ayrıntılandırılmış yaklaşık $1.128/ay ve
önbellek yeniden kullanımıyla zaten tasarruf edilmiş $17.256/ay.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Bir mesajın nasıl yanıta dönüştüğünü çizer.**
Canlı akış diyagramı: siz, mesajın geldiği kanal, ağ geçidi, şu anda yanıt
veren model ve başvurduğu her araç. İş onlardan geçtikçe düğümler yanar.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Makinedeki her ajan, tek bir tabloda.**
Ne çalıştırdığı, son 24 saatte ve yaşam boyu ne kadara mal olduğu, en son ne
zaman görüldüğü, kime ait olduğu ve bir aboneliğin faturayı karşılayıp
karşılamadığı. Burada 14 ajan, 3 oturum çalışıyor, 13 sessiz.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Bir turun zamanının ve parasının araç araç nereye gittiğini gösterir.**
Gerçek bir oturumdan bir tur: 11,2 dakikada 11 araç, $1,16'ya. Her Bash
çağrısı ve model çağrısı zaman çizelgesinde kendi çubuğunu alır, böylece
4,1 dakika süren komut ile 226 ms süren komut bir bakışta ayırt edilir.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Sadece harcamayı değil, işi de not verir.**
Bu hafta bir A: 54 görev temiz döndü, 2 pürüzlü görev $48,57'ye mal oldu, ve
değerlendirmek için çok az etkinliği olan çalışmalar kazanç olarak
sayılmak yerine notun dışında bırakılıyor. Her pürüzlü çalışma kendi izine
bağlanıyor.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Bağlam penceresinin neden dolmaya devam ettiğini gösterir.**
Son turda 1M token'lık pencerenin 715K'sı, %83,3'lük bir zirve, tümü bir
taşma yerine proaktif olarak tetiklenen 4 sıkıştırma ve arkasındaki her
turun kullanım oranı.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tespit, siz hiçbir şey yapılandırmadan çalışır.**
Yerleşik dedektörler kurulumdan itibaren açıktır: ajan sessizleşti, telemetri
akışı durdu, maliyet artışı, token patlaması, artan hatalar, hata artışı,
bütçe eşiği, tehdit imzası eşleşti, güvenlik aracı bulgusu, güvenlik
duruşu değişti. Kendi kurallarınız isteğe bağlı olarak üstüne eklenir.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Riskli bir çağrıyı bekletmek isteğe bağlıdır ve kapalı olarak gelir.**
Özyinelemeli silmeler, force push'lar, sudo, sırlar, paket kurulumları ve
giden çağrıların her biri açabileceğiniz bir kurala sahiptir. Siz açana
kadar, ClawMetry izler ve hiçbir şeyi değiştirmez. Biri açıldığında, eşleşen
çağrılar burada (ya da telefonunuzda) bir onay ya da red için bekler.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Çalışma zamanı bazında daha fazlası: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
