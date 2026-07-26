<!-- i18n-src:bab48eec552f -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ajanınızın düşünmesini izleyin.** **14 AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 10 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için bir gözlemlenebilirlik aracı olarak başladı; şimdi ise **tüm ajan filonuzu** tek bir gösterge panelinde ölçümlüyor ve makinenizdeki her çalışma zamanını otomatik olarak algılıyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw ve NemoClaw, açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ise ClawMetry Cloud veya kendi barındırdığınız bir Pro lisansıyla etkinleşir. Çalışma zamanını başlıktan değiştirin, her sekme (maliyet, token'lar, araçlar, izler) o çalışma zamanına yeniden odaklanır. Tam ücretsiz/ücretli ayrımı, katman matrisi, `/api/entitlement` şeması ve `clawmetry license` CLI'si için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Mesajların kanallar, beyin, araçlar arasında akışını ve geri dönüşünü gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, aktivite ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık dökümlerle token ve maliyet takibi
- **Sessions** — Model, token'lar, son aktiviteyle birlikte aktif ajan oturumları
- **Crons** — Durum, sonraki çalıştırma, süre bilgisiyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notları görüntüleyin
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, Email'e yönlendirir
- **Approvals** — Yıkıcı silmeleri, force push'ları, veritabanı mutasyonlarını, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onaya bağlayın

## Ekran Görüntüleri

### 🧠 Brain — Canlı ajan olay akışı
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token kullanımı ve oturum özeti
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Gerçek zamanlı araç çağrısı akışı
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Modele ve oturuma göre maliyet dökümü
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Çalışma alanı dosya tarayıcısı
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Duruş ve denetim günlüğü
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Bütçe sınırları, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / Email'e webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onaya bağlayın; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code için çalıştırma öncesi engelleme** — tek bir komut, eşleşen araç
çağrılarını *çalışmadan önce* duraklatan ve kararınızı bekleyen bir PreToolUse
hook'u kurar (telefonunuzdan tek dokunuşla, [bulut push bildirimleri](https://app.clawmetry.com/push)
etkinleştirildiğinde):

```bash
clawmetry hooks install     # ~/.claude/settings.json dosyasına yazar (idempotent)
clawmetry hooks status      # neyin bağlı olduğunu ve kaç politikanın etkin olduğunu gösterir
clawmetry hooks uninstall   # yalnızca ClawMetry'nin girdilerini kaldırır
```

Bir ret, yalnızca o tek araç çağrısını engeller; ajan oturumunu korur ve başka
bir yaklaşım deneyebilir. Telefonunuzdan onaylamak, Claude Code'un kendi izin
istemini atlar (zaten yanıtlamışsınızdır). Eşleşmeyen araçlar yaklaşık 40ms'ye
mal olur ve Claude Code'un normal izin akışına düşer. Ayrıca Claude Code'un
kendisi sizi beklerken de telefonunuza push bildirimi alırsınız (`permission_prompt` /
`idle_prompt` bildirimleri).

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

**Kaynaktan:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Frontend Geliştirme

v2 React uygulaması `frontend/` dizininde bulunur ve Flask sunucusu v2
etkinleştirilerek başlatıldığında `/v2` adresinde sunulur.

Geliştirme yaparken iki terminal kullanın:

```bash
# Terminal 1: :8900 üzerinde Flask API/sunucu
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: :5173 üzerinde Vite dev sunucusu
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini
`http://localhost:8900` adresine yönlendirir, böylece React uygulaması
ekstra CORS ayarı yapmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilecek paketi oluşturmak için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` dizinine yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry, sadece OpenClaw'ı değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine çeviren özel bir okuyucu adaptörüyle gelir; daemon bunları aynı DuckDB deposuna + bulut anlık görüntüsüne, çalışma zamanı etiketiyle birlikte alır ve birden fazla çalışma zamanı mevcut olduğunda Session replay sekmesi bir **çalışma zamanı değiştirici** gösterir. Tam matris ve çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md) dosyasına, OpenClaw ailesi hakkında bir giriş için [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) dosyasına bakın.

| Çalışma Zamanı / Ajan | Durum | Notlar |
|---|---|---|
| **OpenClaw** | Yerel | Referans çalışma zamanı, otomatik algılanır |
| **PicoClaw** | Beta adaptör | Düz `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Dökümler, model, araç çağrıları. |
| **NanoClaw** | Beta adaptör | Oturum başına SQLite (`data/v2-sessions`). Dökümler + mesaj sayıları. |
| **Hermes** | Beta adaptör | SQLite `~/.hermes/state.db`. Dökümler, model, token'lar/maliyet. |
| **Claude Code** | Beta adaptör | JSONL `~/.claude/projects/.../<id>.jsonl`. Dökümler, model, araç çağrıları + düşünme, token kullanımı. |
| **Codex** | Beta adaptör | Rollout JSONL `~/.codex/sessions/...`. Dökümler, model, araç çağrıları, token kullanımı. |
| **Cursor** | Beta adaptör | SQLite `state.vscdb`. Chat/composer dökümleri, model. |
| **Aider** | Beta adaptör | Proje başına `.aider.chat.history.md`. Dökümler, model, token sayıları. |
| **Goose** | Beta adaptör | SQLite `~/.local/share/goose`. Dökümler, model, araç çağrıları, token toplamları. |
| **opencode** | Beta adaptör | SQLite `~/.local/share/opencode`. Dökümler, model, araç çağrıları, token'lar + maliyet. |
| **Qwen Code** | Beta adaptör | JSONL `~/.qwen/projects/.../chats`. Dökümler, model, araç çağrıları, token kullanımı. |
| **Pi** | Beta adaptör | JSONL `~/.pi/agent/sessions`. Dökümler, model, araç çağrıları, token'lar + maliyet. |
| **Deep Agents** | Beta adaptör | SQLite `~/.deepagents/.state/sessions.db`. Dökümler, model, araç çağrıları, token'lar + maliyet. |

