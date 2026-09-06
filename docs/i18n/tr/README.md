<!-- i18n-src:88be2deff5d5 -->
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

**Aracınızın düşünmesini izleyin.** **30 AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 26 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

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

Her çalışma zamanı aynı gösterge panelini alır. Birden fazlasını aynı anda çalıştırın, başlıktaki seçici her sekmeyi seçtiğiniz çalışma zamanına göre yeniden kapsamlandırır.

Kendi ajanınızı bir SDK üzerinde mi oluşturdunuz? Interceptor onun LLM çağrılarını da izler. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın adım adım ne yaptığı, tekrar oynatma ile
- **Maliyet ve token'lar**: çalışma zamanı, model, oturum ve gün bazında, anomali işaretleriyle
- **Akış**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Beyin**: gerçekleştiği anda akan muhakeme ve araç çağrısı olay akışı
- **Bağlam taşması**: sağlayıcıya göre boyutlandırılmış pencere kullanımı, sıkıştırma ile zorlanmış taşma karşılaştırması, artı göremediğimiz şeylerin çalışma zamanı bazında haritası ([nasıl](docs/CONTEXT_BLOWOUT.md))
- **Bellek ve beceriler**: her çalışma zamanının fiilen yüklediği dosyalar ve beceriler
- **Sağlık ve günlükler**: disk, bellek, hata oranları, hız sınırları, canlı günlük akışı
- **Uyarılar**: bütçe sınırları, hata artışları, ajan çevrimdışı olma durumu, Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirilir
- **Onaylar**: riskli araç çağrılarını çalışmadan *önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Bağlam taşması ve izlemenin maliyeti

Herhangi bir ajan karşılaştırma aracına güvenmeden önce cevaplanmaya değer iki soru.

**Çalışma zamanları arasında bağlam penceresi taşmasını nasıl ele alıyor?**

Bir kullanım yüzdesi, ancak neye böldüğü kadar dürüsttür. ClawMetry pencereyi, [okuyabileceğiniz ve PR gönderebileceğiniz bir tablodan](clawmetry/context_windows.py) sağlayıcı bazında boyutlandırır; bu tablo Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ve GLM'yi kapsar. 30 çalışma zamanının tamamını tek bir satıcının cetveliyle ölçmez. Bu önemlidir: Anthropic'in 200K'sına karşı ölçülen 300K'lık bir GPT-5 turu, aslında GPT-5'in 400K'sının %75'inde iken ">%100, patladı" olarak okunur. Aynı cetvel, gerçekten taşmış olan 130K'lık bir DeepSeek turunu rahat bir %65 olarak gizler.

Her pencere kaynağıyla birlikte gelir: `model_table`, `explicit_marker`, `observed_floor` veya modeli bilmediğimizde dürüst bir `default`. Bir tahmine dayalı gösterge asla bir arama sonucuna dayalı olanla aynı otoriteyle işlenmez.

ClawMetry, sıkıştırma olaylarını yalnızca bazı çalışma zamanlarında görebilir. Bu nedenle `GET /api/context-coverage`, her çalışma zamanı için sıfırın **"temiz çalıştı" mı yoksa "biz göremiyoruz" mu** anlamına geldiğini bildirir. Aslında kör olduğu anlamına gelen bir `0` bunu söyler.
[Tam detay](docs/CONTEXT_BLOWOUT.md)

**Enstrümantasyonun maliyeti nedir?**

| Yol | Ajanınıza eklenen | Varsayılan mı? |
|---|---|---|
| Oturum dosyası izleme (30 çalışma zamanının tamamı) | **0**. Ayrı bir işlem, ajanınızda ClawMetry kodu yok | açık |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | LLM çağrısı başına **+0.44 ms**, ya da 5 saniyelik bir çağrının %0.009'u | kapalı |
| Araçtan önce hook geçidi (ısınmış önbellek) | Kapılı araç çağrısı başına **+44 ms**, 36 ms'lik yorumlayıcı tabanının üzerinde | kapalı |
| Uygulama proxy'si | LLM çağrısı başına **+9.7 ms** | kapalı |

Daemon barındırma maliyeti: saniyede **2.762 olay** alım, disk üzerinde olay başına **710 bayt** (100 bin olay için 67.7 MB) ve yoğun bir kurulumda sürekli olarak **bir çekirdeğin ~%12'si**. Bu son rakam, kendi belirttiğimiz %5-10 bütçenin üzerinde olduğu için sayfada peşinden koşulacak bir hata olarak yayınlanmıştır.

