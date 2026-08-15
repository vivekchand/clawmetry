<!-- i18n-src:c422fb7dd0da -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ajanınızın düşüncelerini görün.** **20 farklı AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 16 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için bir gözlemlenebilirlik aracı olarak başladı; şimdi ise makinenizdeki her çalışma zamanını otomatik algılayarak **tüm ajan filonuzu** tek bir gösterge panelinde ölçümlüyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw ve NemoClaw, açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ise ClawMetry Cloud veya kendi barındırdığınız bir Pro lisansı ile devreye girer. Üstbilgiden çalışma zamanını değiştirin; maliyet, token, araçlar, izler gibi her sekme otomatik olarak o çalışma zamanına göre kapsamlanır. Tam ücretsiz/ücretli ayrımı, katman matrisi, `/api/entitlement` şeması ve `clawmetry license` CLI'si için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Kanallar, beyin, araçlar ve geri dönüş arasında akan mesajları gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, etkinlik ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık dökümlerle token ve maliyet takibi
- **Sessions** — Model, token, son etkinlik bilgileriyle aktif ajan oturumları
- **Crons** — Durum, sonraki çalışma zamanı, süre bilgileriyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notları gözden geçirin
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirme
- **Approvals** — Yıkıcı silme işlemlerini, zorla push'ları, veritabanı değişikliklerini, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onaya kilitleyin

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

### 🔐 Security — Güvenlik duruşu ve denetim günlüğü
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Bütçe sınırları, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / E-posta'ya webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onaya kilitleyin; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code için yürütme öncesi engelleme** — tek bir komut, eşleşen
araç çağrılarını çalışmadan *önce* duraklatan ve kararınızı bekleyen bir
PreToolUse hook'u kurar ([bulut push bildirimleri](https://app.clawmetry.com/push)
etkinken telefonunuzdan tek dokunuşla):

```bash
clawmetry hooks install     # ~/.claude/settings.json dosyasına yazar (idempotent)
clawmetry hooks status      # neyin bağlı olduğunu ve kaç politikanın etkin olduğunu gösterir
clawmetry hooks uninstall   # yalnızca ClawMetry'nin girdilerini kaldırır
```

Bir reddetme yalnızca o tek araç çağrısını engeller; ajan oturumunu korur ve
başka bir yaklaşım deneyebilir. Telefonunuzdan onaylamak, Claude Code'un
kendi izin istemini atlar (zaten yanıtladınız). Eşleşmeyen araçlar ~40ms'e
mal olur ve Claude Code'un normal izin akışına düşer. Ayrıca Claude Code'un
kendisi sizi beklerken de telefonunuza push bildirimi alırsınız
(`permission_prompt` / `idle_prompt` bildirimleri).

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

## v2 Ön Yüz Geliştirme

v2 React uygulaması `frontend/` içinde bulunur ve v2 etkinleştirilerek
başlatıldığında Flask sunucusu tarafından `/v2` adresinde sunulur.

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

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini
`http://localhost:8900` adresine yönlendirir, böylece React uygulaması
ekstra CORS ayarına gerek kalmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilecek paketi (bundle) oluşturmak için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` içine yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry yalnızca OpenClaw'ı değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine dönüştüren özel bir okuyucu bağdaştırıcısıyla gelir; daemon bunları aynı DuckDB deposuna + bulut anlık görüntüsüne, çalışma zamanı etiketiyle birlikte aktarır ve birden fazla çalışma zamanı mevcut olduğunda Session replay sekmesi bir **çalışma zamanı değiştirici** gösterir. Tam matris + çalışma zamanı ekleme rehberi için [`docs/compatibility.md`](docs/compatibility.md) dosyasına, OpenClaw ailesine giriş için ise [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) dosyasına bakın.

[Perplexity'nin numbat](https://github.com/perplexityai/numbat) ajan güvenlik aracını mı kullanıyorsunuz? ClawMetry, bulgularını ve uygulama kararlarını kutudan çıktığı gibi alır; bkz. [`docs/NUMBAT.md`](docs/NUMBAT.md).

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
| **n8n** | Beta bağdaştırıcı | SQLite `~/.n8n/database.sqlite`. İş akışı yürütmeleri, düğüm çalışmaları, AI Agent istemleri, n8n'nin kaydettiği yerlerde model + token. |
| **Antigravity** | Beta bağdaştırıcı | `~/.gemini/<flavor>/brain/` altında beyin JSONL'i. Konuşmalar, araç adımları, düşünme, üretim başına Gemini token dağılımı + maliyet, arka plan üretim tüketimi. |
| **GitHub Copilot** | Beta bağdaştırıcı | `~/.copilot/session-state/` altında Copilot CLI `events.jsonl` + çağrı başına kullanım defteri olan `session-store.db`. Konuşmalar, araç çağrıları, model yönlendirme, önbellek duyarlı token dağılımı, satıcı tarafından faturalandırılan AI-kredi maliyeti. |
| **Grok** | Beta bağdaştırıcı | xAI Grok Build CLI (`~/.grok/bin/grok` altında Rust ikili dosyası): genel olay günlüğü `~/.grok/logs/unified.jsonl` + oturum başına `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Konuşmalar, tur başına token dağılımı, model yönlendirme ve CLI'nin makinenizden çıkan içeriği görebilmeniz için `~/.grok/upload_queue/` altında hazırlanan giden repo yükü. |

