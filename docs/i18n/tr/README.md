<!-- i18n-src:191e9094d7fa -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Aracınızın düşüncesini görün.** **14 farklı AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 10 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için gözlemlenebilirlik olarak başladı; artık **tüm ajan filonuzu** tek bir gösterge panelinde ölçümlüyor ve makinenizdeki her çalışma zamanını otomatik algılıyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw ve NemoClaw açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ise ClawMetry Cloud veya kendi barındırdığınız bir Pro lisansıyla etkinleşir. Üstbilgiden çalışma zamanını değiştirin; maliyet, token, araçlar, izler gibi her sekme o çalışma zamanına göre yeniden kapsamlanır. Tam ücretsiz/ücretli ayrımı, katman matrisi, `/api/entitlement` şeması ve `clawmetry license` CLI'si için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Kanallar, beyin, araçlar arasında akan ve geri dönen mesajları gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, aktivite ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık kırılımlarla token ve maliyet takibi
- **Sessions** — Model, token, son etkinlik bilgileriyle aktif ajan oturumları
- **Crons** — Durum, sonraki çalıştırma zamanı, süre bilgileriyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notları göz atın
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirir
- **Approvals** — Yıkıcı silmeleri, zorla push'ları, veritabanı mutasyonlarını, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onaya bağlayın

## Ekran Görüntüleri

