<!-- i18n-src:48548997be76 -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ajanınızın düşüncelerini izleyin.** **12 yapay zeka ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 8 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için bir gözlemlenebilirlik aracı olarak başladı ve artık makinenizdeki her çalışma zamanını otomatik algılayarak tüm **ajan filonuzu** tek bir gösterge panelinde izler:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw ve NemoClaw açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ClawMetry Cloud veya kendi barındırdığınız bir Pro lisansıyla etkinleşir. Başlıktan çalışma zamanını değiştirdiğinizde maliyet, token, araç ve izlemeler dahil her sekme o çalışma zamanına göre yeniden kapsamlanır.

## Neler Sunulur

- **Flow** — Mesajların kanallar, beyin, araçlar ve geri dönüş boyunca aktığını gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, etkinlik ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık dökümlerle token ve maliyet takibi
- **Sessions** — Model, token ve son etkinlik bilgileriyle aktif ajan oturumları
- **Crons** — Durum, bir sonraki çalışma ve süre bilgisiyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notlara göz atın
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı tespiti; Slack, Discord, PagerDuty, Telegram ve E-posta'ya yönlendirme
- **Approvals** — Yıkıcı silmeleri, zorla göndermeleri, veritabanı mutasyonlarını, sudo işlemlerini, paket kurulumlarını ve ağ çağrılarını tek tıkla onay arkasına kilitleyin

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

### 🔐 Security — Güvenlik durumu ve denetim günlüğü
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Bütçe sınırları, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / E-posta'ya webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onay arkasına kilitleyin; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Kurulum

**Tek satır (önerilen):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Kaynaktan:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Ön Yüz Geliştirme

v2 React uygulaması `frontend/` dizininde bulunur ve Flask sunucusu v2 etkin şekilde başlatıldığında `/v2` adresinden sunulur.

Geliştirme sırasında iki terminal kullanın:

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

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini `http://localhost:8900` adresine proxy'ler; böylece React uygulaması ek CORS ayarı gerektirmeden yerel Flask sunucusuyla iletişim kurabilir.

Python paketiyle birlikte gelen paketi derlemek için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` dizinine yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry, yalnızca OpenClaw değil pek çok yapay zeka ajan çalışma zamanını izler. OpenClaw dışındaki her çalışma zamanı, yerel oturum formatını ClawMetry'nin birleşik yapılarına dönüştüren özel bir okuyucu adaptörüyle gelir; daemon bunları çalışma zamanıyla etiketlenmiş şekilde aynı DuckDB deposuna ve bulut anlık görüntüsüne alır; Oturum tekrar oynatma sekmesi birden fazla çalışma zamanı mevcut olduğunda bir **çalışma zamanı değiştirici** gösterir. Tam matris ve çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md) sayfasına, OpenClaw ailesi tanıtımı için ise [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) sayfasına bakın.

| Çalışma Zamanı / Ajan | Durum | Notlar |
|---|---|---|
| **OpenClaw** | Yerel | Referans çalışma zamanı, otomatik algılanır |
| **PicoClaw** | Beta adaptör | Düz `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkriptler, model, araç çağrıları. |
| **NanoClaw** | Beta adaptör | Oturum başına SQLite (`data/v2-sessions`). Transkriptler ve mesaj sayıları. |
| **Hermes** | Beta adaptör | SQLite `~/.hermes/state.db`. Transkriptler, model, token/maliyet. |
| **Claude Code** | Beta adaptör | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkriptler, model, araç çağrıları ve düşünceler, token kullanımı. |
| **Codex** | Beta adaptör | Rollout JSONL `~/.codex/sessions/...`. Transkriptler, model, araç çağrıları, token kullanımı. |
| **Cursor** | Beta adaptör | SQLite `state.vscdb`. Sohbet/kompozitör transkriptleri, model. |
| **Aider** | Beta adaptör | Proje başına `.aider.chat.history.md`. Transkriptler, model, token sayıları. |
| **Goose** | Beta adaptör | SQLite `~/.local/share/goose`. Transkriptler, model, araç çağrıları, token toplamları. |
| **opencode** | Beta adaptör | SQLite `~/.local/share/opencode`. Transkriptler, model, araç çağrıları, token ve maliyet. |
| **Qwen Code** | Beta adaptör | JSONL `~/.qwen/projects/.../chats`. Transkriptler, model, araç çağrıları, token kullanımı. |

"Beta adaptör", ClawMetry'nin söz konusu çalışma zamanının gerçek disk biçimi için bir okuyucu sunduğu anlamına gelir; her biri gerçek bir makinede gerçek bir kuruluma karşı oluşturulmuş ve doğrulanmıştır (bkz. `tests/fixtures/runtimes/<rt>/`). Adaptörler salt okunurdur; her biri çalışma zamanının diske gerçekten ne yazdığı konusunda dürüsttür (örneğin PicoClaw/NanoClaw/Cursor, token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü temiz bir derinlemesine inceleme için tek birine kısıtlar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet atıflandırması