"Beta bağdaştırıcı", ClawMetry'nin o çalışma zamanının gerçek disk üzerindeki biçimi için bir okuyucu gönderdiği anlamına gelir; her biri gerçek bir makinedeki gerçek bir kurulum üzerinde oluşturulmuş ve doğrulanmıştır (bkz. `tests/fixtures/runtimes/<rt>/`). Bağdaştırıcılar salt okunurdur; her biri kendi çalışma zamanının diske gerçekte ne kaydettiği konusunda dürüsttür (örneğin PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü tek birine kapsamlayarak temiz bir derinlemesine inceleme sağlar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet ilişkilendirme

Yukarıdaki çalışma zamanlarının hepsi oturumları diske yazar. Sizin kendi **üretim ajanınız** ise; OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B veya düz bir `httpx` döngüsü üzerine kurduğunuz o ajan, bunu yapmaz. ClawMetry'nin sıfır yapılandırmalı yakalayıcısı, `httpx`/`requests`'i maymun yaması (monkey-patch) yaparak yine de LLM çağrılarını (maliyet, token, gecikme, hatalar) yakalar:

```python
import clawmetry.track            # yakalayıcıyı etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürünü adlandır

# ...ajanınız normal şekilde çalışır; artık her LLM çağrısı izlenip ilişkilendirilir.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her çağrıyı **adlandırılmış bir kaynak** ile etiketler; böylece çalıştırdığınız her ürün, gösterge panelinin Overview sekmesindeki **🔌 Döngü dışı kaynaklar** kartında kendi başına, maliyeti ilişkilendirilebilir bir satır olarak görünür; ajan başına çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak ayarlanmadıysa? Çağrılar yine izlenir; kart sadece gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı bağdaştırıcılarının beslediği aynı veri katmanıdır (DuckDB → bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar da her şey gibi, uçtan uca şifrelenmiş olarak buluta senkronize edilir.

## OpenTelemetry — satıcıdan bağımsız, izlerinizi istediğiniz yere gönderin

ClawMetry, **GenAI semantik kurallarını** kullanarak her iki yönde de **OpenTelemetry** konuşur, böylece ajan izleriniz asla tek bir araca kilitlenmez.

Her oturumu; LLM çağrıları, araçlar, alt ajanlar, token'lar, maliyet, herhangi bir toplayıcıya (Datadog, Grafana, Honeycomb veya kendi OTel Collector'ınız) OTLP/HTTP GenAI izleri olarak **dışa aktarın**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# eşdeğer olarak:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Kimlik doğrulama başlıkları ve sorgulama aralığı isteğe bağlı ortam değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # ek HTTP başlıkları
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # saniye (varsayılan 60)
```

**İçe Aktar** — yerleşik OTLP alıcısı, `/v1/traces`, `/v1/logs` ve `/v1/metrics` adreslerinde başka herhangi bir yerden izleri, günlükleri ve metrikleri kabul eder. OpenTelemetry ile donatılmış herhangi bir uygulamayı buna yönlendirin:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON izleri ve günlükleri, ekstra bir şey gerekmeden düz bir `pip install clawmetry` üzerinde çalışır. Protobuf içe aktarma (ve OTLP/JSON metrikleri) `pip install clawmetry[otel]` gerektirir. Kendi `service.name` değerini ayarlayan bir uygulama, çalışma zamanı değiştiricide kendi maliyeti ve token'larıyla birlikte kendi ajanı olarak görünür.

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **hem de** verilerinizi ekibinizin zaten çalıştırdığı herhangi bir arka uçta elde edersiniz; kilitlenme yok, kurulacak ikinci bir ajan yok.

## Yapılandırma

Çoğu kişinin herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma alanınızı, günlüklerinizi, oturumlarınızı ve zamanlanmış işlerinizi otomatik algılar.

Özelleştirme ihtiyacınız varsa:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Yalnızca localhost'a bağlan
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesindeki adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı etkinlik gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten kurulu olan kanallar Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj sayılarıyla canlı bir sohbet balonu görünümü görebilirsiniz.