Bir Apple M2 Pro üzerinde `benchmarks/overhead.py` ile ölçülmüştür. Test düzeneği her koşulu ayrı bir işlemde çalıştırır, sıralarını değiştirir ve **turlar işaretinde anlaşamadığında bir sayı yazdırmayı reddeder**. Bir dakikada kendi makinenizde çalıştırın:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Hook geçitleri ve uygulama proxy'si dahil her yol ölçülür ve test düzeneği CI'da Linux, macOS ve Windows üzerinde çalışır. Bilinmeye değer iki sonuç: proxy Windows'ta Linux'a göre yaklaşık yedi kat daha maliyetli ve daemon şu anda bir çekirdeğin yaklaşık %12'sini sürekli kullanıyor, kendi %5-10 bütçemizin üzerinde. Ham JSON, yöntem ve hâlâ ölçülmemiş olanlar [docs/OVERHEAD.md](docs/OVERHEAD.md) içindedir.

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Ücretsiz** | OpenClaw + NVIDIA NemoClaw + Goose, tam gösterge paneli, yalnızca yerel | $0 |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | düğüm başına ayda $9 |
| **Pro** | Starter + kontrol ve değerlendirme: onaylar, araç risk politikaları, değerlendirmeler, anomali tespiti, maliyet optimize edici, OTel dışa aktarma, kurcalamaya karşı kanıtlanabilir denetim günlüğü | düğüm başına ayda $19 |

Yıllık planlar, Kurumsal ve güncel rakamlar
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** adresinde bulunur. Kendi barındırdığınız lisans
anahtarları bulut olmadan çalışır (`clawmetry license`). Tam ücretsiz/ücretli ayrımı
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) içindedir.

## Verileriniz makinenizde kalır

ClawMetry yerel oturum dosyalarını ve günlükleri okur. **`clawmetry connect` komutunu çalıştırmadıkça hiçbir oturum verisi
makinenizden çıkmaz** — hiçbir istem, yanıt, araç argümanı, dosya
içeriği veya günlük satırı. Bağlandığınızda, anlık görüntü hiçbir zaman makinenizden
çıkmayan bir anahtarla uçtan uca şifrelenir ve tarayıcınızda çözülür. Bir
düğümün anahtarı yoksa, yükleme açık metin olarak gönderilmek yerine atlanır ve hiçbir
sunucu yanıtı bunu kapatamaz.

Bağlanmadan önce varsayılan olarak çalışan, her ikisi de opt-out olan ve hiçbiri
oturum verisi taşımayan iki şey vardır: anonim bir kurulum ping'i ve
PyPI'ye karşı bir sürüm kontrolü. Varsayılan bir kurulum ayrıca açılış banner
satırı için genel IP'nizi bir kez arar. Her hedef, neyi taşıdığı ve nasıl kapatılacağı
[docs/EGRESS.md](docs/EGRESS.md) içinde listelenmiştir; kendi barındırılan, yeniden yönlendirilmiş ve
hava boşluklu (air-gapped) kurulumlar hiçbir isteğe bağlı giden çağrı yapmaz.

Şifre çözme, size sunduğumuz kod içinde, tarayıcınızda gerçekleşir. Bu eskiden
bir vaatti; şimdi kontrol edebileceğiniz bir şey. Anahtarınıza dokunan her satır
tek bir okunabilir dosyada yaşar, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
bu dosya wheel içinde gönderilir ve olduğu gibi sunulur, bir Alt Kaynak
Bütünlüğü (Subresource Integrity) hash'i ile sabitlenmiştir. Tarayıcının yayınladığımız şeyi çalıştırdığını doğrulamak için:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Bunun kanıtlamadığı şey: dosyayı yükleyen sayfayı biz sunuyoruz, dolayısıyla farklı bir
sayfa sunabiliriz. Bütünlük hash'leri sizi ele geçirilmiş bir CDN'den korur,
satıcıdan değil. Kazandığınız şey, herhangi bir değişikliğin
kasıtlı olması, sayfa kaynağında görünür olması ve herkesin PyPI'den alabileceği bir
yapıdan farklı olması gerektiğidir. Kendi barındırma veya yalnızca yerel kalma
bağımlılığı tamamen ortadan kaldırır.

## Kurulum

```bash
pip install clawmetry     # ardından: clawmetry
```

Ya da tek satırlık: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows üzerinde Python 3.8+ ve aynı makinede en az bir ajan
çalışma zamanı gerekir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

