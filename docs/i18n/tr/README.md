<!-- i18n-src:8252f6b1d31d -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Aracınızın düşüncelerini görün.** **14 AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 10 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için gözlemlenebilirlik olarak başladı ve şimdi makinenizdeki her çalışma zamanını otomatik algılayarak **tüm ajan filonuzu** tek bir gösterge panelinde ölçümlüyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw ve NemoClaw, açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ise ClawMetry Cloud veya kendi barındırdığınız bir Pro lisansıyla etkinleşir. Çalışma zamanlarını üstbilgiden değiştirin; maliyet, token, araçlar, izler gibi her sekme o çalışma zamanına göre yeniden kapsamlanır. Tam ücretsiz/ücretli ayrımı, katman matrisi, `/api/entitlement` şekli ve `clawmetry license` CLI'si için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Kanallar, beyin, araçlar arasında akan ve geri dönen mesajları gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, aktivite ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık dökümlerle token ve maliyet takibi
- **Sessions** — Model, token, son aktivite ile aktif ajan oturumları
- **Crons** — Durum, sonraki çalışma, süre ile zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notlara göz atın
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirir
- **Approvals** — Yıkıcı silme işlemlerini, force push'ları, veritabanı mutasyonlarını, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onay arkasında kapıda tutun

## Ekran Görüntüleri