"Beta adaptör", ClawMetry'nin o çalışma zamanının gerçek disk üzerindeki biçimi için bir okuyucu sunduğu anlamına gelir; her biri gerçek bir makinedeki gerçek bir kurulum karşısında oluşturulmuş ve doğrulanmıştır (bkz. `tests/fixtures/runtimes/<rt>/`). Adaptörler salt okunurdur; her biri kendi çalışma zamanının diskte gerçekte ne sakladığı konusunda dürüsttür (örn. PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü temiz bir derinlemesine inceleme için tek bir çalışma zamanına odaklar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet atfı

Yukarıdaki çalışma zamanlarının tümü oturumları diske yazar. Sizin kendi **üretim ajanınız** ise -OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B veya sade bir `httpx` döngüsü üzerine kurduğunuz- bunu yapmaz. ClawMetry'nin sıfır yapılandırmalı interceptor'ı, `httpx`/`requests`'i monkey-patch ederek LLM çağrılarını (maliyet, token'lar, gecikme, hatalar) yine de yakalar:

```python
import clawmetry.track            # interceptor'ı etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürünü adlandır

# ...ajanınız normal şekilde çalışır; her LLM çağrısı artık izlenir + atfedilir.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her çağrıyı **adlandırılmış bir kaynak** ile etiketler; böylece çalıştırdığınız her ürün, gösterge panelinin Overview sekmesindeki **🔌 Döngü dışı kaynaklar** kartında kendi başına, maliyet atfedilebilir bir satır olarak görünür — her ajan için çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak ayarlanmadıysa? Çağrılar yine de izlenir; kart sadece gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı adaptörlerinin beslediği aynı veri katmanıdır (DuckDB → bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar diğer her şey gibi buluta senkronize olur, uçtan uca şifrelenmiş olarak.

## OpenTelemetry — sağlayıcıdan bağımsız, izlerinizi istediğiniz yere gönderin

ClawMetry her iki yönde de **OpenTelemetry** konuşur, **GenAI anlamsal sözleşmelerini** kullanarak, böylece ajan izleriniz asla tek bir araca kilitlenmez.

Her oturumu -LLM çağrıları, araçlar, alt ajanlar, token'lar, maliyet- herhangi bir toplayıcıya (Datadog, Grafana, Honeycomb veya kendi OTel Collector'ınız) OTLP/HTTP GenAI izleri olarak **dışa aktarın**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# eşdeğer olarak:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Yetkilendirme başlıkları ve yoklama aralığı isteğe bağlı ortam değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ek HTTP başlıkları
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # saniye (varsayılan 60)
```

**İçe aktarma** — yerleşik OTLP alıcısı, başka herhangi bir yerden gelen izleri ve metrikleri `/v1/traces` ve `/v1/metrics` adreslerinde kabul eder (protobuf içe aktarımı için `pip install clawmetry[otel]`).

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **hem de** verilerinizi ekibinizin zaten çalıştırdığı herhangi bir arka uçta elde edersiniz — kilitlenme yok, kurulacak ikinci bir ajan yok.

## Yapılandırma

Çoğu kişinin herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma alanınızı, günlüklerinizi, oturumlarınızı ve zamanlanmış işlerinizi otomatik olarak algılar.

Özelleştirmeniz gerekiyorsa:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Sadece yerel makineye bağla
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesinde adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı aktivite gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten kurulu olan kanallar Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj sayılarıyla birlikte canlı bir sohbet balonu görünümü görebilirsiniz.

