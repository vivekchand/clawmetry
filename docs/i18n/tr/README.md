<!-- i18n-src:12b97259721e -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Bir ajan, ilerleme kaydetmeden yüz araç çağrısı yapabilir.** ClawMetry,
kodlama ajanlarınızın zaten yazdığı oturum dosyalarını okur ve zaman çizelgesini,
araç çağrılarını ve çalışma zamanının ortaya koyduğu her türlü token ve maliyet
verisini tek bir görünümde birleştirir; böylece işleyen uzun bir çalışmayı
takılıp kalmış olandan ayırt edebilirsiniz.

**31 AI ajan çalışma zamanıyla** çalışır — Claude Code, OpenAI Codex, Hermes, OpenClaw ve 27 tane daha. Tüm ajan filonuz için tek bir kontrol paneli. ([tam liste](SUPPORTED_RUNTIMES.txt), katalogdan üretilir.)

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır. Sıfır yapılandırma: zaten sahip
olduğunuz ajan çalışma zamanlarını bulur, onları salt okunur olarak okur ve
çalışma biçimlerinde hiçbir şeyi değiştirmez.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Kurmadan önce

| | |
|---|---|
| **Ne yapar** | Ajanlarınızın zaten yazdığı oturum dosyalarını ve günlükleri okur. SDK yok, kod değişikliği yok, uygulamanızda enstrümantasyon yok. |
| **Ne görürsünüz** | Oturum zaman çizelgesi, araç araç yeniden oynatma, token ve maliyet dökümü ve yörünge sinyalleri (döngüye girme, tekrarlanan başarısızlıklar) — çalışma zamanı başına. |
| **Ücretsiz olan** | `pip install clawmetry`, hesap, anahtar veya ağ çağrısı olmadan **OpenClaw, NVIDIA NemoClaw ve Goose**'u okur. Diğer 27 tanesi — Claude Code, Codex, Cursor ve geri kalanı — kapalı kaynaklı `clawmetry-pro` bileşeni tarafından okunur; bu bileşen 7 günlük deneme sürümü veya bir planla birlikte gelir — tam ayrım için bkz. [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Nasıl başlanır** | `pip install clawmetry && clawmetry`, ardından localhost:8900 adresini açın. Bu makinede henüz ajan yok mu? `clawmetry --sample`, etiketlenmiş üç sentetik oturumla açılır. |
| **Makinenizden ne çıkar** | `clawmetry connect` komutunu çalıştırmadığınız sürece hiçbir oturum verisi çıkmaz. Varsayılan olarak iki şey çalışır, ikisi de devre dışı bırakılabilir ve hiçbiri oturum içeriği taşımaz: anonim bir kurulum pingi ve bir PyPI sürüm kontrolü. Her hedef, yorumları okuyarak değil bir ağ trafiği yakalamasından yeniden oluşturularak [docs/EGRESS.md](docs/EGRESS.md) dosyasında envanterlenmiştir. |

Çıktıyı değerlendirmeden önce bilinmesi gereken iki sınır var: çalışma zamanları
çok farklı veriler ortaya koyar (bazıları hiç maliyet yayımlamaz — [matris](docs/compatibility.md)
hangisinin, çalışma zamanı başına, olduğunu belirtir) ve bir eylemi gözlemlemek
onu engelleyebilmekle aynı şey değildir ([hangi kontroller gerçek, çalışma zamanı başına](docs/APPROVALS.md)).


## 31 çalışma zamanıyla çalışır

**Açık kaynak uygulamada ücretsiz:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Ücretli planda:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Her çalışma zamanı aynı kontrol panelini alır. Birkaçını aynı anda çalıştırın,
üstteki geçiş anahtarı her sekmeyi seçtiğiniz çalışma zamanına yeniden kapsar.

Kendi ajanınızı bir SDK üzerine mi kurdunuz? İnterceptor onun LLM çağrılarını da
izler. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın adım adım ne yaptığı, yeniden oynatma ile
- **Maliyet ve token**: çalışma zamanı, model, oturum ve gün bazında, anomali işaretleriyle
- **Akış**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Beyin**: gerçekleştiği anda akan akıl yürütme ve araç çağrısı olay akışı
- **Bağlam taşması**: sağlayıcı başına boyutlandırılmış pencere kullanımı, sıkıştırma ile zorunlu taşma karşılaştırması, ayrıca çalışma zamanı başına *göremediğimiz* şeylerin haritası ([nasıl](docs/CONTEXT_BLOWOUT.md))
- **Bellek ve beceriler**: her çalışma zamanının gerçekte yüklediği dosyalar ve beceriler
- **Sağlık ve günlükler**: disk, bellek, hata oranları, hız sınırları, canlı günlük akışı
- **Uyarılar**: bütçe tavanları, hata sıçramaları, ajan çevrimdışı; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirilir
- **Onaylar**: riskli araç çağrılarını çalıştırılmadan *önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Bağlam taşması ve izlemenin maliyeti