| Kanal | Durum | Canlı Açılır Pencere | Notlar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Tam | ✅ | Mesajlar, istatistikler, 10s yenileme |
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
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi barındırdığınız takım sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkezi olmayan, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkezi olmayan NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry, `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları oluşturur. Manuel kurulum gerekmez.

## Docker ile Dağıtım

ClawMetry'yi bir konteynerde mi çalıştırmak istiyorsunuz? Sorun değil! 🐳

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

> **Not:** Docker içinde çalıştırırken, ClawMetry'nin kurulumunuzu otomatik algılayabilmesi için ajanınızın veri + günlük dizinlerini (örn. `~/.openclaw`, `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip aracılığıyla otomatik kurulur)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok veya QM (veya Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, OpenClaw ajanlarını sandbox'lanmış OpenShell konteynerleri içinde çalıştıran NVIDIA'nın kurumsal güvenlik sarmalayıcısı [NemoClaw](https://github.com/NVIDIA/NemoClaw)'yu otomatik algılar.

Çoğu durumda ekstra yapılandırma gerekmez. Senkronizasyon daemon'u, oturum dosyalarının ister ana makinede `~/.openclaw/` içinde ister bir OpenShell konteyneri içinde olsun otomatik olarak bulur.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili dosya algılama** — `nemoclaw` CLI'sini kontrol eder ve sandbox bilgisini almak için `nemoclaw status` çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için tarar, ardından oturumları birim bağlantıları veya `docker cp` üzerinden okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut gösterge panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir; böylece bunları standart OpenClaw oturumlarından ilk bakışta ayırt edebilirsiniz.

### Önerilen kurulum: ana makinede senkronizasyon daemon'u

En iyi deneyim için, ClawMetry'nin senkronizasyon daemon'unu sandbox içinde değil **ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından kaçınır.

```bash
# Ana makinede (sandbox dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Senkronizasyon daemon'u, çalışan herhangi bir OpenShell konteyneri içindeki oturumları otomatik olarak bulur.

### İsteğe bağlı: açık sandbox adı

Otomatik algılama çalışmazsa, ClawMetry'yi doğru sandbox'a yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sandbox içinde çalıştırma (ileri düzey)

Senkronizasyon daemon'unu OpenShell sandbox'ı **içinde** çalıştırmanız gerekiyorsa, ClawMetry ingest API'sine ulaşabilmesi için NemoClaw ağ politikanıza şu giden (egress) kuralını ekleyin:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Evet (senkronizasyon daemon'u → bulut) |
| `localhost:8900` | 8900 | HTTP | Evet (yerel gösterge paneli arayüzü) |
| Docker soketi (`/var/run/docker.sock`) | — | Unix soketi | Konteyner oturum keşfi için |

Senkronizasyon daemon'u yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları yapar. Herhangi bir gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**'na bakın.

## Test

Bu proje BrowserStack ile test edilmiştir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `https://app.clawmetry.com/api/install` adresine anonim
kurulum yaşam döngüsü pingleri gönderir: `clawmetry` CLI'sini yeni bir
makinede ilk çalıştırdığınızda bir `install` pingi, yeni bir sürüme
yükselttikten sonraki ilk çalıştırmada bir `update` pingi ve gösterge
panelindeki katılım seçimini tamamladığınızda bir `onboarded` pingi.
Bunu, gerçek kurulum sayısını saymak için kullanıyoruz (ham PyPI indirme
rakamlarının ~%98'i yansı sunucular, CI ve otomatik güncelleme yeniden
indirmeleridir) ve hangi ajan çerçevelerinin ve sürümlerinin gerçekte
kullanımda olduğunu öğrenmek için.

**Yaşam döngüsü olayı ve sürüm başına en fazla bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` içinde saklanan rastgele UUID | tekrarları önleme; Bulut senkronizasyonunu açıkça bağlayana kadar anonimdir (kimliği doğrulanmış daemon nabız atışı daha sonra bunu taşır ve bu kurulumu hesabınızla ilişkilendirir) |
| `event` | `install` / `update` / `onboarded` | yeni kurulum mu yoksa var olanın yükseltilmesi mi |
| `version` | `0.12.167` | kullanımda olan sürümler |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürüm destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | bundan sonra hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediğimiz şeyler**: IP adresi (bulut, ülke kodunu sunucu
tarafında istekten türetir, ardından IP'yi atar), ana bilgisayar adı,
kullanıcı adı, çalışma alanı yolu, dosya içerikleri, api_key'iniz,
e-postanız, kişisel veya çalışma alanına özgü herhangi bir şey. Kablo
üzerindeki (wire) yük, [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
dosyasında denetlenebilir.

**Devre dışı bırakma** (bunlardan herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # kabuk başına
export DO_NOT_TRACK=1                          # W3C araçlar arası standart
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işaretçisi
```

Buradaki bir ağ hatası, `clawmetry`'nin çalışmasını asla engellemez;
ping, 3 saniyelik zaman aşımı olan bir daemon iş parçacığında ateşle ve
unut (fire-and-forget) şeklindedir.

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
  <strong>🦞 Ajanınızın düşüncelerini görün</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçasıdır</sub>
</p>