### 🧠 Brain — Canlı ajan olay akışı
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token kullanımı ve oturum özeti
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Gerçek zamanlı araç çağrısı akışı
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Model ve oturuma göre maliyet kırılımı
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Çalışma alanı dosya tarayıcısı
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Duruş ve denetim günlüğü
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Bütçe sınırları, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / E-posta'ya webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onaya bağlayın; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code için yürütme öncesi engelleme** — tek bir komut, eşleşen araç
çağrılarını çalıştırılmadan *önce* duraklatan ve kararınızı bekleyen bir
PreToolUse kancası kurar (telefonunuzdan
[cloud push bildirimleri](https://app.clawmetry.com/push) etkinken tek dokunuşla):

```bash
clawmetry hooks install     # ~/.claude/settings.json dosyasına yazar (idempotent)
clawmetry hooks status      # neyin bağlandığını + kaç politikanın etkin olduğunu gösterir
clawmetry hooks uninstall   # yalnızca ClawMetry'nin girdilerini kaldırır
```

Bir ret yalnızca o tek araç çağrısını engeller; ajan oturumunu korur ve
başka bir yaklaşım deneyebilir. Telefonunuzdan onaylamak, Claude Code'un
kendi izin istemini atlar (zaten yanıtladınız). Eşleşmeyen araçlar ~40ms'ye
mal olur ve Claude Code'un normal izin akışına geri düşer. Ayrıca Claude
Code'un sizi beklediği durumlarda da (`permission_prompt` / `idle_prompt`
bildirimleri) telefonunuza bir push bildirimi gelir.

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

v2 React uygulaması `frontend/` dizininde bulunur ve Flask sunucusu v2
etkinken başlatıldığında `/v2` adresinde sunulur.

Geliştirme yaparken iki terminal kullanın:

```bash
# Terminal 1: Flask API/sunucusu :8900 üzerinde
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite geliştirme sunucusu :5173 üzerinde
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini
`http://localhost:8900` adresine yönlendirir; böylece React uygulaması ek
bir CORS kurulumu olmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilen paketi oluşturmak için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` dizinine yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry yalnızca OpenClaw'ı değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine çeviren özel bir okuyucu adaptörüyle birlikte gelir; daemon bunları çalışma zamanı etiketiyle birlikte aynı DuckDB deposuna + bulut anlık görüntüsüne alır ve birden fazla çalışma zamanı mevcut olduğunda Oturum tekrar oynatma sekmesi bir **çalışma zamanı değiştirici** gösterir. Tam matris + çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md), OpenClaw ailesine giriş için [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) dosyasına bakın.

[Perplexity'nin numbat](https://github.com/perplexityai/numbat) ajan güvenliği aracını mı kullanıyorsunuz? ClawMetry, bulgularını ve uygulama kararlarını doğrudan kutudan alır; bkz. [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Çalışma Zamanı / Ajan | Durum | Notlar |
|---|---|---|
| **OpenClaw** | Yerel | Referans çalışma zamanı, otomatik algılanır |
| **PicoClaw** | Beta adaptör | Düz `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Konuşma dökümleri, model, araç çağrıları. |
| **NanoClaw** | Beta adaptör | Oturum başına SQLite (`data/v2-sessions`). Konuşma dökümleri + mesaj sayıları. |
| **Hermes** | Beta adaptör | SQLite `~/.hermes/state.db`. Konuşma dökümleri, model, token/maliyet. |
| **Claude Code** | Beta adaptör | JSONL `~/.claude/projects/.../<id>.jsonl`. Konuşma dökümleri, model, düşünceyle birlikte araç çağrıları, token kullanımı. |
| **Codex** | Beta adaptör | Rollout JSONL `~/.codex/sessions/...`. Konuşma dökümleri, model, araç çağrıları, token kullanımı. |
| **Cursor** | Beta adaptör | SQLite `state.vscdb`. Sohbet/composer konuşma dökümleri, model. |
| **Aider** | Beta adaptör | Proje başına `.aider.chat.history.md`. Konuşma dökümleri, model, token sayıları. |
| **Goose** | Beta adaptör | SQLite `~/.local/share/goose`. Konuşma dökümleri, model, araç çağrıları, token toplamları. |
| **opencode** | Beta adaptör | SQLite `~/.local/share/opencode`. Konuşma dökümleri, model, araç çağrıları, token + maliyet. |
| **Qwen Code** | Beta adaptör | JSONL `~/.qwen/projects/.../chats`. Konuşma dökümleri, model, araç çağrıları, token kullanımı. |
| **Pi** | Beta adaptör | JSONL `~/.pi/agent/sessions`. Konuşma dökümleri, model, araç çağrıları, token + maliyet. |
| **Deep Agents** | Beta adaptör | SQLite `~/.deepagents/.state/sessions.db`. Konuşma dökümleri, model, araç çağrıları, token + maliyet. |
| **n8n** | Beta adaptör | SQLite `~/.n8n/database.sqlite`. İş akışı yürütmeleri, düğüm çalışmaları, AI Agent istemleri, n8n'in kaydettiği yerlerde model + token. |
| **Antigravity** | Beta adaptör | `~/.gemini/<flavor>/brain/` altında Brain JSONL. Konuşmalar, araç adımları, düşünce, üretim başına Gemini token kırılımı + maliyet, arka plan üretim tüketimi. |

"Beta adaptör", ClawMetry'nin o çalışma zamanının gerçek disk üzerindeki biçimi için bir okuyucu gönderdiği ve her birinin gerçek bir makinedeki gerçek bir kuruluma karşı oluşturulup doğrulandığı anlamına gelir (bkz. `tests/fixtures/runtimes/<rt>/`). Adaptörler salt okunurdur; her biri çalışma zamanının diskte gerçekte ne depoladığı konusunda dürüsttür (ör. PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü temiz bir derinlemesine inceleme için tek bir çalışma zamanına kapsamlar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet atfı

Yukarıdaki çalışma zamanlarının hepsi oturumları diske yazar. Sizin kendi
**üretim ajanınız** ise -OpenAI Agents SDK, LangChain, Vercel AI SDK,
LlamaIndex, E2B veya düz bir `httpx` döngüsü üzerine kurduğunuz ajan-
bunu yapmaz. ClawMetry'nin sıfır yapılandırmalı önleyicisi, `httpx`/`requests`
üzerinde maymun yaması (monkey-patch) yaparak yine de onun LLM çağrılarını
(maliyet, token, gecikme, hatalar) yakalar:

```python
import clawmetry.track            # önleyiciyi etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürünü adlandır

# ...ajanınız normal şekilde çalışır; artık her LLM çağrısı izleniyor + atfediliyor.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her
çağrıyı **adlandırılmış bir kaynak** ile etiketler; böylece çalıştırdığınız
her ürün, gösterge panelinin Overview sekmesindeki **🔌 Döngü dışı kaynaklar**
kartında kendi başına, maliyeti atfedilebilir bir satır olarak görünür:
ajan başına çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak ayarlanmadıysa
çağrılar yine de izlenir; kart yalnızca gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı adaptörlerinin beslediği aynı veri katmanıdır (DuckDB →
bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar da diğer her şey gibi
uçtan uca şifrelenerek bulut gösterge paneline senkronize olur.

## OpenTelemetry — satıcıdan bağımsız, izlerinizi istediğiniz yere gönderin

ClawMetry her iki yönde de **OpenTelemetry** konuşur, **GenAI semantik
kurallarını** kullanarak; böylece ajan izleriniz asla tek bir araca kilitlenmez.

**Dışa aktarma** — her oturumu (LLM çağrıları, araçlar, alt ajanlar, token,
maliyet) OTLP/HTTP GenAI izleri olarak herhangi bir toplayıcıya gönderin
(Datadog, Grafana, Honeycomb veya kendi OTel Collector'ınız):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# eşdeğer olarak:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Kimlik doğrulama başlıkları ve sorgulama aralığı isteğe bağlı ortam
değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ek HTTP başlıkları
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # saniye (varsayılan 60)
```

**İçe aktarma** — yerleşik OTLP alıcısı, `/v1/traces` ve `/v1/metrics`
adreslerinde başka herhangi bir yerden gelen izleri ve metrikleri kabul eder
(protobuf içe aktarımı için `pip install clawmetry[otel]`).

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **hem
de** ekibinizin zaten çalıştırdığı herhangi bir arka uçtaki verilerinizi elde
edersiniz; ne kilitlenme, ne de kurulacak ikinci bir ajan.

## Yapılandırma

Çoğu insanın herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma
alanınızı, günlüklerinizi, oturumlarınızı ve zamanlanmış işlerinizi otomatik
algılar.

Özelleştirmeniz gerekiyorsa:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Yalnızca localhost'a bağlan
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesinde adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı etkinlik gösterir.
Yalnızca `openclaw.json` dosyanızda gerçekten kurulmuş kanallar Flow
diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj
sayılarıyla birlikte canlı bir sohbet balonu görünümü görebilirsiniz.

| Kanal | Durum | Canlı Açılır Pencere | Notlar |
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
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi barındırılan takım sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkeziyetsiz, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkeziyetsiz NIP-04 DM'leri |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları render eder. Manuel kurulum gerekmez.

## Docker Dağıtımı

ClawMetry'yi bir konteyner içinde çalıştırmak mı istiyorsunuz? Sorun değil! 🐳

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

> **Not:** Docker içinde çalıştırırken, ClawMetry'nin kurulumunuzu otomatik algılayabilmesi için ajanınızın veri + log dizinlerini (ör. `~/.openclaw`, `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip ile otomatik olarak yüklenir)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n veya Antigravity (veya Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, OpenClaw ajanlarını sandbox'lanmış OpenShell konteynerleri içinde
çalıştıran NVIDIA'nın kurumsal güvenlik sarmalayıcısı olan
[NemoClaw](https://github.com/NVIDIA/NemoClaw)'ı otomatik olarak algılar.

Çoğu durumda ekstra yapılandırma gerekmez. Sync daemon'u, oturum dosyalarının
ister ana makinede `~/.openclaw/` içinde ister bir OpenShell konteyneri
içinde bulunmasına bakılmaksızın otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili dosya algılama** — `nemoclaw` CLI'sinin varlığını kontrol eder ve sandbox bilgisini almak için `nemoclaw status` komutunu çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için tarar, ardından oturumları birim bağlamaları veya `docker cp` üzerinden okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut gösterge
panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir;
böylece bunları standart OpenClaw oturumlarından bir bakışta ayırt edebilirsiniz.

### Önerilen kurulum: sync daemon'u HOST üzerinde

En iyi deneyim için, ClawMetry'nin sync daemon'unu sandbox içinde değil,
**ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından kaçınır.

```bash
# Ana makinede (sandbox dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync daemon'u, çalışan herhangi bir OpenShell konteyneri içindeki oturumları
otomatik olarak bulacaktır.

### İsteğe bağlı: açık sandbox adı

Otomatik algılama çalışmazsa, ClawMetry'yi doğru sandbox'a yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sandbox içinde çalıştırma (ileri düzey)

Sync daemon'unu OpenShell sandbox'ının **içinde** çalıştırmanız gerekiyorsa,
ClawMetry ingest API'sine ulaşabilmesi için NemoClaw ağ politikanıza şu
egress kuralını ekleyin:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Evet (sync daemon → bulut) |
| `localhost:8900` | 8900 | HTTP | Evet (yerel gösterge paneli arayüzü) |
| Docker soketi (`/var/run/docker.sock`) | — | Unix soketi | Konteyner oturum keşfi için |

Sync daemon'u yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları
yapar. Gelen (inbound) port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** dosyasına bakın.

## Test

Bu proje BrowserStack ile test edilmektedir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `https://app.clawmetry.com/api/install` adresine anonim kurulum
yaşam döngüsü ping'leri gönderir: yeni bir makinede `clawmetry` CLI'sini ilk
çalıştırdığınızda bir `install` ping'i, yeni bir sürüme yükselttikten sonraki
ilk çalıştırmada bir `update` ping'i ve gösterge paneli içi katılım seçimini
tamamladığınızda bir `onboarded` ping'i. Bunu, gerçek kurulumları saymak için
kullanıyoruz (ham PyPI indirme sayıları ~%98 oranında yansı sunucular, CI ve
otomatik güncelleme yeniden indirmeleridir) ve pratikte hangi ajan
çerçevelerinin ve sürümlerinin kullanıldığını öğrenmek için.

**Yaşam döngüsü olayı ve sürüm başına en fazla bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` konumunda saklanan rastgele UUID | tekilleştirme; Bulut senkronizasyonunu açıkça bağlayana kadar anonimdir (kimliği doğrulanmış daemon nabız atışı bu kurulumu hesabınıza bağlayarak kimliği taşır) |
| `event` | `install` / `update` / `onboarded` | yeni kurulum mu yoksa mevcut olanın yükseltmesi mi |
| `version` | `0.12.167` | hangi sürümlerin kullanımda olduğu |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürüm destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | sonrasında hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediğimiz veriler**: IP (bulut, ülke kodunu sunucu tarafında
istekten türetir, ardından IP'yi atar), ana bilgisayar adı, kullanıcı adı,
çalışma alanı yolu, dosya içerikleri, api_key'iniz, e-postanız, herhangi bir
KVK veya çalışma alanına özgü veri. Aktarım yükü
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında denetlenebilir.

**Devre dışı bırakma** (aşağıdakilerden herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # kabuk başına
export DO_NOT_TRACK=1                          # W3C çapraz araç standardı
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işareti
```

Buradaki bir ağ hatası, `clawmetry`'nin çalışmasını asla engellemez; ping,
3 saniyelik zaman aşımıyla bir daemon iş parçacığında gönder ve unut
şeklindedir.

## Star Geçmişi

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
  <strong>🦞 Aracınızın düşüncesini görün</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçasıdır</sub>
</p>
