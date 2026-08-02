<!-- i18n-src:0e34918f8f2e -->
> Türkçe translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Aracınızın düşünme sürecini görün.** **14 AI ajan çalışma zamanı** için gerçek zamanlı gözlemlenebilirlik: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ve 10 tane daha. Tüm ajan filonuz için tek bir gösterge paneli.

> 🌐 **Bunu şu dillerde okuyun:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [daha fazlası →](docs/i18n/)

Tek komut. Sıfır yapılandırma. Her şeyi otomatik algılar.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** adresinde açılır ve işiniz biter.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ajan çalışma zamanıyla çalışır

ClawMetry, OpenClaw için bir gözlemlenebilirlik aracı olarak başladı; şimdi ise makinenizdeki her çalışma zamanını otomatik algılayarak **tüm ajan filonuzu** tek bir gösterge panelinde ölçümlüyor:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw ve NemoClaw açık kaynaklı uygulamada ücretsizdir; diğer çalışma zamanları ise ClawMetry Cloud veya self-hosted bir Pro lisansıyla etkinleşir. Üst bilgiden çalışma zamanını değiştirin; maliyet, token, araçlar, izler gibi her sekme o çalışma zamanına göre yeniden kapsamlanır. Tam ücretsiz/ücretli ayrımı, kademe matrisi, `/api/entitlement` şeması ve `clawmetry license` CLI'ı için **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** dosyasına bakın.

## Neler Elde Edersiniz

- **Flow** — Kanallar, beyin, araçlar arasında akan mesajları gösteren canlı animasyonlu diyagram
- **Overview** — Sağlık kontrolleri, aktivite ısı haritası, oturum sayıları, model bilgisi
- **Usage** — Günlük/haftalık/aylık kırılımlarla token ve maliyet takibi
- **Sessions** — Model, token, son aktivite bilgisiyle aktif ajan oturumları
- **Crons** — Durum, sonraki çalıştırma, süre bilgisiyle zamanlanmış işler
- **Logs** — Renk kodlu gerçek zamanlı log akışı
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md ve günlük notları göz atın
- **Transcripts** — Oturum geçmişlerini okumak için sohbet balonu arayüzü
- **Alerts** — Bütçe sınırları, hata oranı tetikleyicileri, ajan çevrimdışı algılama; Slack, Discord, PagerDuty, Telegram, E-postaya yönlendirir
- **Approvals** — Yıkıcı silmeleri, force push'ları, veritabanı değişikliklerini, sudo'yu, paket kurulumlarını, ağ çağrılarını tek tıkla onaya bağlayın

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
çağrılarını *çalışmadan önce* duraklatan ve kararınızı bekleyen bir
PreToolUse hook'u kurar ([bulut push bildirimleri](https://app.clawmetry.com/push) etkinleştirildiğinde
telefonunuzdan tek dokunuşla):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Bir reddetme yalnızca o tek araç çağrısını engeller; ajan oturumunu korur ve
başka bir yaklaşım deneyebilir. Telefonunuzdan onaylamak, Claude Code'un kendi
izin isteğini atlar (zaten yanıtlamış oldunuz). Eşleşmeyen araçlar ~40ms
maliyete neden olur ve Claude Code'un normal izin akışına düşer. Ayrıca
Claude Code'un kendisi sizi beklediğinde de bir telefon bildirimi alırsınız
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

v2 React uygulaması `frontend/` içinde yer alır ve Flask sunucusu v2
etkinleştirilerek başlatıldığında `/v2` yolunda sunulur.

Geliştirme sırasında iki terminal kullanın:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` adresini açın. Vite, `/api` isteklerini
`http://localhost:8900` adresine proxy'ler; böylece React uygulaması ekstra
CORS ayarı olmadan yerel Flask sunucusuyla konuşabilir.

Python paketiyle birlikte gönderilecek paketi derlemek için:

```bash
cd frontend
npm run build
```

Üretim paketi `clawmetry/static/v2/dist/` konumuna yazılır.

## Çalışma Zamanı / Ajan Uyumluluğu