Herhangi bir ajan karşılaştırma aracına güvenmeden önce yanıtlamaya değer iki soru.

**Çalışma zamanları arasında bağlam penceresi taşmasını nasıl ele alıyor?**

Kullanım yüzdesi, ancak neye bölündüğü kadar dürüsttür. ClawMetry, pencereyi
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ve GLM'yi
kapsayan, [okuyup PR gönderebileceğiniz bir tablodan](clawmetry/context_windows.py)
sağlayıcı başına boyutlandırır. 31 çalışma zamanının tamamını tek bir
sağlayıcının cetveliyle ölçmez. Bu önemlidir: 300K'lık bir GPT-5 turu,
Anthropic'in 200K'sına karşı puanlandığında ">%100, taşmış" okunur; oysa
gerçekte GPT-5'in 400K'sının %75'indedir. Aynı cetvel, gerçekten taşmış olan
130K'lık bir DeepSeek turunu rahat bir %65 olarak gizler.

Her pencere kendi kökenini taşır: `model_table`, `explicit_marker`,
`observed_floor` veya modeli bilmediğimizde dürüst bir `default`. Bir tahmin
üzerine kurulu bir gösterge, hiçbir zaman bir arama üzerine kurulu olanla aynı
otoriteyle görüntülenmez.

ClawMetry, bazı çalışma zamanlarında sıkıştırma olaylarını yalnızca kısmen
görebilir. Bu yüzden `GET /api/context-coverage`, çalışma zamanı başına,
**sıfırın "temiz çalıştı" mı yoksa "kör kaldık" mı** anlamına geldiğini
bildirir. Gerçekte kör anlamına gelen bir `0` bunu söyler.
[Tüm ayrıntılar](docs/CONTEXT_BLOWOUT.md)

**Enstrümantasyonun maliyeti nedir?**

| Yol | Ajanınıza eklenen | Varsayılan mı? |
|---|---|---|
| Oturum dosyası izleme (31 çalışma zamanının tamamı) | **0**. Ayrı bir süreç, ajanınızda ClawMetry kodu yok | açık |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | LLM çağrısı başına **+0.44 ms**, ya da 5 saniyelik bir çağrının %0.009'u | kapalı |
| Ön-araç hook geçidi (sıcak önbellek) | Geçitlenen araç çağrısı başına **+44 ms**, 36 ms'lik yorumlayıcı tabanının üzerinde | kapalı |
| Uygulama proxy'si | LLM çağrısı başına **+9.7 ms** | kapalı |

Daemon ana bilgisayar maliyeti: alım için **saniyede 2.762 olay**, diskte
**olay başına 710 bayt** (100 bin olay için 67.7 MB) ve yoğun bir kurulumda
sürekli olarak **bir çekirdeğin yaklaşık %12'si**. Bu son sayı kendi
belirttiğimiz %5-10 bütçesinin üzerinde, bu yüzden sayfadan çıkarılmak yerine
peşine düşülmesi gereken bir hata olarak yayımlanıyor.

Bir Apple M2 Pro üzerinde `benchmarks/overhead.py` ile ölçülmüştür. Test düzeneği
her koşulu ayrı bir süreçte çalıştırır, sıralarını değiştirir ve **turlar işaretin
yönü konusunda anlaşmazlığa düştüğünde bir sayı yazdırmayı reddeder**. Kendi
makinenizde bir dakikada çalıştırın:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Hook geçitleri ve uygulama proxy'si dahil her yol ölçülür ve test düzeneği
CI'da Linux, macOS ve Windows'ta çalışır. Bilinmeye değer iki sonuç: proxy,
Windows'ta Linux'a göre yaklaşık yedi kat daha maliyetli ve daemon şu anda
kendi %5-10 bütçemizin üzerinde, bir çekirdeğin yaklaşık %12'sini sürekli
kullanıyor. Ham JSON, yöntem ve hâlâ ölçülmemiş olanlar
[docs/OVERHEAD.md](docs/OVERHEAD.md) dosyasındadır.

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, tam kontrol paneli, yalnızca yerel | $0 |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | düğüm başına ayda $9 |
| **Pro** | Starter + kontrol ve değerlendirme: onaylar, araç risk politikaları, değerlendirmeler, anomali tespiti, maliyet optimize edici, OTel dışa aktarım, kurcalamaya karşı kanıtlanabilir denetim günlüğü | düğüm başına ayda $19 |

