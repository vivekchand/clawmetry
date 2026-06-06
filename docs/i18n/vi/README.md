<!-- i18n-src:48548997be76 -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Xem agent của bạn suy nghĩ.** Theo dõi thời gian thực cho **12 runtime agent AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex và 8 runtime khác. Một bảng điều khiển cho toàn bộ đội agent của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một lệnh. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900** và bạn đã xong.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Tương thích với 12 runtime agent

ClawMetry bắt đầu như một công cụ theo dõi cho OpenClaw, và nay theo dõi **toàn bộ đội agent** của bạn trong một bảng điều khiển duy nhất, tự động phát hiện từng runtime trên máy của bạn:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw và NemoClaw miễn phí trong ứng dụng mã nguồn mở; các runtime còn lại được kích hoạt với ClawMetry Cloud hoặc giấy phép Pro tự lưu trữ. Chuyển đổi runtime từ thanh tiêu đề và mọi tab như chi phí, token, công cụ, trace đều được lọc theo runtime đó.

## Những gì bạn nhận được

- **Flow** — Sơ đồ hoạt hình trực tiếp hiển thị tin nhắn di chuyển qua các kênh, não, công cụ và quay trở lại
- **Overview** — Kiểm tra sức khỏe, bản đồ nhiệt hoạt động, số phiên, thông tin mô hình
- **Usage** — Theo dõi token và chi phí theo ngày/tuần/tháng
- **Sessions** — Các phiên agent đang hoạt động với mô hình, token, hoạt động gần nhất
- **Crons** — Các công việc định kỳ với trạng thái, lần chạy tiếp theo, thời lượng
- **Logs** — Truyền phát nhật ký thời gian thực có màu sắc
- **Memory** — Duyệt SOUL.md, MEMORY.md, AGENTS.md, ghi chú hằng ngày
- **Transcripts** — Giao diện bong bóng chat để đọc lịch sử phiên
- **Alerts** — Giới hạn ngân sách, kích hoạt tỷ lệ lỗi, phát hiện agent ngoại tuyến; gửi đến Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Chặn các thao tác xóa nguy hiểm, force push, biến đổi DB, sudo, cài đặt gói, lệnh gọi mạng bằng phê duyệt một cú nhấp

## Ảnh chụp màn hình

### 🧠 Brain — Luồng sự kiện agent trực tiếp
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Sử dụng token và tóm tắt phiên
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Nguồn cung cấp lệnh gọi công cụ thời gian thực
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Phân tích chi phí theo mô hình và phiên
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Trình duyệt tệp không gian làm việc
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Tình trạng bảo mật và nhật ký kiểm toán
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Giới hạn ngân sách, kích hoạt tỷ lệ lỗi, webhook đến Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Chặn các lệnh gọi công cụ rủi ro bằng phê duyệt thủ công; quy tắc bảo vệ dựa trên chính sách
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Cài đặt

**Một lệnh (khuyến nghị):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Từ mã nguồn:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Phát triển Frontend v2

Ứng dụng React v2 nằm trong `frontend/` và được phục vụ tại `/v2` khi máy chủ Flask được khởi động với v2 được bật.

Sử dụng hai terminal trong khi phát triển:

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

Mở `http://localhost:5173/v2/`. Vite ủy quyền các yêu cầu `/api` đến `http://localhost:8900`, vì vậy ứng dụng React có thể giao tiếp với máy chủ Flask cục bộ mà không cần thiết lập CORS thêm.

Để build gói đi kèm với gói Python:

```bash
cd frontend
npm run build
```

Gói sản xuất được ghi vào `clawmetry/static/v2/dist/`.

## Khả năng tương thích Runtime / Agent

ClawMetry theo dõi nhiều runtime agent AI, không chỉ OpenClaw. Mỗi runtime không phải OpenClaw đi kèm một bộ chuyển đổi đọc chuyên dụng dịch định dạng phiên gốc của nó sang các hình dạng thống nhất của ClawMetry; daemon nhập chúng vào cùng kho DuckDB và ảnh chụp đám mây, được gắn thẻ theo runtime, và tab Phát lại phiên hiển thị **bộ chuyển đổi runtime** khi có nhiều hơn một. Xem [`docs/compatibility.md`](docs/compatibility.md) để biết ma trận đầy đủ cùng hướng dẫn thêm runtime, và [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) để tìm hiểu về dòng OpenClaw.