### 🧠 Brain — Canlı ajan olay akışı
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token kullanımı ve oturum özeti
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Gerçek zamanlı araç çağrı akışı
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Model ve oturuma göre maliyet dökümü
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Çalışma alanı dosya tarayıcısı
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Duruş ve denetim günlüğü
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Bütçe sınırları, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / E-posta'ya webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onay arkasında kapıda tutun; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code için çalıştırma öncesi engelleme** — tek bir komut, eşleşen araç
çağrılarını *çalışmadan önce* duraklatan ve kararınızı bekleyen bir PreToolUse
kancası kurar (telefonunuzdan tek dokunuşla,
[bulut push bildirimleri](https://app.clawmetry.com/push) etkinken):

```bash
clawmetry hooks install     # ~/.claude/settings.json dosyasını yazar (idempotent)
clawmetry hooks status      # neyin bağlandığını + kaç politikanın etkin olduğunu gösterir
clawmetry hooks uninstall   # yalnızca ClawMetry'nin girdilerini kaldırır
```

Bir ret, yalnızca o tek araç çağrısını engeller; ajan oturumunu korur ve başka
bir yaklaşım deneyebilir. Telefonunuzdan onaylamak, Claude Code'un kendi izin
istemini atlar (zaten yanıtladınız). Eşleşmeyen araçlar ~40ms'ye mal olur ve
Claude Code'un normal izin akışına geri düşer. Ayrıca Claude Code'un kendisi
sizi beklerken de telefonunuza bir push bildirimi alırsınız
(`permission_prompt` / `idle_prompt` bildirimleri).

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

v2 React uygulaması `frontend/` içinde yaşar ve v2 etkinken Flask
sunucusu başlatıldığında `/v2` adresinde sunulur.

Geliştirme sırasında iki terminal kullanın:

```bash
# Terminal 1: :8900 üzerinde Flask API/sunucusu
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: :5173 üzerinde Vite geliştirme sunucusu
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini
`http://localhost:8900` adresine yönlendirir, böylece React uygulaması
ekstra CORS ayarı olmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilen paketi oluşturmak için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` konumuna yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry yalnızca OpenClaw'ı değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine çeviren özel bir okuyucu bağdaştırıcısı sunar; daemon bunları çalışma zamanı etiketiyle aynı DuckDB deposuna + bulut anlık görüntüsüne alır ve birden fazla çalışma zamanı mevcut olduğunda Session replay sekmesi bir **çalışma zamanı değiştirici** gösterir. Tam matris + çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md), OpenClaw ailesi hakkında bir giriş için [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) dosyasına bakın.

| Çalışma Zamanı / Ajan | Durum | Notlar |
|---|---|---|
| **OpenClaw** | Yerel | Referans çalışma zamanı, otomatik algılanır |
| **PicoClaw** | Beta bağdaştırıcı | Düz `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkriptler, model, araç çağrıları. |
| **NanoClaw** | Beta bağdaştırıcı | Oturum başına SQLite (`data/v2-sessions`). Transkriptler + mesaj sayıları. |
| **Hermes** | Beta bağdaştırıcı | SQLite `~/.hermes/state.db`. Transkriptler, model, token/maliyet. |
| **Claude Code** | Beta bağdaştırıcı | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkriptler, model, araç çağrıları + düşünme, token kullanımı. |
| **Codex** | Beta bağdaştırıcı | Rollout JSONL `~/.codex/sessions/...`. Transkriptler, model, araç çağrıları, token kullanımı. |
| **Cursor** | Beta bağdaştırıcı | SQLite `state.vscdb`. Sohbet/composer transkriptleri, model. |
| **Aider** | Beta bağdaştırıcı | Proje başına `.aider.chat.history.md`. Transkriptler, model, token sayıları. |
| **Goose** | Beta bağdaştırıcı | SQLite `~/.local/share/goose`. Transkriptler, model, araç çağrıları, token toplamları. |
| **opencode** | Beta bağdaştırıcı | SQLite `~/.local/share/opencode`. Transkriptler, model, araç çağrıları, token + maliyet. |
| **Qwen Code** | Beta bağdaştırıcı | JSONL `~/.qwen/projects/.../chats`. Transkriptler, model, araç çağrıları, token kullanımı. |
| **Pi** | Beta bağdaştırıcı | JSONL `~/.pi/agent/sessions`. Transkriptler, model, araç çağrıları, token + maliyet. |
| **Deep Agents** | Beta bağdaştırıcı | SQLite `~/.deepagents/.state/sessions.db`. Transkriptler, model, araç çağrıları, token + maliyet. |
| **n8n** | Beta bağdaştırıcı | SQLite `~/.n8n/database.sqlite`. İş akışı çalıştırmaları, düğüm çalıştırmaları, AI Agent istemleri, n8n'in kaydettiği yerlerde model + token. |

"Beta bağdaştırıcı", ClawMetry'nin o çalışma zamanının gerçek diskteki biçimi için bir okuyucu sunduğu, her birinin gerçek bir makinedeki gerçek bir kurulumla oluşturulup doğrulandığı anlamına gelir (bkz. `tests/fixtures/runtimes/<rt>/`). Bağdaştırıcılar salt okunurdur; her biri çalışma zamanının diske gerçekte ne kaydettiği konusunda dürüsttür (örn. PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü temiz bir derinlemesine inceleme için tek birine kapsamlar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet ilişkilendirmesi

Yukarıdaki çalışma zamanlarının hepsi oturumları diske yazar. Sizin kendi **üretim ajanınız** ise, OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B veya düz bir `httpx` döngüsü üzerine kurduğunuz ajan, bunu yapmaz. ClawMetry'nin sıfır yapılandırmalı interceptor'ı, `httpx`/`requests`'e monkey-patch uygulayarak LLM çağrılarını (maliyet, token, gecikme, hatalar) yine de yakalar:

```python
import clawmetry.track            # interceptor'ı etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürünü adlandır

# ...ajanınız normal şekilde çalışır; artık her LLM çağrısı izlenir + ilişkilendirilir.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her çağrıyı adlandırılmış bir **kaynak** ile etiketler; böylece çalıştırdığınız her ürün, gösterge panelinin Overview sekmesindeki **🔌 Döngü dışı kaynaklar** kartında kendi başına birinci sınıf, maliyet ilişkilendirilebilir bir satır olarak görünür: ajan başına çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak ayarlanmadıysa? Çağrılar yine izlenir; kart sadece gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı bağdaştırıcılarının beslediği aynı veri katmanıdır (DuckDB → bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar da diğer her şey gibi buluta senkronize edilir, uçtan uca şifreli olarak.

## OpenTelemetry — satıcıdan bağımsız, izlerinizi istediğiniz yere gönderin

ClawMetry, **GenAI anlamsal kurallarını** kullanarak her iki yönde de **OpenTelemetry** konuşur, böylece ajan izleriniz asla tek bir araca kilitlenmez.

Her oturumu (LLM çağrıları, araçlar, alt ajanlar, token'lar, maliyet) herhangi bir toplayıcıya (Datadog, Grafana, Honeycomb veya kendi OTel Collector'ınız) OTLP/HTTP GenAI izleri olarak **dışa aktarın**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# eşdeğer olarak:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Yetkilendirme başlıkları ve yoklama aralığı isteğe bağlı ortam değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ekstra HTTP başlıkları
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # saniye (varsayılan 60)
```

**Alma** — yerleşik OTLP alıcısı, `/v1/traces` ve `/v1/metrics` adreslerinde başka her şeyden gelen izleri ve metrikleri kabul eder (protobuf alımı için `pip install clawmetry[otel]`).

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **hem de** verilerinizi ekibinizin zaten kullandığı herhangi bir arka uçta elde edersiniz; kilitlenme yok, kurulacak ikinci bir ajan yok.

## Yapılandırma

Çoğu kişinin herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma alanınızı, günlüklerinizi, oturumlarınızı ve cron işlerinizi otomatik algılar.

Özelleştirmeniz gerekiyorsa:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Yalnızca localhost'a bağlan
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesindeki adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı aktivite gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten kurulu olan kanallar Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj sayılarıyla canlı sohbet balonu görünümünü görebilirsiniz.

| Kanal | Durum | Canlı Popup | Notlar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Tam | ✅ | Mesajlar, istatistikler, 10 sn yenileme |
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
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi barındırılan ekip sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkeziyetsiz, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkeziyetsiz NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları oluşturur. Manuel kurulum gerekmez.

## Docker ile Dağıtım

ClawMetry'yi bir konteynerde çalıştırmak mı istiyorsunuz? Sorun değil! 🐳

**Docker ile hızlı başlangıç:**

```bash
# İmajı oluştur
docker build -t clawmetry .

# Varsayılan ayarlarla çalıştır
docker run -p 8900:8900 clawmetry

# Ya da ajanınızın veri dizinini bağlayın (gösterilen: OpenClaw'ın ~/.openclaw'ı)
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

> **Not:** Docker'da çalıştırırken, ClawMetry'nin kurulumunuzu otomatik algılayabilmesi için ajanınızın veri + log dizinlerini (örn. `~/.openclaw`, `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip aracılığıyla otomatik olarak kurulur)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents veya n8n (ya da Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, [NemoClaw](https://github.com/NVIDIA/NemoClaw)'ı otomatik olarak algılar; bu, NVIDIA'nın ajanları sandbox'lı OpenShell konteynerleri içinde çalıştıran OpenClaw için kurumsal güvenlik sarmalayıcısıdır.

Çoğu durumda ekstra yapılandırma gerekmez. Senkronizasyon daemon'u, oturum dosyalarını ister ana bilgisayarda `~/.openclaw/` içinde ister bir OpenShell konteyneri içinde bulunsun otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili dosya algılama** — `nemoclaw` CLI'sini kontrol eder ve sandbox bilgisi almak için `nemoclaw status` çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için tarar, ardından oturumları birim bağlantıları veya `docker cp` aracılığıyla okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut gösterge panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir, böylece bunları standart OpenClaw oturumlarından bir bakışta ayırt edebilirsiniz.

### Önerilen kurulum: sync daemon'unu HOST üzerinde çalıştırın

En iyi deneyim için ClawMetry'nin senkronizasyon daemon'unu (sandbox içinde değil) **ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından kaçınır.

```bash
# Ana makinede (sandbox dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Senkronizasyon daemon'u, çalışan herhangi bir OpenShell konteyneri içindeki oturumları otomatik olarak bulacaktır.

### İsteğe bağlı: açık sandbox adı

Otomatik algılama çalışmazsa, ClawMetry'yi doğru sandbox'a yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sandbox içinde çalıştırma (ileri düzey)

Senkronizasyon daemon'unu OpenShell sandbox'ının **içinde** çalıştırmanız gerekiyorsa, ClawMetry ingest API'sine ulaşabilmesi için NemoClaw ağ politikanıza şu çıkış (egress) kuralını ekleyin:

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

Senkronizasyon daemon'u yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları yapar. Gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**'na bakın.

## Test

Bu proje BrowserStack ile test edilmektedir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `https://app.clawmetry.com/api/install` adresine anonim
kurulum yaşam döngüsü sinyalleri gönderir: `clawmetry` CLI'sini yeni bir
makinede ilk çalıştırdığınızda bir `install` sinyali, yeni bir sürüme
yükselttikten sonraki ilk çalıştırmada bir `update` sinyali ve gösterge
paneli içi ilk kurulum seçimini tamamladığınızda bir `onboarded`
sinyali. Bunu gerçek kurulumları saymak için kullanıyoruz (ham PyPI
indirme sayıları ~%98 yansı sunucu, CI ve otomatik güncelleme yeniden
indirmeleri) ve hangi ajan çerçevelerinin ve sürümlerinin gerçekte
kullanımda olduğunu öğrenmek için.

**Sürüm başına yaşam döngüsü olayı başına en fazla bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` konumunda saklanan rastgele UUID | tekilleştirme; Cloud senkronizasyonunu açıkça bağlayana kadar anonimdir (kimliği doğrulanmış daemon nabız sinyali daha sonra bunu taşır ve bu kurulumu hesabınıza bağlar) |
| `event` | `install` / `update` / `onboarded` | mevcut bir kurulumun yeni kurulumu mu yükseltmesi mi |
| `version` | `0.12.167` | hangi sürümlerin kullanımda olduğu |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürüm destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | sırada hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediklerimiz**: IP adresi (bulut, ülke kodunu istekten sunucu
tarafında türetir, ardından IP'yi atar), ana bilgisayar adı, kullanıcı
adı, çalışma alanı yolu, dosya içerikleri, api_key'iniz, e-postanız,
kişisel veya çalışma alanına özgü herhangi bir şey. Kablo üzerindeki
yük [`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında
denetlenebilir.

**Devre dışı bırakma** (aşağıdakilerden herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # kabuk başına
export DO_NOT_TRACK=1                          # W3C çapraz araç standardı
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işareti
```

Buradaki bir ağ hatası, `clawmetry`'nin çalışmasını asla engellemez;
sinyal, 3 sn zaman aşımlı bir daemon iş parçacığında gönder ve unut
şeklindedir.

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
  <strong>🦞 Aracınızın düşüncelerini görün</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçasıdır</sub>
</p>
