<!-- i18n-src:8f42d460a973 -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ajanınızın düşünme sürecini görün.** **14 farklı AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 10 tane daha. Tüm ajan filonuz için tek bir kontrol paneli.

> 🌐 **Bu belgeyi şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için bir gözlemlenebilirlik aracı olarak başladı; şimdi ise **tüm ajan filonuzu** tek bir kontrol panelinde ölçümlüyor ve makinenizdeki her çalışma zamanını otomatik olarak algılıyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw ve NemoClaw, açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ise ClawMetry Cloud veya kendi sunucunuzda barındırılan bir Pro lisansı ile etkinleşir. Çalışma zamanını üst bilgiden değiştirin; maliyet, token, araçlar, izler gibi her sekme o çalışma zamanına göre yeniden kapsamlanır. Tam ücretsiz/ücretli ayrımı, katman matrisi, `/api/entitlement` şeması ve `clawmetry license` CLI'ı için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Mesajların kanallar, beyin, araçlar arasında akışını ve geri dönüşünü gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, aktivite ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık dökümlerle token ve maliyet takibi
- **Sessions** — Model, token, son aktivite bilgisiyle aktif ajan oturumları
- **Crons** — Durum, sonraki çalışma zamanı, süre bilgisiyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, günlük notları göz atma
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe limitleri, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirir
- **Approvals** — Yıkıcı silme işlemlerini, force push'ları, veritabanı değişikliklerini, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onay arkasında kapı altına alır

## Ekran Görüntüleri

### 🧠 Brain — Canlı ajan olay akışı
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token kullanımı ve oturum özeti
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Gerçek zamanlı araç çağrısı akışı
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Model ve oturuma göre maliyet dökümü
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Çalışma alanı dosya tarayıcısı
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Duruş ve denetim kaydı
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Bütçe limitleri, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / E-posta'ya webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onay arkasında kapı altına alın; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Kurulum

**Tek satırlık (önerilen):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Kaynak koddan:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Ön Yüz Geliştirme

v2 React uygulaması `frontend/` dizininde yer alır ve Flask sunucusu v2 etkinken başlatıldığında `/v2` adresinde sunulur.

Geliştirme yaparken iki terminal kullanın:

```bash
# Terminal 1: :8900 üzerinde Flask API/sunucu
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: :5173 üzerinde Vite geliştirme sunucusu
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini `http://localhost:8900` adresine yönlendirir, böylece React uygulaması ekstra CORS ayarına gerek kalmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilen paketi (bundle) oluşturmak için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` dizinine yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry yalnızca OpenClaw değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine dönüştüren özel bir okuyucu bağdaştırıcısı (adapter) ile gelir; arka plan servisi (daemon) bunları çalışma zamanı etiketiyle aynı DuckDB deposuna + bulut anlık görüntüsüne alır ve Session replay sekmesi birden fazla çalışma zamanı bulunduğunda bir **çalışma zamanı değiştirici** gösterir. Tam matris + çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md) dosyasına, OpenClaw ailesi girişi için [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) dosyasına bakın.

| Çalışma Zamanı / Ajan | Durum | Notlar |
|---|---|---|
| **OpenClaw** | Yerel (Native) | Referans çalışma zamanı, otomatik algılanır |
| **PicoClaw** | Beta bağdaştırıcı | Düz `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Dökümler, model, araç çağrıları. |
| **NanoClaw** | Beta bağdaştırıcı | Oturum başına SQLite (`data/v2-sessions`). Dökümler + mesaj sayıları. |
| **Hermes** | Beta bağdaştırıcı | SQLite `~/.hermes/state.db`. Dökümler, model, token/maliyet. |
| **Claude Code** | Beta bağdaştırıcı | JSONL `~/.claude/projects/.../<id>.jsonl`. Dökümler, model, araç çağrıları + düşünme, token kullanımı. |
| **Codex** | Beta bağdaştırıcı | Rollout JSONL `~/.codex/sessions/...`. Dökümler, model, araç çağrıları, token kullanımı. |
| **Cursor** | Beta bağdaştırıcı | SQLite `state.vscdb`. Sohbet/composer dökümleri, model. |
| **Aider** | Beta bağdaştırıcı | Proje başına `.aider.chat.history.md`. Dökümler, model, token sayıları. |
| **Goose** | Beta bağdaştırıcı | SQLite `~/.local/share/goose`. Dökümler, model, araç çağrıları, token toplamları. |
| **opencode** | Beta bağdaştırıcı | SQLite `~/.local/share/opencode`. Dökümler, model, araç çağrıları, token + maliyet. |
| **Qwen Code** | Beta bağdaştırıcı | JSONL `~/.qwen/projects/.../chats`. Dökümler, model, araç çağrıları, token kullanımı. |
| **Pi** | Beta bağdaştırıcı | JSONL `~/.pi/agent/sessions`. Dökümler, model, araç çağrıları, token + maliyet. |
| **Deep Agents** | Beta bağdaştırıcı | SQLite `~/.deepagents/.state/sessions.db`. Dökümler, model, araç çağrıları, token + maliyet. |

"Beta bağdaştırıcı", ClawMetry'nin o çalışma zamanının gerçek disk üzerindeki biçimi için bir okuyucu sunduğu anlamına gelir; her biri gerçek bir makinede gerçek bir kurulum üzerinde inşa edilip doğrulanmıştır (bkz. `tests/fixtures/runtimes/<rt>/`). Bağdaştırıcılar salt okunurdur; her biri çalışma zamanının diskte gerçekte ne sakladığı konusunda dürüsttür (örn. PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici temiz bir derinlemesine inceleme için oturumlar görünümünü tek birine daraltır.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet atfı

Yukarıdaki çalışma zamanlarının hepsi oturumları diske yazar. Sizin kendi **üretim ajanınız** ise, yani OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B veya sade bir `httpx` döngüsü üzerine kurduğunuz ajan, bunu yapmaz. ClawMetry'nin sıfır yapılandırmalı interceptor'ı, `httpx`/`requests` üzerinde monkey-patching yaparak yine de bu ajanın LLM çağrılarını (maliyet, token, gecikme, hatalar) yakalar:

```python
import clawmetry.track            # interceptor'ı etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürünü adlandır