| Runtime / Agent | Trạng thái | Ghi chú |
|---|---|---|
| **OpenClaw** | Gốc | Runtime tham chiếu, tự động phát hiện |
| **PicoClaw** | Bộ chuyển đổi Beta | JSONL `providers.Message` phẳng (`~/.picoclaw/workspace/sessions`). Bản ghi, mô hình, lệnh gọi công cụ. |
| **NanoClaw** | Bộ chuyển đổi Beta | SQLite theo phiên (`data/v2-sessions`). Bản ghi và số lượng tin nhắn. |
| **Hermes** | Bộ chuyển đổi Beta | SQLite `~/.hermes/state.db`. Bản ghi, mô hình, token/chi phí. |
| **Claude Code** | Bộ chuyển đổi Beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Bản ghi, mô hình, lệnh gọi công cụ và suy nghĩ, sử dụng token. |
| **Codex** | Bộ chuyển đổi Beta | JSONL triển khai `~/.codex/sessions/...`. Bản ghi, mô hình, lệnh gọi công cụ, sử dụng token. |
| **Cursor** | Bộ chuyển đổi Beta | SQLite `state.vscdb`. Bản ghi chat/composer, mô hình. |
| **Aider** | Bộ chuyển đổi Beta | `.aider.chat.history.md` theo dự án. Bản ghi, mô hình, số lượng token. |
| **Goose** | Bộ chuyển đổi Beta | SQLite `~/.local/share/goose`. Bản ghi, mô hình, lệnh gọi công cụ, tổng token. |
| **opencode** | Bộ chuyển đổi Beta | SQLite `~/.local/share/opencode`. Bản ghi, mô hình, lệnh gọi công cụ, token và chi phí. |
| **Qwen Code** | Bộ chuyển đổi Beta | JSONL `~/.qwen/projects/.../chats`. Bản ghi, mô hình, lệnh gọi công cụ, sử dụng token. |

"Bộ chuyển đổi Beta" có nghĩa là ClawMetry cung cấp một trình đọc cho định dạng trên đĩa thực của runtime đó, mỗi bộ được xây dựng và xác minh dựa trên cài đặt thực trên máy thực (xem `tests/fixtures/runtimes/<rt>/`). Các bộ chuyển đổi chỉ đọc; mỗi bộ trung thực về những gì runtime của nó thực sự lưu trữ (ví dụ PicoClaw/NanoClaw/Cursor không ghi chi phí token ra đĩa). Khi nhiều runtime chạy trên một nút, bộ chuyển đổi runtime thu hẹp chế độ xem phiên về một runtime để phân tích sâu gọn gàng.

## Theo dõi bất kỳ agent SDK nào, gán chi phí ngoài vòng lặp