Yıllık planlar, Kurumsal ve güncel rakamlar
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** adresinde yer alır.
Kendi sunucunuzda barındırılan lisans anahtarları bulut olmadan çalışır
(`clawmetry license`). Tam ücretsiz/ücretli ayrımı
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) dosyasındadır.

## Verileriniz makinenizde kalır

ClawMetry yerel oturum dosyalarını ve günlükleri okur. **`clawmetry connect`
komutunu çalıştırmadığınız sürece hiçbir oturum verisi kutunuzdan çıkmaz** —
istemler, yanıtlar, araç argümanları, dosya içerikleri veya günlük satırları
yok. Bağlandığınızda, anlık görüntü, makinenizden asla çıkmayan bir anahtarla
uçtan uca şifrelenir ve tarayıcınızda şifresi çözülür. Bir düğümün anahtarı yoksa,
yükleme açık metin olarak gönderilmek yerine atlanır ve hiçbir sunucu yanıtı
bunu kapatamaz.

Bağlanmadan önce varsayılan olarak iki şey çalışır, ikisi de devre dışı
bırakılabilir ve hiçbiri oturum verisi taşımaz: anonim bir kurulum pingi ve
PyPI'ye karşı bir sürüm kontrolü. Varsayılan bir kurulum ayrıca başlangıç
banner satırı için genel IP adresinizi bir kez sorgular. Her hedef, ne
taşıdığı ve nasıl kapatılacağı [docs/EGRESS.md](docs/EGRESS.md) dosyasında
listelenmiştir; kendi sunucusunda barındırılan, yeniden yönlendirilmiş ve
hava boşluklu kurulumlar hiçbir isteğe bağlı giden çağrı yapmaz.

Şifre çözme işlemi tarayıcınızda, size sunduğumuz kod içinde gerçekleşir. Bu
eskiden bir vaatti; şimdi kontrol edebileceğiniz bir şey. Anahtarınıza dokunan
her satır, wheel içinde gönderilen ve bir Alt Kaynak Bütünlüğü (Subresource
Integrity) karma değeriyle sabitlenmiş, olduğu gibi sunulan tek okunabilir
dosyada, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
içinde yaşar. Tarayıcının yayımladığımız şeyi çalıştırdığını doğrulamak için:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Bunun kanıtlamadığı şey şu: dosyayı yükleyen sayfayı biz sunuyoruz, dolayısıyla
farklı bir sayfa sunabiliriz. Bütünlük karmaları sizi ele geçirilmiş bir CDN'den
korur, satıcıdan değil. Kazandığınız şey, herhangi bir değişikliğin kasıtlı,
sayfa kaynağında görünür ve herkesin erişebileceği PyPI'deki bir yapıttan farklı
olması gerektiğidir. Kendi kendine barındırma veya yalnızca yerel kalma bu
bağımlılığı tamamen ortadan kaldırır.

## Kurulum

```bash
pip install clawmetry     # ardından: clawmetry
```

Veya tek satırlık kurulum: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows'ta Python 3.8+ ve aynı makinede en az bir ajan
çalışma zamanı gerektirir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

