<!-- i18n-src:c99ac0512cae -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Bir ajan ilerleme kaydetmeden yüz tane araç çağrısı yapabilir.** ClawMetry,
kodlama ajanlarınızın zaten yazdığı oturum dosyalarını okur ve zaman çizelgesini,
araç çağrılarını ve çalışma zamanının gösterdiği token ile maliyet verilerini tek
bir görünümde toplar; böylece çalışan uzun bir koşuyu takılı kalmış olandan ayırt edebilirsiniz.

**33 AI ajan çalışma zamanıyla** çalışır: Claude Code, OpenAI Codex, Hermes, OpenClaw ve 29 tane daha. Tüm ajan filonuz için tek bir pano. ([tam liste](SUPPORTED_RUNTIMES.txt), katalogdan üretilmiştir.)

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır. Sıfır yapılandırma: zaten sahip olduğunuz
ajan çalışma zamanlarını bulur, onları salt okunur olarak okur ve nasıl çalıştıkları konusunda hiçbir şeyi değiştirmez.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Kurmadan önce

| | |
|---|---|
| **Ne yapar** | Ajanlarınızın zaten yazdığı oturum dosyalarını ve günlükleri okur. SDK yok, kod değişikliği yok, uygulamanızda enstrümantasyon yok. |
| **Ne görürsünüz** | Oturum zaman çizelgesi, araç araç tekrar oynatma, token ve maliyet dökümü ve çalışma zamanı bazında trajektori sinyalleri (döngüye girme, tekrarlanan hatalar). |
| **Ücretsiz olan** | `pip install clawmetry`, hesap, anahtar veya ağ çağrısı gerektirmeden **OpenClaw, NVIDIA NemoClaw, Goose ve Qwen Code**'u okur. Diğer 28 tanesi -- Claude Code, Codex, Cursor ve geri kalanı -- 7 günlük deneme veya bir planla gelen kapalı kaynaklı `clawmetry-pro` eklentisi tarafından okunur; tam ayrım için bkz. [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Nasıl başlanır** | `pip install clawmetry && clawmetry`, ardından localhost:8900 adresini açın. Bu makinede henüz ajan yok mu? `clawmetry --sample` üç etiketli sentetik oturumla açılır. |
| **Makinenizden ne çıkar** | `clawmetry connect` çalıştırmadığınız sürece hiçbir oturum verisi çıkmaz. Varsayılan olarak çalışan iki şey vardır, ikisi de devre dışı bırakılabilir ve ikisi de oturum içeriği taşımaz: anonim bir kurulum pingi ve bir PyPI sürüm kontrolü. Her hedef, yorumları okumak yerine bir ağ yakalamasından yeniden oluşturularak [docs/EGRESS.md](docs/EGRESS.md) içinde envanterlenmiştir. |

Çıktıyı değerlendirmeden önce bilinmesi gereken iki sınırlama var: çalışma zamanları
çok farklı veriler sunar (bazıları hiç maliyet yayınlamaz -- hangilerinin yaptığını
[matris](docs/compatibility.md) çalışma zamanı bazında söyler) ve bir eylemi gözlemlemek
onu engelleyebilmekle aynı şey değildir (çalışma zamanı bazında [hangi kontrollerin gerçek olduğu](docs/APPROVALS.md)).


## 33 ajan çalışma zamanıyla çalışır

**Açık kaynak uygulamada ücretsiz:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Ücretli planda:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Her çalışma zamanı aynı panoyu alır. Birden fazlasını aynı anda çalıştırın,
başlıktaki değiştirici her sekmeyi bunlardan birine yeniden kapsar.

Kendi ajanınızı bir SDK üzerine mi kurdunuz? Interceptor onun LLM çağrılarını da
izler. Bkz. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Neler elde edersiniz

- **Oturumlar ve dökümler**: her ajanın tur tur ne yaptığı, tekrar oynatmayla birlikte
- **Maliyet ve tokenlar**: çalışma zamanı, model, oturum ve gün bazında, anormallik işaretleriyle birlikte
- **Akış**: kanallar, modeller ve araçlar arasında hareket eden mesajların canlı diyagramı
- **Brain**: gerçekleştiği anda akan muhakeme ve araç çağrısı olay akışı
- **Bağlam patlaması**: sağlayıcıya göre boyutlandırılmış pencere kullanımı, sıkıştırma ile zorunlu taşmanın karşılaştırılması, artı çalışma zamanı bazında *göremediğimiz* şeylerin bir haritası ([nasıl](docs/CONTEXT_BLOWOUT.md))
- **Bellek ve beceriler**: her çalışma zamanının gerçekten yüklediği dosyalar ve beceriler
- **Sağlık ve günlükler**: disk, bellek, hata oranları, hız sınırları, canlı günlük akışı
- **Uyarılar**: bütçe sınırları, hata artışları, ajan çevrimdışı durumu; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirilir
- **Onaylar**: riskli araç çağrılarını *çalışmadan önce* duraklatın ve telefonunuzdan onaylayın ([nasıl](docs/APPROVALS.md))

