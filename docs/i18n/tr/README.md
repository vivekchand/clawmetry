<!-- i18n-src:7cfb63716507 -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Ajanınızın düşünme sürecini görün.** **14 AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 10 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için gözlemlenebilirlik olarak başladı ve şimdi makinenizdeki her çalışma zamanını otomatik algılayarak **tüm ajan filonuzu** tek bir gösterge panelinde ölçümlüyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw ve NemoClaw açık kaynak uygulamada ücretsizdir; diğer çalışma zamanları ClawMetry Cloud veya kendi barındırdığınız bir Pro lisansıyla etkinleşir. Başlıktan çalışma zamanını değiştirin ve her sekme (maliyet, token, araçlar, izler) o çalışma zamanına göre yeniden kapsamlanır. Tam ücretsiz/ücretli ayrımı, katman matrisi, `/api/entitlement` şekli ve `clawmetry license` CLI'si için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Kanallar, beyin, araçlar ve geri dönüş arasında akan mesajları gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, aktivite ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık dökümlerle token ve maliyet takibi
- **Sessions** — Model, token, son aktivite bilgileriyle aktif ajan oturumları
- **Crons** — Durum, sonraki çalışma zamanı, süre bilgileriyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı günlük akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notları gözden geçirin
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, E-posta'ya yönlendirir
- **Approvals** — Yıkıcı silmeleri, force push'ları, DB mutasyonlarını, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onay arkasında kilitler

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