Các runtime trên đều ghi phiên ra đĩa. **Agent sản xuất** của bạn, cái bạn xây dựng trên OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, hay một vòng lặp `httpx` đơn giản thì không. Bộ chặn không cần cấu hình của ClawMetry vẫn thu thập các lệnh gọi LLM của nó (chi phí, token, độ trễ, lỗi) bằng cách vá monkey `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (hoặc biến môi trường `CLAWMETRY_SOURCE=support-agent`) gắn thẻ mỗi lệnh gọi với một **nguồn được đặt tên**, vì vậy mọi sản phẩm bạn chạy đều hiển thị dưới dạng dòng riêng có thể gán chi phí trong thẻ **🔌 Nguồn ngoài vòng lặp** trên Overview của bảng điều khiển, bao gồm lệnh gọi, nhà cung cấp, độ trễ, tỷ lệ lỗi theo agent. Không đặt nguồn? Các lệnh gọi vẫn được theo dõi; thẻ chỉ ẩn đi.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Đây là cùng lớp dữ liệu mà các bộ chuyển đổi runtime cung cấp (DuckDB thành ảnh chụp đám mây), vì vậy các nguồn ngoài vòng lặp đồng bộ hóa lên bảng điều khiển đám mây giống như mọi thứ khác, được mã hóa đầu cuối.

## OpenTelemetry — trung lập với nhà cung cấp, gửi trace của bạn đến bất kỳ đâu

ClawMetry hỗ trợ **OpenTelemetry** theo cả hai hướng, sử dụng **quy ước ngữ nghĩa GenAI**, vì vậy các trace agent của bạn không bao giờ bị khóa vào một công cụ.

**Xuất** mọi phiên, bao gồm lệnh gọi LLM, công cụ, sub-agent, token, chi phí dưới dạng OTLP/HTTP GenAI span đến bất kỳ collector nào (Datadog, Grafana, Honeycomb, hoặc OTel Collector của riêng bạn):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Header xác thực và khoảng thời gian thăm dò là các biến môi trường tùy chọn:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Nhập** — bộ nhận OTLP tích hợp chấp nhận trace và số liệu từ bất kỳ nguồn nào tại `/v1/traces` và `/v1/metrics` (`pip install clawmetry[otel]` để nhập protobuf).

Bạn có bảng điều khiển ClawMetry không cần cấu hình, ưu tiên cục bộ **và** dữ liệu của bạn trong bất kỳ backend nào mà nhóm bạn đang sử dụng, không bị khóa, không cần cài đặt agent thứ hai.

## Cấu hình

Hầu hết mọi người không cần cấu hình gì. ClawMetry tự động phát hiện không gian làm việc, nhật ký, phiên và cron của bạn.

Nếu bạn cần tùy chỉnh:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tất cả các tùy chọn: `clawmetry --help`

## Các kênh được hỗ trợ

ClawMetry hiển thị hoạt động trực tiếp cho mọi kênh OpenClaw bạn đã cấu hình. Chỉ các kênh thực sự được thiết lập trong `openclaw.json` của bạn mới xuất hiện trong sơ đồ Flow, những kênh chưa cấu hình sẽ tự động bị ẩn.

Nhấp vào bất kỳ nút kênh nào trong Flow để xem chế độ xem bong bóng chat trực tiếp với số lượng tin nhắn đến/đi.

| Kênh | Trạng thái | Cửa sổ trực tiếp | Ghi chú |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Đầy đủ | ✅ | Tin nhắn, thống kê, làm mới 10 giây |
| 💬 **iMessage** | ✅ Đầy đủ | ✅ | Đọc `~/Library/Messages/chat.db` trực tiếp |
| 💚 **WhatsApp** | ✅ Đầy đủ | ✅ | Qua WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Đầy đủ | ✅ | Qua signal-cli |
| 🟣 **Discord** | ✅ Đầy đủ | ✅ | Phát hiện Guild và kênh |
| 🟪 **Slack** | ✅ Đầy đủ | ✅ | Phát hiện workspace và kênh |
| 🌐 **Webchat** | ✅ Đầy đủ | ✅ | Phiên giao diện web tích hợp |
| 📡 **IRC** | ✅ Đầy đủ | ✅ | Giao diện bong bóng kiểu terminal |
| 🍏 **BlueBubbles** | ✅ Đầy đủ | ✅ | iMessage qua BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Đầy đủ | ✅ | Qua webhook Chat API |
| 🟣 **MS Teams** | ✅ Đầy đủ | ✅ | Qua plugin bot Teams |
| 🔷 **Mattermost** | ✅ Đầy đủ | ✅ | Chat nhóm tự lưu trữ |
| 🟩 **Matrix** | ✅ Đầy đủ | ✅ | Phi tập trung, hỗ trợ E2EE |
| 🟢 **LINE** | ✅ Đầy đủ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Đầy đủ | ✅ | DM phi tập trung NIP-04 |
| 🟣 **Twitch** | ✅ Đầy đủ | ✅ | Chat qua kết nối IRC |
| 🔷 **Feishu/Lark** | ✅ Đầy đủ | ✅ | Đăng ký sự kiện WebSocket |
| 🔵 **Zalo** | ✅ Đầy đủ | ✅ | Zalo Bot API |

> **Tự động phát hiện:** ClawMetry đọc `~/.openclaw/openclaw.json` của bạn và chỉ hiển thị các kênh bạn đã thực sự cấu hình. Không cần thiết lập thủ công.

## Triển khai Docker

Muốn chạy ClawMetry trong container? Không có gì phức tạp! 🐳

**Khởi động nhanh với Docker:**

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

**Ví dụ Docker Compose:**

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

> **Lưu ý:** Khi chạy trong Docker, hãy gắn kết các thư mục dữ liệu và nhật ký của agent (ví dụ `~/.openclaw`, `~/.claude`, `~/.codex`) để ClawMetry có thể tự động phát hiện cài đặt của bạn.

## Yêu cầu

- Python 3.8 trở lên
- Flask (tự động cài đặt qua pip)
- Một runtime agent AI trên cùng máy: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw hoặc PicoClaw (hoặc volume đã gắn kết cho Docker)
- Linux hoặc macOS

## Hỗ trợ NemoClaw / OpenShell

ClawMetry tự động phát hiện [NemoClaw](https://github.com/NVIDIA/NemoClaw), lớp bọc bảo mật doanh nghiệp của NVIDIA cho OpenClaw chạy các agent bên trong các container OpenShell được sandbox hóa.

Hầu hết các trường hợp không cần cấu hình thêm. Daemon đồng bộ hóa tự động tìm các tệp phiên dù chúng nằm trong `~/.openclaw/` trên máy chủ hay bên trong một container OpenShell.

### Cách hoạt động

ClawMetry phát hiện NemoClaw theo hai cách:

1. **Phát hiện nhị phân** — kiểm tra CLI `nemoclaw` và chạy `nemoclaw status` để lấy thông tin sandbox
2. **Phát hiện container** — quét các container Docker đang chạy có hình ảnh `openshell`, `nemoclaw`, hoặc `ghcr.io/nvidia/`, sau đó đọc phiên qua volume mount hoặc `docker cp`

Các tệp phiên được đồng bộ từ container NemoClaw được gắn thẻ `runtime=nemoclaw` và siêu dữ liệu `container_id` trong bảng điều khiển đám mây, để bạn có thể phân biệt chúng với các phiên OpenClaw tiêu chuẩn chỉ bằng một cái nhìn.

### Thiết lập khuyến nghị: daemon đồng bộ trên MÁY CHỦ

Để có trải nghiệm tốt nhất, hãy chạy daemon đồng bộ của ClawMetry trên **máy chủ** (không phải bên trong sandbox). Điều này tránh các hạn chế chính sách mạng của NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon đồng bộ sẽ tự động tìm các phiên bên trong bất kỳ container OpenShell đang chạy nào.

### Tùy chọn: tên sandbox rõ ràng

Nếu tự động phát hiện không hoạt động, hãy chỉ ClawMetry đến sandbox đúng:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Chạy bên trong sandbox (nâng cao)

Nếu bạn phải chạy daemon đồng bộ **bên trong** sandbox OpenShell, hãy thêm quy tắc egress này vào chính sách mạng NemoClaw của bạn để nó có thể đến ClawMetry ingest API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Áp dụng bằng:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Cổng và điểm cuối

| Điểm cuối | Cổng | Giao thức | Bắt buộc |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Có (daemon đồng bộ thành đám mây) |
| `localhost:8900` | 8900 | HTTP | Có (giao diện bảng điều khiển cục bộ) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Để khám phá phiên container |

Daemon đồng bộ chỉ thực hiện các lệnh gọi HTTPS ra ngoài đến `ingest.clawmetry.com`. Không cần cổng vào.

---

## Triển khai đám mây

Xem **[Hướng dẫn kiểm tra đám mây](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** để biết về SSH tunnel, reverse proxy và Docker.

## Kiểm tra

Dự án này được kiểm tra với BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry gửi một ping ẩn danh "lần chạy đầu tiên" đến
`https://app.clawmetry.com/api/install` lần đầu tiên bạn chạy CLI
`clawmetry` trên máy mới. Chúng tôi dùng thông tin này để đếm số lần cài đặt (số liệu tiếp thị duy nhất chúng tôi có cho một dự án OSS) và tìm hiểu các framework agent mà người dùng đã cài đặt.