## Bağlam patlaması ve izlemenin maliyeti

Herhangi bir ajan karşılaştırma aracına güvenmeden önce yanıtlanmaya değer iki soru.

**Çalışma zamanları arasında bağlam penceresi patlamasını nasıl ele alıyor?**

Bir kullanım yüzdesi, ancak böldüğü sayı kadar dürüsttür. ClawMetry, pencereyi
[okuyabileceğiniz ve PR gönderebileceğiniz bir tablodan](clawmetry/context_windows.py)
sağlayıcı bazında boyutlandırır; bu tablo Anthropic, OpenAI, Google, xAI, DeepSeek,
Kimi, Qwen, Mistral, Llama ve GLM'yi kapsar. 33 çalışma zamanının tamamını tek bir
satıcının cetveliyle ölçmez. Bu önemlidir: Anthropic'in 200K'sına karşı puanlanan
300K'lık bir GPT-5 turu, GPT-5'in 400K'sının aslında %75'indeyken ">%100, patlamış"
olarak okunur. Aynı cetvel, gerçekten taşmış 130K'lık bir DeepSeek turunu rahat bir
%65 olarak gizler.

Her pencere kendi kökenini taşır: `model_table`, `explicit_marker`,
`observed_floor` veya modeli bilmediğimizde dürüst bir `default`. Bir tahmine
dayalı gösterge, bir aramaya dayalı olanla aynı otoriteyle hiçbir zaman render edilmez.

ClawMetry bazı çalışma zamanlarında sıkıştırma olaylarını yalnızca kısmen görebilir.
Bu yüzden `GET /api/context-coverage`, çalışma zamanı bazında, bir **sıfırın
"temiz çalıştı" mı yoksa "kör durumdayız" mı** anlamına geldiğini raporlar.
Aslında kör anlamına gelen bir `0` bunu söyler.
[Tam ayrıntı](docs/CONTEXT_BLOWOUT.md)

**Enstrümantasyonun maliyeti nedir?**

| Yol | Ajanınıza eklenen | Varsayılan mı? |
|---|---|---|
| Oturum dosyası izleme (33 çalışma zamanının tamamı) | **0**. Ayrı bir işlem, ajanınızda ClawMetry kodu yok | açık |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | LLM çağrısı başına **+0,44 ms**, yani 5 saniyelik bir çağrının %0,009'u | kapalı |
| Araç öncesi hook kapısı (ısınmış önbellek) | 36 ms'lik bir yorumlayıcı tabanının üzerinde, kapıdan geçen araç çağrısı başına **+44 ms** | kapalı |
| Zorunlu kılma proxy'si | LLM çağrısı başına **+9,7 ms** | kapalı |

Daemon ana bilgisayar maliyeti: saniyede **2.762 olay** alım, olay başına
diskte **710 bayt** (100 bin olay için 67,7 MB) ve yoğun bir kurulumda sürekli
olarak **bir çekirdeğin ~%12'si**. Bu son sayı kendi beyan ettiğimiz %5-10
bütçesinin üzerinde olduğundan, sayfadan çıkarılmak yerine kovalanması gereken
bir hata olarak yayınlanmıştır.

Bir Apple M2 Pro üzerinde `benchmarks/overhead.py` ile ölçülmüştür. Kabuk, her
koşulu ayrı bir işlemde çalıştırır, sırasını değiştirir ve **turlar işaretinde
anlaşmazsa bir sayı yazdırmayı reddeder**. Kendi makinenizde bir dakikada çalıştırın:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Hook kapıları ve zorunlu kılma proxy'si dahil her yol ölçülür ve kabuk CI'da
Linux, macOS ve Windows üzerinde çalışır. Bilinmeye değer iki sonuç: proxy
Windows'ta Linux'tekinden yaklaşık yedi kat daha pahalıya mal oluyor ve daemon
şu anda kendi %5-10 bütçemizin üzerinde, bir çekirdeğin yaklaşık %12'sini sürekli
olarak kullanıyor. Ham JSON, yöntem ve hâlâ ölçülmemiş olanlar
[docs/OVERHEAD.md](docs/OVERHEAD.md) içindedir.

## Fiyatlandırma