ClawMetry yalnızca OpenClaw'ı değil, birçok AI ajan çalışma zamanını gözlemler. OpenClaw dışındaki her çalışma zamanı, kendi yerel oturum biçimini ClawMetry'nin birleşik şekillerine dönüştüren özel bir okuyucu adaptörüyle gelir; daemon bunları aynı DuckDB deposuna + bulut anlık görüntüsüne, çalışma zamanı etiketiyle alır ve Session replay sekmesi birden fazla çalışma zamanı bulunduğunda bir **çalışma zamanı değiştirici** gösterir. Tam matris + çalışma zamanı ekleme kılavuzu için [`docs/compatibility.md`](docs/compatibility.md), OpenClaw ailesi tanıtımı için [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) belgelerine bakın.

[Perplexity'nin numbat](https://github.com/perplexityai/numbat) ajan güvenliği aracını mı çalıştırıyorsunuz? ClawMetry bulgularını ve uygulama kararlarını kutudan çıktığı gibi alır; bkz. [`docs/NUMBAT.md`](docs/NUMBAT.md).

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
| **Antigravity** | Beta adaptör | `~/.gemini/<flavor>/brain/` altında Brain JSONL. Konuşmalar, araç adımları, düşünme, üretim başına Gemini token kırılımı + maliyet, arka plan üretim tüketimi. |
| **GitHub Copilot** | Beta adaptör | `~/.copilot/session-state/` altındaki Copilot CLI `events.jsonl` + çağrı başına kullanım defteri olan `session-store.db`. Konuşmalar, araç çağrıları, model yönlendirme, önbellek duyarlı token kırılımı, satıcı tarafından faturalandırılan AI kredi maliyeti. |

"Beta adaptör", ClawMetry'nin o çalışma zamanının gerçek disk üzerindeki biçimi için bir okuyucu sunduğu ve her birinin gerçek bir makinede gerçek bir kurulum üzerinde inşa edilip doğrulandığı anlamına gelir (bkz. `tests/fixtures/runtimes/<rt>/`). Adaptörler salt okunurdur; her biri çalışma zamanının diske gerçekte ne kaydettiği konusunda dürüsttür (örn. PicoClaw/NanoClaw/Cursor token maliyetini diske yazmaz). Bir düğümde birden fazla çalışma zamanı çalıştığında, çalışma zamanı değiştirici oturumlar görünümünü temiz bir derin inceleme için tek bir çalışma zamanına kapsamlar.

## Herhangi bir SDK ajanını izleyin — döngü dışı maliyet atfı

Yukarıdaki çalışma zamanlarının tümü oturumları diske yazar. Sizin kendi
**üretim ajanınız** ise, OpenAI Agents SDK, LangChain, Vercel AI SDK,
LlamaIndex, E2B veya düz bir `httpx` döngüsü üzerine kurduğunuz o ajan,
yazmaz. ClawMetry'nin sıfır yapılandırmalı interceptor'ı, `httpx`/`requests`'i
monkey-patch ederek yine de LLM çağrılarını (maliyet, token, gecikme,
hatalar) yakalar:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (veya `CLAWMETRY_SOURCE=support-agent` ortam değişkeni), her
çağrıyı **adlandırılmış bir kaynak** ile etiketler; böylece çalıştırdığınız
her ürün, gösterge panelinin Overview sekmesindeki **🔌 Döngü dışı kaynaklar**
kartında kendi başına birinci sınıf, maliyet atfedilebilir bir satır olarak
görünür: ajan başına çağrılar, sağlayıcılar, gecikme, hata oranı. Kaynak
belirlenmediyse çağrılar yine de izlenir; kart sadece gizli kalır.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Bu, çalışma zamanı adaptörlerini besleyen aynı veri katmanıdır (DuckDB →
bulut anlık görüntüsü), bu yüzden döngü dışı kaynaklar da diğer her şey gibi
uçtan uca şifrelenmiş biçimde buluta senkronize olur.

## OpenTelemetry — satıcıdan bağımsız, izlerinizi istediğiniz yere gönderin

ClawMetry, **GenAI anlamsal kurallarını** kullanarak her iki yönde de
**OpenTelemetry** konuşur; böylece ajan izleriniz asla tek bir araca kilitli
kalmaz.

Her oturumu (LLM çağrıları, araçlar, alt ajanlar, tokenlar, maliyet) OTLP/HTTP
GenAI izleri olarak herhangi bir toplayıcıya (Datadog, Grafana, Honeycomb ya
da kendi OTel Collector'ınız) **dışa aktarın**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Kimlik doğrulama başlıkları ve yoklama aralığı isteğe bağlı ortam
değişkenleridir:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**İçe aktarma** — yerleşik OTLP alıcısı, `/v1/traces` ve `/v1/metrics`
yollarında başka her yerden izleri ve metrikleri kabul eder (protobuf içe
aktarımı için `pip install clawmetry[otel]`).

Hem sıfır yapılandırmalı, yerel öncelikli ClawMetry gösterge panelini **hem
de** verilerinizi ekibinizin zaten kullandığı arka uçta elde edersiniz; kilit
yok, kurulacak ikinci bir ajan yok.

## Yapılandırma

Çoğu kişinin herhangi bir yapılandırmaya ihtiyacı yoktur. ClawMetry çalışma
alanınızı, günlüklerinizi, oturumlarınızı ve cron işlerinizi otomatik olarak
algılar.

Özelleştirmeniz gerekiyorsa:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tüm seçenekler: `clawmetry --help`

## Desteklenen Kanallar

ClawMetry, yapılandırdığınız her OpenClaw kanalı için canlı aktiviteyi
gösterir. Yalnızca `openclaw.json` dosyanızda gerçekten kurulmuş kanallar
Flow diyagramında görünür; yapılandırılmamış olanlar otomatik olarak
gizlenir.

Flow'daki herhangi bir kanal düğümüne tıklayarak gelen/giden mesaj
sayılarıyla canlı bir sohbet balonu görünümü görebilirsiniz.

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
| 🔷 **Mattermost** | ✅ Tam | ✅ | Self-hosted takım sohbeti |
| 🟩 **Matrix** | ✅ Tam | ✅ | Merkezi olmayan, E2EE desteği |
| 🟢 **LINE** | ✅ Tam | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Tam | ✅ | Merkezi olmayan NIP-04 DM'ler |
| 🟣 **Twitch** | ✅ Tam | ✅ | IRC bağlantısı üzerinden sohbet |
| 🔷 **Feishu/Lark** | ✅ Tam | ✅ | WebSocket olay aboneliği |
| 🔵 **Zalo** | ✅ Tam | ✅ | Zalo Bot API |

> **Otomatik algılama:** ClawMetry `~/.openclaw/openclaw.json` dosyanızı
> okur ve yalnızca gerçekten yapılandırdığınız kanalları oluşturur. Manuel
> kurulum gerekmez.

## Docker Dağıtımı

ClawMetry'yi bir konteynerde mi çalıştırmak istiyorsunuz? Sorun değil! 🐳

**Docker ile hızlı başlangıç:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
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

> **Not:** Docker içinde çalıştırırken, ClawMetry'nin kurulumunuzu otomatik
> algılayabilmesi için ajanınızın veri + log dizinlerini (örn. `~/.openclaw`,
> `~/.claude`, `~/.codex`) bağlayın.

## Gereksinimler

- Python 3.8+
- Flask (pip ile otomatik olarak kurulur)
- Aynı makinede bir AI ajan çalışma zamanı: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity veya GitHub Copilot (veya Docker için bağlanmış birimler)
- Linux veya macOS

## NemoClaw / OpenShell Desteği

ClawMetry, OpenClaw'ı sandbox'lanmış OpenShell konteynerleri içinde çalıştıran NVIDIA'nın kurumsal güvenlik sarmalayıcısı [NemoClaw](https://github.com/NVIDIA/NemoClaw)'ı otomatik olarak algılar.

Çoğu durumda ekstra yapılandırma gerekmez. Sync daemon, oturum dosyalarının ana makinedeki `~/.openclaw/` dizininde mi yoksa bir OpenShell konteyneri içinde mi olduğunu otomatik olarak keşfeder.

### Nasıl çalışır

ClawMetry, NemoClaw'ı iki şekilde algılar:

1. **İkili dosya algılama** — `nemoclaw` CLI'ını kontrol eder ve sandbox bilgisini almak için `nemoclaw status` çalıştırır
2. **Konteyner algılama** — çalışan Docker konteynerlerini `openshell`, `nemoclaw` veya `ghcr.io/nvidia/` görüntüleri için tarar, ardından birim bağlantıları veya `docker cp` üzerinden oturumları okur

NemoClaw konteynerlerinden senkronize edilen oturum dosyaları, bulut gösterge panelinde `runtime=nemoclaw` ve `container_id` meta verisiyle etiketlenir; böylece bunları standart OpenClaw oturumlarından bir bakışta ayırt edebilirsiniz.

### Önerilen kurulum: sync daemon'ı HOST üzerinde çalıştırın

En iyi deneyim için ClawMetry'nin sync daemon'ını sandbox içinde değil,
**ana makinede** çalıştırın. Bu, NemoClaw ağ politikası kısıtlamalarından
kaçınır.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync daemon, çalışan herhangi bir OpenShell konteyneri içindeki oturumları
otomatik olarak bulur.

### İsteğe bağlı: açık sandbox adı

Otomatik algılama çalışmazsa, ClawMetry'yi doğru sandbox'a yönlendirin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Sandbox içinde çalıştırma (ileri düzey)

Sync daemon'ı OpenShell sandbox'ı **içinde** çalıştırmanız gerekiyorsa,
ClawMetry ingest API'sine ulaşabilmesi için NemoClaw ağ politikanıza şu
çıkış (egress) kuralını ekleyin:

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
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Konteyner oturumu keşfi için |

Sync daemon yalnızca `ingest.clawmetry.com` adresine giden HTTPS çağrıları
yapar. Gelen port gerekmez.

---

## Bulut Dağıtımı

SSH tünelleri, ters proxy ve Docker için **[Bulut Test Kılavuzu](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**'na bakın.

## Test

Bu proje BrowserStack ile test edilmektedir.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry, `https://app.clawmetry.com/api/install` adresine anonim kurulum
yaşam döngüsü sinyalleri gönderir: yeni bir makinede `clawmetry` CLI'ını ilk
çalıştırdığınızda bir `install` sinyali, yeni bir sürüme yükseltildikten
sonraki ilk çalıştırmada bir `update` sinyali ve gösterge panelindeki
onboarding seçimini tamamladığınızda bir `onboarded` sinyali. Bunu, gerçek
kurulumları saymak için kullanıyoruz (ham PyPI indirme sayıları yaklaşık %98
oranında yansı sunucular, CI ve otomatik güncelleme yeniden indirmelerinden
oluşur) ve gerçekte hangi ajan çerçevelerinin ve sürümlerinin kullanımda
olduğunu öğrenmek için.

**Yaşam döngüsü olayı ve sürüm başına en fazla bir POST**, şunları içerir:

| Alan | Örnek | Neden |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` konumunda saklanan rastgele UUID | tekilleştirme; Bulut senkronizasyonunu açıkça bağlayana kadar anonimdir (kimliği doğrulanmış daemon nabız sinyali, bu kurulumu hesabınıza bağlayarak bunu taşır) |
| `event` | `install` / `update` / `onboarded` | yeni kurulum mu yoksa mevcut olanın yükseltmesi mi |
| `version` | `0.12.167` | kullanımda olan sürümler |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform desteği öncelikleri |
| `python` | `3.11.15` | Python sürümü destek matrisi |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | sırada hangi ajanlarla entegre olmamız gerektiği |
| `is_ci` / `ci_provider` | `true` / `github_actions` | insan kurulumlarını CI gürültüsünden ayırma |

**Göndermediklerimiz**: IP (bulut, ülke kodunu istekten sunucu tarafında
türetir, ardından IP'yi atar), ana bilgisayar adı, kullanıcı adı, çalışma
alanı yolu, dosya içerikleri, api_key'iniz, e-postanız, herhangi bir kişisel
veya çalışma alanına özgü bilgi. Kablo üzerindeki yük
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) dosyasında denetlenebilir.

**Devre dışı bırakma** (bunlardan herhangi biri kalıcı olarak devre dışı bırakır):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Buradaki bir ağ hatası `clawmetry`'nin çalışmasını asla engellemez; sinyal,
3 saniyelik zaman aşımıyla bir daemon iş parçacığında "gönder ve unut"
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
  <strong>🦞 Aracınızın düşünme sürecini görün</strong><br>
  <sub>Geliştiren: <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ekosisteminin bir parçasıdır</sub>
</p>