**Chính xác một POST mỗi lần cài đặt**, chứa:

| Trường | Ví dụ | Lý do |
|---|---|---|
| `install_id` | UUID ngẫu nhiên được lưu tại `~/.clawmetry/install_id` | Loại trùng lặp; không liên kết với email hay api_key của bạn |
| `version` | `0.12.167` | Các phiên bản nào đang được sử dụng |
| `os` / `os_version` | `Darwin` / `25.3.0` | Ưu tiên hỗ trợ nền tảng |
| `python` | `3.11.15` | Ma trận hỗ trợ phiên bản Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | Agent nào chúng tôi nên tích hợp tiếp theo |
| `is_ci` / `ci_provider` | `true` / `github_actions` | Phân biệt lần cài đặt của người thật với CI |

**Những gì chúng tôi KHÔNG gửi**: IP (đám mây lấy mã quốc gia phía máy chủ từ yêu cầu, sau đó loại bỏ IP), tên máy chủ, tên người dùng, đường dẫn không gian làm việc, nội dung tệp, api_key, email của bạn, bất kỳ thông tin cá nhân hay nội dung riêng của không gian làm việc nào. Dữ liệu truyền tải có thể kiểm tra tại
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Từ chối** (bất kỳ cách nào trong số này sẽ vô hiệu hóa vĩnh viễn):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Lỗi mạng ở đây không bao giờ chặn `clawmetry` khỏi việc chạy,
ping được gửi theo kiểu fire-and-forget trên một luồng daemon với thời gian chờ 3 giây.

## Lịch sử sao

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Giấy phép

MIT

---

<p align="center">
  <strong>🦞 Xem agent của bạn suy nghĩ</strong><br>
  <sub>Được xây dựng bởi <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Một phần của hệ sinh thái <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