Ya da ajanın sizin için kurmasına izin verin. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
becerisi, Claude Code, Codex, Cursor, Gemini CLI, Copilot veya OpenCode'a
ClawMetry'yi kurmayı, makinedeki ajanların ne yaptığını ve ne harcadığını bildirmeyi,
istek üzerine bir oturumu durdurmayı ve riskli araç çağrılarını onay için beklemeye almayı öğretir:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokümanlar

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her adaptörün ne okuduğu ve bir çalışma zamanı nasıl eklenir |
| [Bağlam taşması](docs/CONTEXT_BLOWOUT.md) | Sağlayıcı bazında pencereler, sıkıştırma ve taşma karşılaştırması, çalışma zamanı bazında kapsama |
| [Ek yük](docs/OVERHEAD.md) | Enstrümantasyonun maliyeti, ölçülmüş, tekrarlamak için test düzeneğiyle birlikte |
| [Yetkilendirmeler](docs/ENTITLEMENTS.md) | Ücretsiz ve ücretli karşılaştırması, katman matrisi, lisans CLI'sı |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Çalıştırma öncesi geçit kontrolü, risk puanlama, telefon onayları |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri her yere aktarın, herhangi bir yerden OTLP alın |
| [Kendi ajanınızı getirin](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain uçtan uca, çalıştırılabilir örneklerle |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi oluşturduğunuz ajanlar için maliyet atfı |
| [Sohbet kanalları](docs/CHANNELS.md) | Akış'ta gösterilen sohbet adaptörleri |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sanal alanlı (sandboxed) NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | İmaj, compose, birim bağlantıları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynaktan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü-açma ping'leri ve bunların nasıl kapatılacağı |

## Ekran görüntüleri

Aşağıdaki her rakam, hiçbir şey önceden eklenmemiş, salt okunur gerçek bir makineden alınmıştır.

**Bir şeyin ne zaman yanlış gittiğini söyler, sadece ne olduğunu değil.**
Üstte iki anomali banner'ı: harcama günlük ortalamanın 7 katı hızla ilerliyor ve
4.2 katlık bir maliyet artışı. Altlarında, son 667 oturumdan 324'ü
nedenine göre ayrıştırılmış bir israf sinyali taşıyor.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Paranın nereye gittiğini her pencerede gösterir.**
Bugün $252.47, bu hafta $513.15, bu ay $1,312.92, her biri arkasındaki token'larla
ve aboneliğinizin bunun ne kadarını zaten karşıladığıyla birlikte. Bunun altında,
kurtarılabilir olarak ayrıştırılmış yaklaşık $1,128/ay ve önbellek yeniden kullanımıyla
zaten tasarruf edilmiş $17,256/ay.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Bir mesajın nasıl bir cevaba dönüştüğünü çizer.**
Canlı akış diyagramı: siz, mesajın geldiği kanal, gateway, şu anda
cevap veren model ve başvurduğu her araç. İş onlardan geçtikçe düğümler
yanıp söner.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Makinedeki her ajan, tek bir tabloda.**
Ne çalıştırdığı, son 24 saatte ve ömrü boyunca ne kadara mal olduğu, en son
ne zaman görüldüğü, kimin sahip olduğu ve bir aboneliğin faturayı karşılayıp
karşılamadığı. Burada 14 ajan, 3 oturum çalışıyor, 13'ü sessiz.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Bir turun zamanının ve parasının nereye gittiğini araç araç gösterir.**
Gerçek bir oturumun bir turu: 11.2 dakikada $1.16'ya 11 araç. Her Bash
çağrısı ve model çağrısı zaman çizelgesinde kendi çubuğunu alır, böylece
4.1 dakika süren komut ile 226ms süren komut bir bakışta ayırt edilir.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Sadece harcamayı değil, işi de notlandırır.**
Bu hafta bir A notu: 54 görev temiz döndü, 2 sorunlu görev $48.57'ye mal oldu ve
değerlendirmek için yetersiz aktiviteye sahip çalışmalar kazanç olarak sayılmak yerine
notun dışında bırakıldı. Her sorunlu çalışma kendi izine bağlantı verir.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Bağlam penceresinin neden sürekli dolduğunu gösterir.**
Son turda 1M token'lık pencerenin 715K'sı, %83.3'lük bir zirve, hepsi
bir taşma yerine proaktif olarak tetiklenen 4 sıkıştırma ve arkasındaki
her turun kullanım oranı.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tespit, siz hiçbir şey yapılandırmadan çalışır.**
Yerleşik dedektörler kurulumdan itibaren açıktır: ajan sessizleşti, telemetri
akışı durdu, maliyet artışı, token patlaması, hatalar yükseliyor, hata artışı,
bütçe eşiği, tehdit imzası eşleşti, güvenlik aracı bulgusu, güvenlik duruşu
değişti. Kendi kurallarınız bunun üzerine isteğe bağlıdır.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Riskli bir çağrıyı beklemeye almak isteğe bağlıdır ve kapalı olarak gönderilir.**
Özyinelemeli silmeler, force push'lar, sudo, gizli bilgiler, paket kurulumları ve giden
çağrıların her birinin açabileceğiniz bir kuralı vardır. Siz açana kadar, ClawMetry izler
ve hiçbir şeyi değiştirmez. Biri açıldığında, eşleşen çağrılar burada (ya da telefonunuzda)
onay veya red için bekler.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Daha fazlası, çalışma zamanı bazında: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