Ya da kurulumu ajana yaptırın. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
becerisi, Claude Code, Codex, Cursor, Gemini CLI, Copilot veya OpenCode'a
ClawMetry'yi kurmayı, makinedeki ajanların ne yaptığını ve ne harcadığını
raporlamayı, istek üzerine bir oturumu durdurmayı ve riskli araç çağrılarını
onay için bekletmeyi öğretir:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Belgeler

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her bağdaştırıcının okuduğu şeyler ve bir çalışma zamanı nasıl eklenir |
| [Bağlam taşması](docs/CONTEXT_BLOWOUT.md) | Sağlayıcı başına pencereler, sıkıştırma ile taşma karşılaştırması, çalışma zamanı başına kapsama |
| [Ek yük](docs/OVERHEAD.md) | Enstrümantasyonun maliyeti, ölçülmüş, yeniden üretmek için test düzeneğiyle |
| [Yetkilendirmeler](docs/ENTITLEMENTS.md) | Ücretsiz ile ücretli, katman matrisi, lisans CLI'si |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Yürütme öncesi geçitleme, risk puanlama, telefonla onaylar |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri her yere dışa aktarın, her şeyden OTLP alın |
| [Kendi ajanınızı getirin](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, uçtan uca LangChain, çalıştırılabilir örneklerle |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi kurduğunuz ajanlar için maliyet atfetme |
| [Sohbet kanalları](docs/CHANNELS.md) | Akışta gösterilen sohbet bağdaştırıcıları |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandbox'lı NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | İmaj, compose, birim bağlamaları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynaktan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü-açma pingleri ve nasıl kapatılır |

## Ekran görüntüleri

Aşağıdaki her rakam, hiçbir şey seeded edilmemiş, salt okunur gerçek bir
makineden alınmıştır.

**Bir şeyin yanlış gittiğini söyler, sadece ne olduğunu değil.**
Üstte iki anomali banner'ı: günlük ortalamanın 7 katı harcama ve 4.2 kat
maliyet sıçraması. Altlarında, son 667 oturumun 324'ü nedene göre
kalemlenmiş bir israf sinyali taşıyor.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Paranın nereye gittiğini her pencerede gösterir.**
Bugün $252.47, bu hafta $513.15, bu ay $1,312.92, her biri arkasındaki
token'larla ve aboneliğinizin şimdiden ne kadarını karşıladığıyla birlikte.
Altında, kurtarılabilir olarak kalemlenmiş yaklaşık $1,128/ay ve önbellek
yeniden kullanımıyla şimdiden tasarruf edilmiş $17,256/ay.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Bir mesajın nasıl yanıta dönüştüğünü çizer.**
Canlı akış diyagramı: siz, mesajın geldiği kanal, gateway, şu anda yanıt
veren model ve başvurduğu her araç. Düğümler, iş içlerinden geçerken yanar.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Makinedeki her ajan, tek bir tabloda.**
Ne çalıştırdığı, son 24 saatte ve yaşam boyu ne harcadığı, en son ne zaman
görüldüğü, sahibi kim ve bir aboneliğin faturayı karşılayıp karşılamadığı.
Burada 14 ajan, 3 oturum çalışıyor, 13'ü sessiz.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Bir turun zamanının ve parasının nereye gittiğini araç araç gösterir.**
Gerçek bir oturumun bir turu: 11.2 dakikada 11 araç, $1.16'ya. Her Bash
çağrısı ve model çağrısı zaman çizelgesinde kendi çubuğunu alır; böylece
4.1 dakika süren komut ile 226ms süren komut bir bakışta ayırt edilir.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Sadece harcamayı değil, işi de notlandırır.**
Bu hafta bir A notu: 54 görev temiz döndü, 2 pürüzlü görev $48.57'ye mal oldu
ve yargılanamayacak kadar az etkinliğe sahip çalışmalar kazanç olarak
sayılmak yerine notun dışında bırakıldı. Her pürüzlü çalışma kendi izine
bağlanır.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Bağlam penceresinin neden sürekli dolduğunu gösterir.**
Son turda 1M token'lık pencerenin 715K'sı, %83.3'lük bir zirve, hepsi bir
taşmada değil proaktif olarak tetiklenen 4 sıkıştırma ve arkasındaki her
turun kullanım oranı.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tespit, siz hiçbir şey yapılandırmadan çalışır.**
Yerleşik dedektörler kurulumdan itibaren açıktır: ajan sessizleşti, telemetri
akışı durdu, maliyet sıçraması, token patlaması, hatalar artıyor, hata
sıçraması, bütçe eşiği, tehdit imzası eşleşti, güvenlik aracı bulgusu,
güvenlik duruşu değişti. Kendi kurallarınız üstüne eklenmesi isteğe bağlıdır.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Riskli bir çağrıyı bekletmek isteğe bağlıdır ve kapalı olarak gönderilir.**
Özyinelemeli silmeler, zorla push'lar, sudo, gizli anahtarlar, paket
kurulumları ve giden çağrıların her biri açabileceğiniz bir kurala sahiptir.
Siz açana kadar ClawMetry izler ve hiçbir şeyi değiştirmez. Biri açıldığında,
eşleşen çağrılar burada (veya telefonunuzda) onay ya da red için bekler.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Daha fazlası, çalışma zamanı başına: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Tanınma

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