| Plan | Neyi kapsar | Fiyat |
|---|---|---|
| **Ücretsiz** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, tam pano, yalnızca yerel | $0 |
| **Starter** | Yukarıdaki diğer tüm çalışma zamanları, filo görünümü, bulut senkronizasyonu | düğüm başına ayda 9$ |
| **Pro** | Starter + kontrol ve değerlendirme: onaylar, araç risk politikaları, değerlendirmeler, anormallik tespiti, maliyet optimize edici, OTel dışa aktarımı, kurcalamaya dayanıklı denetim günlüğü | düğüm başına ayda 19$ |

Yıllık planlar, Kurumsal ve güncel rakamlar
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** adresindedir. Kendi
sunucunuzda barındırılan lisans anahtarları bulut olmadan çalışır
(`clawmetry license`). Ücretsiz/ücretli ayrımının tam hali
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) içindedir.

## Verileriniz makinenizde kalır

ClawMetry yerel oturum dosyalarını ve günlükleri okur. **`clawmetry connect`
çalıştırmadığınız sürece hiçbir oturum verisi kutunuzdan çıkmaz** -- istemler,
yanıtlar, araç argümanları, dosya içerikleri veya günlük satırları dahil değil.
Bağlandığınızda, anlık görüntü, makinenizden asla çıkmayan bir anahtarla uçtan
uca şifrelenir ve tarayıcınızda şifresi çözülür. Bir düğümün anahtarı yoksa,
yükleme açık metin olarak gönderilmek yerine atlanır ve hiçbir sunucu yanıtı
bunu kapatamaz.

Bağlanmadan önce varsayılan olarak çalışan iki şey vardır, ikisi de devre dışı
bırakılabilir ve ikisi de oturum verisi taşımaz: anonim bir kurulum pingi ve
PyPI'ye karşı bir sürüm kontrolü. Varsayılan bir kurulum ayrıca başlangıç
banner satırı için genel IP adresinizi bir kez sorgular. Her hedef, taşıdığı
şey ve nasıl kapatılacağı [docs/EGRESS.md](docs/EGRESS.md) içinde listelenmiştir;
kendi sunucunuzda barındırılan, yeniden yönlendirilmiş ve hava boşluklu
kurulumlar hiçbir isteğe bağlı giden çağrı yapmaz.

Şifre çözme işlemi, size sunduğumuz kod içinde, tarayıcınızda gerçekleşir. Bu
bir zamanlar bir vaattik; artık kontrol edebileceğiniz bir şey. Anahtarınıza
dokunan her satır, wheel içinde gönderilen ve bir Subresource Integrity hash'iyle
sabitlenerek olduğu gibi sunulan tek okunabilir dosyada,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), yer alır.
Tarayıcının yayınladığımız şeyi çalıştırdığını doğrulamak için:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Bunun kanıtlamadığı şey şu: dosyayı yükleyen sayfayı biz sunuyoruz, dolayısıyla
farklı bir sayfa da sunabiliriz. Bütünlük hash'leri sizi ele geçirilmiş bir
CDN'den korur, satıcıdan değil. Kazandığınız şey, herhangi bir değiştirmenin
kasıtlı olması, sayfa kaynağında görünür olması ve herkesin PyPI'den indirebileceği
bir yapıttan farklı olması gerektiğidir. Kendi sunucunuzda barındırmak veya
yalnızca yerel kalmak bu bağımlılığı tamamen ortadan kaldırır.

## Kurulum

```bash
pip install clawmetry     # ardından: clawmetry
```

Ya da tek satırlık komut: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux veya Windows üzerinde Python 3.8+ ve aynı makinede en az bir ajan
çalışma zamanı gerektirir. Docker talimatları: [docs/DOCKER.md](docs/DOCKER.md).

Ya da ajanın sizin için kurmasına izin verin. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
becerisi, Claude Code, Codex, Cursor, Gemini CLI, Copilot veya OpenCode'a
ClawMetry'yi kurmayı, makinedeki ajanların ne yaptığını ve ne harcadığını
raporlamayı, istek üzerine bir oturumu durdurmayı ve riskli araç çağrılarını
onay için beklemeye almayı öğretir:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokümanlar

| | |
|---|---|
| [Çalışma zamanı uyumluluğu](docs/compatibility.md) | Her adaptörün ne okuduğu ve bir çalışma zamanının nasıl ekleneceği |
| [Bağlam patlaması](docs/CONTEXT_BLOWOUT.md) | Sağlayıcı bazında pencereler, sıkıştırmaya karşı taşma, çalışma zamanı bazında kapsam |
| [Ek yük](docs/OVERHEAD.md) | Enstrümantasyonun maliyeti, ölçülmüş, yeniden üretmek için kabukla birlikte |
| [Haklar (Entitlements)](docs/ENTITLEMENTS.md) | Ücretsiz'e karşı ücretli, katman matrisi, lisans CLI'si |
| [Onaylar ve politikalar](docs/APPROVALS.md) | Çalıştırma öncesi kapılama, risk puanlama, telefon onayları |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | İzleri her yere dışa aktarın, her yerden OTLP alın |
| [Kendi ajanınızı getirin](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain uçtan uca, çalıştırılabilir örneklerle |
| [SDK izleme](docs/SDK_TRACKING.md) | Kendi oluşturduğunuz ajanlar için maliyet atfı |
| [Sohbet kanalları](docs/CHANNELS.md) | Akış'ta gösterilen sohbet adaptörleri |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandbox'lanmış NVIDIA NemoClaw kurulumları |
| [Docker](docs/DOCKER.md) | Image, compose, birim bağlamaları |
| [Mimari](ARCHITECTURE.md) · [Geliştirme](docs/DEVELOPMENT.md) | İçeride nasıl çalıştığı; kaynaktan çalıştırma |
| [Telemetri](docs/TELEMETRY.md) | Anonim kurulum ve masaüstü açma pingleri ve bunların nasıl kapatılacağı |

## Ekran görüntüleri

Aşağıdaki her rakam, hiçbir şey ekilmemiş, salt okunur gerçek bir makineden alınmıştır.

**Sadece ne olduğunu değil, bir şeyin yanlış gittiğini de söyler.**
Üstte iki anormallik banner'ı: günlük ortalamanın 7 katı çalışan harcama ve
4,2 kat maliyet artışı. Altlarında, nedene göre ayrıştırılmış, israf sinyali
taşıyan 667 son oturumun 324'ü.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Paranın nereye gittiğini her pencerede gösterir.**
Bugün 252,47$, bu hafta 513,15$, bu ay 1.312,92$; her biri arkasındaki
tokenlarla ve aboneliğinizin bunun ne kadarını zaten karşıladığıyla birlikte.
Altında, ayda yaklaşık 1.128$ geri kazanılabilir olarak ayrıştırılmış ve
önbellek yeniden kullanımıyla ayda zaten 17.256$ tasarruf edilmiş.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Bir mesajın nasıl yanıta dönüştüğünü çizer.**
Canlı akış diyagramı: siz, mesajın geldiği kanal, gateway, şu anda yanıtlayan
model ve uzandığı her araç. İş düğümlerden geçerken düğümler yanıyor.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Makinedeki her ajan, tek bir tabloda.**
Ne çalıştırdığı, son 24 saatte ve ömrü boyunca ne kadara mal olduğu, en son
ne zaman görüldüğü, kime ait olduğu ve bir aboneliğin faturayı karşılayıp
karşılamadığı. Burada 14 ajan, 3 oturum çalışıyor, 13'ü sessiz.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Bir turun zamanının ve parasının nereye gittiğini araç araç gösterir.**
Gerçek bir oturumun bir turu: 11,2 dakikada 11 araç, 1,16$ karşılığında. Her
Bash çağrısı ve model çağrısı zaman çizelgesinde kendi çubuğunu alır; böylece
4,1 dakika süren komutla 226ms süren komut bir bakışta ayırt edilir.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Yalnızca harcamayı değil, işi de notlandırır.**
Bu hafta bir A notu: 54 görev temiz döndü, 2 sorunlu görev 48,57$'a mal oldu
ve değerlendirmek için çok az etkinliği olan koşullar kazanç olarak sayılmak
yerine notun dışında bırakıldı. Her sorunlu koşu kendi izine bağlanır.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Bağlam penceresinin neden sürekli dolduğunu gösterir.**
Son turda 1M tokenlık pencerenin 715K'sı, %83,3 zirve, hepsi taşma yerine
proaktif olarak tetiklenen 4 sıkıştırma ve bunun arkasındaki her turun kullanımı.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Tespit, siz hiçbir şey yapılandırmadan çalışır.**
Yerleşik dedektörler kurulumdan itibaren açıktır: ajan sessizleşti, telemetri
akışı durdu, maliyet artışı, token patlaması, hatalar tırmanıyor, hata artışı,
bütçe eşiği, tehdit imzası eşleşti, güvenlik aracı bulgusu, güvenlik duruşu
değişti. Kendi kurallarınız bunun üzerine isteğe bağlıdır.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Riskli bir çağrıyı beklemeye almak isteğe bağlıdır ve kapalı gönderilir.**
Özyinelemeli silmeler, zorla push'lar, sudo, sırlar, paket kurulumları ve
giden çağrıların her birinin açabileceğiniz bir kuralı vardır. Siz açana kadar
ClawMetry sadece izler ve hiçbir şeyi değiştirmez. Biri açıldığında, eşleşen
çağrılar burada (ya da telefonunuzda) onay ya da ret için bekler.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Çalışma zamanı bazında daha fazlası: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Tanınma

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star Geçmişi

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