Yukarıdaki çalışma zamanlarının tamamı oturumları diske yazar. OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B veya düz bir `httpx` döngüsü üzerine kurduğunuz kendi **üretim ajanınız** bunu yapmaz. ClawMetry'nin sıfır yapılandırmalı engelleyicisi, `httpx`/`requests`'i monkey-patch yöntemiyle değiştirerek yine de LLM çağrılarını (maliyet, token, gecikme, hatalar) yakalar:

```python
import clawmetry.track            # engelleyiciyi etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürüne bir ad verin

# ...ajanınız normal şekilde çalışır; her LLM çağrısı artık izlenir ve atıflandırılır.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her çağrıyı bir **adlandırılmış kaynakla** etiketler; böylece çalıştırdığınız her ürün, Overview'daki **🔌 Döngü dışı kaynaklar** kartında ajan başına çağrı, sağlayıcı, gecikme ve hata oranıyla birlikte kendi birinci sınıf, maliyet atıflandırılabilir satırı olarak görünür. Kaynak belirlenmemiş mi? Çağrılar yine de izlenir; kart yalnızca gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı adaptörlerinin beslediği veri katmanının aynısıdır (DuckDB → bulut anlık görüntüsü); dolayısıyla döngü dışı kaynaklar, diğer her şeyle aynı şekilde uçtan uca şifreli olarak bulut gösterge paneline eşitlenir.

## OpenTelemetry — satıcıya bağımsız, izlemelerinizi istediğiniz yere gönderin

ClawMetry, **GenAI semantik kurallarını** kullanarak her iki yönde de **OpenTelemetry** konuşur; böylece ajan izlemeleriniz hiçbir zaman tek bir araca kilitlenmez.

Her oturumu (LLM çağrıları, araçlar, alt ajanlar, tokenlar, maliyet) OTLP/HTTP GenAI aralıkları olarak istediğiniz toplayıcıya (Datadog, Grafana, Honeycomb veya kendi OTel Toplayıcınız) **dışa aktarın**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# eşdeğeri:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Kimlik doğrulama başlıkları ve yoklama aralığı isteğe bağlı ortam değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ek HTTP başlıkları
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # saniye (varsayılan 60)
```

**Alma** — yerleşik OTLP alıcısı, başka kaynaklardan gelen izlemeleri ve metrikleri `/v1/traces` ve `/v1/metrics` adreslerinde kabul eder (protobuf alma için `pip install clawmetry[otel]`).

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **hem de** ekibinizin halihazırda kullandığı arka uçta verilerinizi elde edersiniz; kilitlenme yok, kurulacak ikinci ajan yok.

## Yapılandırma

Çoğu kullanıcının herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma alanınızı, loglarınızı, oturumlarınızı ve cron işlemlerinizi otomatik olarak algılar.

Özelleştirmeniz gerekirse:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Yalnızca localhost'a bağlan
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesindeki adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı etkinliği gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten ayarlanmış kanallar Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Gelen/giden mesaj sayılarıyla canlı sohbet balonu görünümü için Flow'daki herhangi bir kanal düğümüne tıklayın.

| Kanal | Durum | Canlı Açılır Pencere | Notlar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Tam | ✅ | Mesajlar, istatistikler, 10 saniyelik yenileme |
| 💬 **iMessage** | ✅ Tam | ✅ | Doğrudan `~/Library/Messages/chat.db` okur |
| 💚 **WhatsApp** | ✅ Tam | ✅ | WhatsApp Web aracılığıyla (Baileys) |
| 🔵 **Signal** | ✅ Tam | ✅ | signal-cli aracılığıyla |
| 🟣 **Discord** | ✅ Tam | ✅ | Sunucu ve kanal tespiti |
| 🟪 **Slack** | ✅ Tam | ✅ | Çalışma alanı ve kanal tespiti |
| 🌐 **Webchat** | ✅ Tam | ✅ | Yerleşik web arayüzü oturumları |
| 📡 **IRC** | ✅ Tam | ✅ | Terminal stili balon arayüzü |
| 🍏 **BlueBubbles** | ✅ Tam | ✅ | BlueBubbles REST API aracılığıyla iMessage |
| 🔵 **Google Chat** | ✅ Tam | ✅ | Chat API webhook'ları aracılığıyla |
| 🟣 **MS Teams** | ✅ Tam | ✅ | Teams bot eklentisi aracılığıyla |
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi barındırılan ekip sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkeziyetsiz, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Mesajlaşma API'si |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkeziyetsiz NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API'si |

> **Otomatik algılama:** ClawMetry, `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları gösterir. Manuel kurulum gerekmez.

## Docker ile Dağıtım

ClawMetry'yi bir konteynerde çalıştırmak mı istiyorsunuz? Sorun değil! 🐳

**Docker ile hızlı başlangıç:**

```bash
# İmajı oluşturun
docker build -t clawmetry .