# ...ajanınız normal şekilde çalışır; artık her LLM çağrısı izlenip atfediliyor.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her çağrıyı **adlandırılmış bir kaynak** ile etiketler; böylece çalıştırdığınız her ürün, kontrol panelindeki Overview sekmesinin **🔌 Döngü dışı kaynaklar** kartında kendi başına, maliyeti atfedilebilir bir satır olarak görünür: ajan başına çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak ayarlanmadıysa? Çağrılar yine izlenir; kart sadece gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı bağdaştırıcılarının beslediği aynı veri katmanıdır (DuckDB → bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar da diğer her şey gibi uçtan uca şifrelenerek buluta senkronize edilir.

## OpenTelemetry — satıcıdan bağımsız, izlerinizi (traces) istediğiniz yere gönderin

ClawMetry, **GenAI semantik kurallarını** kullanarak her iki yönde de **OpenTelemetry** konuşur; böylece ajan izleriniz asla tek bir araca kilitlenmez.

Her oturumu; LLM çağrıları, araçlar, alt ajanlar, tokenlar, maliyet dahil; OTLP/HTTP GenAI span'leri olarak herhangi bir koleksiyoncuya (Datadog, Grafana, Honeycomb veya kendi OTel Collector'ınıza) **dışa aktarın**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# eşdeğer olarak:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Kimlik doğrulama başlıkları ve yoklama (poll) aralığı isteğe bağlı ortam değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ekstra HTTP başlıkları
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # saniye (varsayılan 60)
```

**İçe aktarma (Ingest)** — yerleşik OTLP alıcısı, başka herhangi bir yerden gelen izleri ve metrikleri `/v1/traces` ve `/v1/metrics` adreslerinde kabul eder (protobuf ile içe aktarma için `pip install clawmetry[otel]`).

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry kontrol panelini **hem de** verinizi ekibinizin zaten kullandığı herhangi bir arka uçta elde edersiniz; kilitlenme yok, kurulacak ikinci bir ajan yok.

## Yapılandırma

Çoğu kişinin herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma alanınızı, loglarınızı, oturumlarınızı ve cron'larınızı otomatik olarak algılar.

Özelleştirmeniz gerekiyorsa:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Yalnızca localhost'a bağlan
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesindeki adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı aktivite gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten kurulmuş olan kanallar Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj sayılarıyla canlı bir sohbet balonu görünümü görebilirsiniz.

| Kanal | Durum | Canlı Açılır Pencere | Notlar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Tam | ✅ | Mesajlar, istatistikler, 10 sn yenileme |
| 💬 **iMessage** | ✅ Tam | ✅ | `~/Library/Messages/chat.db` dosyasını doğrudan okur |
| 💚 **WhatsApp** | ✅ Tam | ✅ | WhatsApp Web (Baileys) üzerinden |
| 🔵 **Signal** | ✅ Tam | ✅ | signal-cli üzerinden |
| 🟣 **Discord** | ✅ Tam | ✅ | Sunucu (guild) + kanal algılama |
| 🟪 **Slack** | ✅ Tam | ✅ | Çalışma alanı + kanal algılama |
| 🌐 **Webchat** | ✅ Tam | ✅ | Yerleşik web arayüzü oturumları |
| 📡 **IRC** | ✅ Tam | ✅ | Terminal tarzı balon arayüzü |
| 🍏 **BlueBubbles** | ✅ Tam | ✅ | BlueBubbles REST API üzerinden iMessage |
| 🔵 **Google Chat** | ✅ Tam | ✅ | Chat API webhook'ları üzerinden |
| 🟣 **MS Teams** | ✅ Tam | ✅ | Teams bot eklentisi üzerinden |
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi sunucunuzda barındırılan takım sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkezi olmayan, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkezi olmayan NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry, `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları render eder. Manuel kurulum gerekmez.