| Kanal | Durum | Canlı Popup | Notlar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Tam | ✅ | Mesajlar, istatistikler, 10sn yenileme |
| 💬 **iMessage** | ✅ Tam | ✅ | `~/Library/Messages/chat.db` dosyasını doğrudan okur |
| 💚 **WhatsApp** | ✅ Tam | ✅ | WhatsApp Web (Baileys) üzerinden |
| 🔵 **Signal** | ✅ Tam | ✅ | signal-cli üzerinden |
| 🟣 **Discord** | ✅ Tam | ✅ | Sunucu + kanal algılama |
| 🟪 **Slack** | ✅ Tam | ✅ | Çalışma alanı + kanal algılama |
| 🌐 **Webchat** | ✅ Tam | ✅ | Yerleşik web arayüzü oturumları |
| 📡 **IRC** | ✅ Tam | ✅ | Terminal tarzı balon arayüzü |
| 🍏 **BlueBubbles** | ✅ Tam | ✅ | BlueBubbles REST API üzerinden iMessage |
| 🔵 **Google Chat** | ✅ Tam | ✅ | Chat API webhook'ları üzerinden |
| 🟣 **MS Teams** | ✅ Tam | ✅ | Teams bot eklentisi üzerinden |
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi barındırılan takım sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkeziyetsiz, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkeziyetsiz NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry, `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları oluşturur. Manuel kurulum gerekmez.

## Docker ile Dağıtım

ClawMetry'yi bir konteynerde çalıştırmak mı istiyorsunuz? Sorun değil! 🐳

**Docker ile hızlı başlangıç:**

```bash
# İmajı oluştur
docker build -t clawmetry .

# Varsayılan ayarlarla çalıştır
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

> **Not:** Docker'da çalıştırırken, ClawMetry'nin kurulumunuzu otomatik algılayabilmesi için ajanınızın veri + günlük dizinlerini (örn. `~/.openclaw`, `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip ile otomatik kurulur)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi veya Deep Agents (veya Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, ajanları sandbox'lanmış OpenShell konteynerleri içinde çalıştıran NVIDIA'nın kurumsal güvenlik sarmalayıcısı [NemoClaw](https://github.com/NVIDIA/NemoClaw)'ı otomatik olarak algılar.

Çoğu durumda ek yapılandırma gerekmez. Sync daemon, oturum dosyalarının ana makinedeki `~/.openclaw/` içinde mi yoksa bir OpenShell konteyneri içinde mi olduğunu otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili algılama** — `nemoclaw` CLI'sini kontrol eder ve sandbox bilgisini almak için `nemoclaw status` çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için tarar, ardından oturumları birim bağlantıları veya `docker cp` üzerinden okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut gösterge panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir; böylece bunları standart OpenClaw oturumlarından ilk bakışta ayırt edebilirsiniz.

### Önerilen kurulum: HOST üzerinde sync daemon

En iyi deneyim için ClawMetry'nin sync daemon'ını sandbox içinde değil, **ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından kaçınmanızı sağlar.

```bash
# Ana makinede (sandbox'ın dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync daemon, çalışan herhangi bir OpenShell konteyneri içindeki oturumları otomatik olarak bulacaktır.

### İsteğe bağlı: açık sandbox adı

Otomatik algılama işe yaramazsa, ClawMetry'yi doğru sandbox'a yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sandbox içinde çalıştırma (ileri düzey)

Sync daemon'ı OpenShell sandbox'ının **içinde** çalıştırmanız gerekiyorsa, ClawMetry ingest API'sine erişebilmesi için NemoClaw ağ politikanıza şu giden trafik kuralını ekleyin:

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

| Uç Nokta | Port | Protokol | Gerekli |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Evet (sync daemon → bulut) |
| `localhost:8900` | 8900 | HTTP | Evet (yerel gösterge paneli arayüzü) |
| Docker soketi (`/var/run/docker.sock`) | — | Unix soketi | Konteyner oturum keşfi için |

Sync daemon yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları yapar. Gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** dosyasına bakın.

## Test

Bu proje BrowserStack ile test edilmiştir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `clawmetry` CLI'sini yeni bir makinede ilk çalıştırdığınızda
`https://app.clawmetry.com/api/install` adresine tek bir anonim "ilk çalıştırma"
pingi gönderir. Bunu kurulumları saymak için (açık kaynak bir proje için sahip
olduğumuz tek pazarlama metriği) ve kullanıcılarımızın hangi ajan
çerçevelerini kurduğunu öğrenmek için kullanıyoruz.

**Kurulum başına tam olarak bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` dosyasında saklanan rastgele UUID | tekrarı önleme; e-postanıza veya api_key'inize bağlı değil |
| `version` | `0.12.167` | hangi sürümlerin kullanımda olduğu |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürüm destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | bundan sonra hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediğimiz şeyler**: IP (bulut, ülke kodunu istekten sunucu tarafında
türetir, ardından IP'yi atar), ana bilgisayar adı, kullanıcı adı, çalışma
alanı yolu, dosya içerikleri, api_key'iniz, e-postanız, kişisel veya çalışma
alanına özgü herhangi bir şey. Tel üzerindeki yük,
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında denetlenebilir.

**Devre dışı bırakma** (bunlardan herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # kabuk başına
export DO_NOT_TRACK=1                          # W3C çapraz araç standardı
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işareti
```

Buradaki bir ağ hatası `clawmetry`'nin çalışmasını asla engellemez; ping,
arka plan iş parçacığında 3 saniyelik zaman aşımıyla gönder-ve-unut şeklindedir.

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
  <strong>🦞 Ajanınızın düşünmesini izleyin</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçası</sub>
</p>