# Varsayılan ayarlarla çalıştırın
docker run -p 8900:8900 clawmetry

# Ya da ajanınızın veri dizinini bağlayın (örnek: OpenClaw'un ~/.openclaw dizini)
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

> **Not:** Docker'da çalıştırırken, ClawMetry'nin kurulumunuzu otomatik algılayabilmesi için ajanınızın veri ve log dizinlerini (örn. `~/.openclaw`, `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip aracılığıyla otomatik olarak kurulur)
- Aynı makinede bir yapay zeka ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw veya PicoClaw (ya da Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, [NemoClaw](https://github.com/NVIDIA/NemoClaw)'u otomatik olarak algılar. NemoClaw, ajanları korumalı alan OpenShell konteynerlerinin içinde çalıştıran NVIDIA'nın OpenClaw için kurumsal güvenlik sarmalayıcısıdır.

Çoğu durumda ek yapılandırma gerekmez. Eşitleme daemon'u, oturum dosyalarının konakta `~/.openclaw/` içinde mi yoksa bir OpenShell konteynerinin içinde mi bulunduğundan bağımsız olarak bunları otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'u iki şekilde algılar:

1. **İkili dosya tespiti** — `nemoclaw` CLI'sını kontrol eder ve korumalı alan bilgilerini almak için `nemoclaw status` komutunu çalıştırır
2. **Konteyner tespiti** — `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için çalışan Docker konteynerlerini tarar, ardından oturumları birim bağlamaları veya `docker cp` aracılığıyla okur

NemoClaw konteynerlerinden eşitlenen oturum dosyaları, bulut gösterge panelinde `runtime=nemoclaw` ve `container_id` meta verileriyle etiketlenir; böylece bunları standart OpenClaw oturumlarından kolayca ayırt edebilirsiniz.

### Önerilen kurulum: eşitleme daemon'unu KONAKTA çalıştırın

En iyi deneyim için ClawMetry'nin eşitleme daemon'unu **konak makinede** (korumalı alanın içinde değil) çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarını önler.

```bash
# Konakta (korumalı alanın dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Eşitleme daemon'u, çalışan OpenShell konteynerlerindeki oturumları otomatik olarak bulacaktır.

### İsteğe bağlı: açık korumalı alan adı

Otomatik algılama çalışmazsa ClawMetry'yi doğru korumalı alana yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Korumalı alanın içinde çalıştırma (gelişmiş)

Eşitleme daemon'unu OpenShell korumalı alanının **içinde** çalıştırmanız gerekiyorsa, ClawMetry alma API'sine ulaşabilmesi için NemoClaw ağ politikanıza şu çıkış kuralını ekleyin:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Şu komutla uygulayın:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Portlar ve uç noktalar

| Uç Nokta | Port | Protokol | Gerekli mi |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Evet (eşitleme daemon'u → bulut) |
| `localhost:8900` | 8900 | HTTP | Evet (yerel gösterge paneli arayüzü) |
| Docker soketi (`/var/run/docker.sock`) | — | Unix soketi | Konteyner oturum keşfi için |

Eşitleme daemon'u yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları yapar. Gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** sayfasına bakın.

## Test

Bu proje BrowserStack ile test edilmektedir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, yeni bir makinede `clawmetry` CLI'sını ilk kez çalıştırdığınızda
`https://app.clawmetry.com/api/install` adresine tek bir anonim "ilk çalıştırma"
pingi gönderir. Bunu, kurulum sayısını (açık kaynaklı bir proje için sahip olduğumuz
tek pazarlama metriği) ve kullanıcılarımızın hangi ajan çerçevelerini kurduğunu
öğrenmek için kullanırız.

**Kurulum başına tam olarak bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` adresinde saklanan rastgele UUID | yineleme önleme; e-postanıza veya api_key'inize bağlı değil |
| `version` | `0.12.167` | ortamda hangi sürümlerin bulunduğu |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform destek öncelikleri |
| `python` | `3.11.15` | Python sürüm destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | hangi ajanlarla entegrasyon yapılması gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediğimiz şeyler**: IP (bulut, sunucu tarafında istekten ülke kodunu türetir, ardından IP'yi siler), ana bilgisayar adı, kullanıcı adı, çalışma alanı yolu, dosya içerikleri, api_key'iniz, e-postanız, kişisel bilgi veya çalışma alanına özgü hiçbir şey. Kablo yükü, [`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında denetlenebilir.

**Devre dışı bırakma** (bunlardan herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # oturum başına
export DO_NOT_TRACK=1                          # W3C çapraz araç standardı
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işaretçisi
```

Buradaki ağ hatası, `clawmetry`'nin çalışmasını hiçbir zaman engellemez; ping, 3 saniyelik zaman aşımasıyla bir daemon iş parçacığında "fırlatıp unut" şeklinde çalışır.

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
  <strong>🦞 Ajanınızın düşüncelerini izleyin</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> tarafından yapıldı · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçası</sub>
</p>