### 🚨 Alerts — Bütçe sınırları, hata oranı tetikleyicileri, Slack / Discord / PagerDuty / E-posta'ya webhook'lar
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskli araç çağrılarını manuel onay arkasında kilitleyin; politika destekli koruma kuralları
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code için çalıştırma öncesi engelleme** — tek bir komut, eşleşen araç
çağrılarını *çalışmadan önce* duraklatan ve kararınızı bekleyen bir
PreToolUse hook'u kurar (telefonunuzdan tek dokunuşla,
[bulut push bildirimleri](https://app.clawmetry.com/push) etkinken):

```bash
clawmetry hooks install     # ~/.claude/settings.json dosyasına yazar (idempotent)
clawmetry hooks status      # neyin bağlı olduğu + kaç politikanın aktif olduğu
clawmetry hooks uninstall   # yalnızca ClawMetry'nin girdilerini kaldırır
```

Bir reddetme yalnızca o tek araç çağrısını engeller; ajan oturumunu korur ve
başka bir yaklaşım deneyebilir. Telefonunuzdan onaylamak, Claude Code'un kendi
izin istemini atlar (zaten cevapladınız). Eşleşmeyen araçlar ~40ms'e mal olur
ve Claude Code'un normal izin akışına düşer. Ayrıca Claude Code'un kendisi
sizi beklediğinde de telefonunuza push bildirimi alırsınız
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

v2 React uygulaması `frontend/` içinde yaşar ve Flask
sunucusu v2 etkinken başlatıldığında `/v2` adresinde sunulur.

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

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini
`http://localhost:8900` adresine yönlendirir, böylece React uygulaması
ekstra CORS yapılandırması olmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilen paketi oluşturmak için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` konumuna yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry sadece OpenClaw'ı değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine çeviren özel bir okuyucu adaptörüyle gelir; daemon bunları aynı DuckDB deposuna + bulut anlık görüntüsüne alır, çalışma zamanıyla etiketler ve birden fazla çalışma zamanı mevcut olduğunda Session replay sekmesi bir **çalışma zamanı değiştirici** gösterir. Tam matris + çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md) dosyasına, OpenClaw ailesi girişi için [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) dosyasına bakın.

[Perplexity'nin numbat](https://github.com/perplexityai/numbat) ajan güvenliği aracını mı kullanıyorsunuz? ClawMetry, bulgularını ve uygulama kararlarını kutudan çıktığı gibi alır; bkz. [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Çalışma Zamanı / Ajan | Durum | Notlar |
|---|---|---|
| **OpenClaw** | Yerel | Referans çalışma zamanı, otomatik algılanır |
| **PicoClaw** | Beta adaptör | Düz `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkriptler, model, araç çağrıları. |
| **NanoClaw** | Beta adaptör | Oturum başına SQLite (`data/v2-sessions`). Transkriptler + mesaj sayıları. |
| **Hermes** | Beta adaptör | SQLite `~/.hermes/state.db`. Transkriptler, model, token/maliyet. |
| **Claude Code** | Beta adaptör | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkriptler, model, araç çağrıları + düşünme, token kullanımı. |
| **Codex** | Beta adaptör | Rollout JSONL `~/.codex/sessions/...`. Transkriptler, model, araç çağrıları, token kullanımı. |
| **Cursor** | Beta adaptör | SQLite `state.vscdb`. Sohbet/composer transkriptleri, model. |
| **Aider** | Beta adaptör | Proje başına `.aider.chat.history.md`. Transkriptler, model, token sayıları. |
| **Goose** | Beta adaptör | SQLite `~/.local/share/goose`. Transkriptler, model, araç çağrıları, token toplamları. |
| **opencode** | Beta adaptör | SQLite `~/.local/share/opencode`. Transkriptler, model, araç çağrıları, token + maliyet. |
| **Qwen Code** | Beta adaptör | JSONL `~/.qwen/projects/.../chats`. Transkriptler, model, araç çağrıları, token kullanımı. |
| **Pi** | Beta adaptör | JSONL `~/.pi/agent/sessions`. Transkriptler, model, araç çağrıları, token + maliyet. |
| **Deep Agents** | Beta adaptör | SQLite `~/.deepagents/.state/sessions.db`. Transkriptler, model, araç çağrıları, token + maliyet. |
| **n8n** | Beta adaptör | SQLite `~/.n8n/database.sqlite`. İş akışı çalıştırmaları, düğüm çalıştırmaları, AI Agent istemleri, n8n'in kaydettiği yerlerde model + token. |
| **Antigravity** | Beta adaptör | `~/.gemini/<flavor>/brain/` altında Brain JSONL. Konuşmalar, araç adımları, düşünme, üretim başına Gemini token dökümü + maliyet, arka plan üretim tüketimi. |
| **GitHub Copilot** | Beta adaptör | `~/.copilot/session-state/` altında Copilot CLI `events.jsonl` + çağrı başına kullanım defteri `session-store.db`. Konuşmalar, araç çağrıları, model yönlendirme, önbellek farkında token dökümü, satıcı tarafından faturalandırılan AI kredisi maliyeti. |
| **Grok** | Beta adaptör | xAI Grok Build CLI (`~/.grok/bin/grok` altında Rust ikili dosyası): global olay günlüğü `~/.grok/logs/unified.jsonl` + oturum başına `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Konuşmalar, tur başına token dökümü, model yönlendirme ve CLI'nin `~/.grok/upload_queue/` altında bekletilen giden repo yükü, böylece makinenizden neyin çıktığını görebilirsiniz. |

"Beta adaptör", ClawMetry'nin o çalışma zamanının gerçek disk üzerindeki biçimi için bir okuyucu gönderdiği anlamına gelir; her biri gerçek bir makinedeki gerçek bir kuruluma karşı oluşturulmuş + doğrulanmıştır (bkz. `tests/fixtures/runtimes/<rt>/`). Adaptörler salt okunurdur; her biri çalışma zamanının diskte gerçekte neyi sakladığı konusunda dürüsttür (örn. PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü temiz bir derinlemesine inceleme için tek birine kapsamlar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet atfı

Yukarıdaki çalışma zamanlarının tümü oturumları diske yazar. Kendi **üretim ajanınız** ise, OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B veya düz bir `httpx` döngüsü üzerine kurduğunuz ajan, yazmaz. ClawMetry'nin sıfır yapılandırmalı arayakalayıcısı, `httpx`/`requests`'i maymun yamayarak yine de onun LLM çağrılarını (maliyet, token, gecikme, hatalar) yakalar:

```python
import clawmetry.track            # arayakalayıcıyı etkinleştir
clawmetry.track.set_source("support-agent")   # bu ürünü adlandır

# ...ajanınız normal şekilde çalışır; her LLM çağrısı artık izleniyor + atfediliyor.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her çağrıyı adlandırılmış bir **kaynak** ile etiketler, böylece çalıştırdığınız her ürün gösterge panelinin Overview sekmesindeki **🔌 Döngü dışı kaynaklar** kartında kendi başına birinci sınıf, maliyet atfedilebilir bir satır olarak görünür; ajan başına çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak ayarlanmadıysa? Çağrılar yine de izlenir; kart sadece gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı adaptörlerinin beslediği aynı veri katmanıdır (DuckDB → bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar da her şey gibi buluta senkronize olur, uçtan uca şifreli.

## OpenTelemetry — satıcıdan bağımsız, izlerinizi istediğiniz yere gönderin

ClawMetry, **GenAI anlamsal kurallarını** kullanarak her iki yönde de **OpenTelemetry** konuşur, böylece ajan izleriniz asla tek bir araca kilitlenmez.

Her oturumu (LLM çağrıları, araçlar, alt ajanlar, tokenler, maliyet) herhangi bir toplayıcıya (Datadog, Grafana, Honeycomb veya kendi OTel Collector'ınıza) OTLP/HTTP GenAI izleri olarak **dışa aktarın**:

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

**İçe aktarma** — yerleşik OTLP alıcısı, `/v1/traces` ve `/v1/metrics` adreslerinde başka herhangi bir yerden izleri ve metrikleri kabul eder (protobuf içe aktarma için `pip install clawmetry[otel]`).

Sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **ve** ekibinizin zaten çalıştırdığı hangi arka uç olursa olsun verinizi elde edersiniz; kilitlenme yok, kurulacak ikinci bir ajan yok.

## Yapılandırma

Çoğu insanın herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma alanınızı, günlüklerinizi, oturumlarınızı ve zamanlanmış işlerinizi otomatik algılar.

Özelleştirmeniz gerekiyorsa:

```bash
clawmetry --port 9000              # Özel port (varsayılan: 8900)
clawmetry --host 127.0.0.1         # Yalnızca localhost'a bağla
clawmetry --workspace ~/mybot      # Özel çalışma alanı yolu
clawmetry --name "Alice"           # Flow görselleştirmesinde adınız
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı aktivite gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten kurulu olan kanallar Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj sayılarıyla canlı sohbet balonu görünümünü görebilirsiniz.

| Kanal | Durum | Canlı Popup | Notlar |
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
| 🔷 **Mattermost** | ✅ Tam | ✅ | Kendi barındırdığınız ekip sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkeziyetsiz, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkeziyetsiz NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry `~/.openclaw/openclaw.json` dosyanızı okur ve yalnızca gerçekten yapılandırdığınız kanalları görüntüler. Manuel kurulum gerekmez.

## Docker Dağıtımı

ClawMetry'yi bir konteynerde mi çalıştırmak istiyorsunuz? Sorun değil! 🐳

**Docker ile hızlı başlangıç:**

```bash
# İmajı oluştur
docker build -t clawmetry .

# Varsayılan ayarlarla çalıştır
docker run -p 8900:8900 clawmetry

# Veya ajanınızın veri dizinini bağlayın (gösterilen: OpenClaw'ın ~/.openclaw dizini)
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
- Flask (pip ile otomatik olarak kurulur)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok veya QM (veya Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, [NemoClaw](https://github.com/NVIDIA/NemoClaw)'ı otomatik olarak algılar; bu, NVIDIA'nın ajanları sanal alana alınmış OpenShell konteynerleri içinde çalıştıran kurumsal güvenlik sarmalayıcısıdır (OpenClaw için).

Çoğu durumda ekstra yapılandırma gerekmez. Senkronizasyon daemon'u, oturum dosyalarının ana bilgisayarda `~/.openclaw/` içinde veya bir OpenShell konteyneri içinde bulunmasından bağımsız olarak otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili dosya algılama** — `nemoclaw` CLI'sini kontrol eder ve sanal alan bilgisi almak için `nemoclaw status` çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` imajları için tarar, ardından oturumları birim bağlantıları veya `docker cp` üzerinden okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut gösterge panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir, böylece bunları standart OpenClaw oturumlarından bir bakışta ayırt edebilirsiniz.

### Önerilen kurulum: HOST üzerinde senkronizasyon daemon'u

En iyi deneyim için ClawMetry'nin senkronizasyon daemon'unu sanal alanın içinde değil, **ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından kaçınır.

```bash
# Ana makinede (sanal alanın dışında)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Senkronizasyon daemon'u, çalışan herhangi bir OpenShell konteyneri içindeki oturumları otomatik olarak bulur.

### İsteğe bağlı: açık sanal alan adı

Otomatik algılama çalışmazsa, ClawMetry'yi doğru sanal alana yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sanal alan içinde çalıştırma (ileri düzey)

Senkronizasyon daemon'unu OpenShell sanal alanının **içinde** çalıştırmanız gerekiyorsa, ClawMetry ingest API'sine ulaşabilmesi için NemoClaw ağ politikanıza şu çıkış kuralını ekleyin:

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

Senkronizasyon daemon'u yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları yapar. Gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**'na bakın.

## Test

Bu proje BrowserStack ile test edilmektedir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `https://app.clawmetry.com/api/install` adresine anonim kurulum
yaşam döngüsü pingleri gönderir: `clawmetry` CLI'sini yeni bir makinede ilk
çalıştırdığınızda bir `install` pingi, yeni bir sürüme yükselttikten sonraki
ilk çalıştırmada bir `update` pingi ve panel içi başlangıç seçimini
tamamladığınızda bir `onboarded` pingi. Bunu gerçek kurulum sayılarını
saymak için kullanıyoruz (ham PyPI indirme sayıları %98 oranında ayna
sunucular, CI ve otomatik güncelleme yeniden indirmelerinden oluşur) ve
gerçekte hangi ajan çerçevelerinin ve sürümlerinin kullanımda olduğunu
öğrenmek için.

**Sürüm başına yaşam döngüsü olayı başına en fazla bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` içinde saklanan rastgele UUID | tekilleştirme; Bulut senkronizasyonunu açıkça bağlayana kadar anonim (kimliği doğrulanmış daemon kalp atışı daha sonra bunu taşır ve bu kurulumu hesabınıza bağlar) |
| `event` | `install` / `update` / `onboarded` | yeni kurulum mu mevcut olanın yükseltilmesi mi |
| `version` | `0.12.167` | kullanımda hangi sürümlerin olduğu |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürüm destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | sırada hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediklerimiz**: IP (bulut, ülke kodunu istekten sunucu tarafında
türetir, ardından IP'yi atar), ana bilgisayar adı, kullanıcı adı, çalışma
alanı yolu, dosya içerikleri, api_key'iniz, e-postanız, herhangi bir PII
veya çalışma alanına özgü bilgi. Bağlantı yükü
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında denetlenebilir.

**Devre dışı bırakma** (bunlardan herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # kabuk başına
export DO_NOT_TRACK=1                          # W3C çapraz araç standardı
touch ~/.clawmetry/notelemetry                 # kalıcı dosya işaretçisi
```

Buradaki bir ağ hatası `clawmetry`'nin çalışmasını asla engellemez; ping,
3 saniyelik zaman aşımıyla bir daemon iş parçacığında ateşle ve unut
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
  <strong>🦞 Ajanınızın düşünme sürecini görün</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçası</sub>
</p>