## Docker ile Dağıtım

ClawMetry'yi bir konteyner içinde çalıştırmak mı istiyorsunuz? Sorun değil! 🐳

**Docker ile hızlı başlangıç:**

```bash
# İmajı oluşturun
docker build -t clawmetry .

# Varsayılan ayarlarla çalıştırın
docker run -p 8900:8900 clawmetry

# Veya ajanınızın veri dizinini bağlayın (gösterilen: OpenClaw'ın ~/.openclaw'ı)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose örneği:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **Not:** Docker içinde çalıştırırken, ClawMetry'nin kurulumunuzu otomatik algılayabilmesi için ajanınızın veri + log dizinlerini (örn. `~/.openclaw`, `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip ile otomatik olarak kurulur)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi veya Deep Agents (veya Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, OpenClaw ajanlarını sandbox'lanmış OpenShell konteynerleri içinde çalıştıran NVIDIA'nın kurumsal güvenlik sarmalayıcısı olan [NemoClaw](https://github.com/NVIDIA/NemoClaw)'u otomatik olarak algılar.

Çoğu durumda ekstra yapılandırma gerekmez. Sync arka plan servisi, oturum dosyalarının ana makinede `~/.openclaw/` içinde mi yoksa bir OpenShell konteyneri içinde mi bulunduğunu otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili (binary) algılama** — `nemoclaw` CLI'ını kontrol eder ve sandbox bilgisini almak için `nemoclaw status` komutunu çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için tarar, ardından oturumları birim bağlantıları (volume mounts) veya `docker cp` üzerinden okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut kontrol panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir; böylece bunları standart OpenClaw oturumlarından bir bakışta ayırt edebilirsiniz.

### Önerilen kurulum: ANA MAKİNE üzerinde sync arka plan servisi

En iyi deneyim için, ClawMetry'nin sync arka plan servisini sandbox içinde değil, **ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından kaçınmanızı sağlar.

```bash
# Ana makinede (sandbox'ın dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync arka plan servisi, çalışan herhangi bir OpenShell konteyneri içindeki oturumları otomatik olarak bulur.

### İsteğe bağlı: açık sandbox adı

Otomatik algılama çalışmazsa, ClawMetry'yi doğru sandbox'a yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sandbox içinde çalıştırma (ileri düzey)

Sync arka plan servisini **OpenShell sandbox'ının içinde** çalıştırmanız gerekiyorsa, ClawMetry ingest API'sine erişebilmesi için NemoClaw ağ politikanıza şu egress kuralını ekleyin:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Şununla uygulayın:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Portlar ve uç noktalar

| Uç Nokta | Port | Protokol | Gerekli mi |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Evet (sync arka plan servisi → bulut) |
| `localhost:8900` | 8900 | HTTP | Evet (yerel kontrol paneli arayüzü) |
| Docker soketi (`/var/run/docker.sock`) | — | Unix soketi | Konteyner oturumu keşfi için |

Sync arka plan servisi yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları yapar. Hiçbir gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**'na bakın.

## Test

Bu proje BrowserStack ile test edilmiştir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `clawmetry` CLI'ını yeni bir makinede ilk kez çalıştırdığınızda `https://app.clawmetry.com/api/install` adresine tek bir anonim "ilk çalıştırma" pingi gönderir. Bunu kurulumları saymak (bir OSS projesi için sahip olduğumuz tek pazarlama metriği) ve kullanıcılarımızın hangi ajan çerçevelerini kurduğunu öğrenmek için kullanıyoruz.

**Kurulum başına tam olarak bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` konumunda saklanan rastgele UUID | tekrar önleme (dedup); e-postanız veya api_key'inizle ilişkilendirilmez |
| `version` | `0.12.167` | hangi sürümlerin kullanımda olduğu |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürümü destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | sırada hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediğimiz şeyler**: IP (bulut, sunucu tarafında istekten ülke kodunu türetir, ardından IP'yi atar), ana bilgisayar adı (hostname), kullanıcı adı, çalışma alanı yolu, dosya içerikleri, api_key'iniz, e-postanız, kişisel olarak tanımlanabilir veya çalışma alanına özgü herhangi bir şey. Aktarım (wire) yükü [`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında denetlenebilir.

**Devre dışı bırakma** (aşağıdakilerden herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # kabuk (shell) başına
export DO_NOT_TRACK=1                          # araçlar arası W3C standardı
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işaretçisi
```

Buradaki bir ağ hatası `clawmetry`'nin çalışmasını asla engellemez; ping, arka plan (daemon) iş parçacığında 3 sn zaman aşımıyla ateşle-ve-unut (fire-and-forget) şeklindedir.

## Yıldız Geçmişi

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lisans

MIT

---

<p align="center">
  <strong>🦞 Ajanınızın düşünme sürecini görün</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçasıdır</sub>
</p>
