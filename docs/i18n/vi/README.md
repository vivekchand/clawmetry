<!-- i18n-src:8f42d460a973 -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Xem agent của bạn suy nghĩ.** Khả năng quan sát theo thời gian thực cho **14 runtime AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 10 runtime khác. Một dashboard duy nhất cho toàn bộ đội agent của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một lệnh duy nhất. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900** là xong.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Hoạt động với 14 runtime agent

ClawMetry khởi đầu là công cụ quan sát cho OpenClaw, và giờ đây đo lường **toàn bộ đội agent** của bạn trong một dashboard duy nhất, tự động phát hiện từng runtime trên máy của bạn:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw và NemoClaw miễn phí trong ứng dụng mã nguồn mở; các runtime khác được kích hoạt với ClawMetry Cloud hoặc giấy phép Pro tự lưu trữ. Chuyển đổi runtime từ phần đầu trang và mọi tab, chi phí, token, công cụ, trace, sẽ tự động thu hẹp phạm vi theo runtime đó. Xem **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** để biết chi tiết chính xác về phân chia miễn phí/trả phí, ma trận các gói, cấu trúc `/api/entitlement`, và CLI `clawmetry license`.

## Bạn nhận được gì

- **Flow** — Sơ đồ động trực tiếp hiển thị tin nhắn luân chuyển qua các kênh, brain, công cụ, và quay lại
- **Overview** — Kiểm tra tình trạng hệ thống, bản đồ nhiệt hoạt động, số lượng phiên, thông tin mô hình
- **Usage** — Theo dõi token và chi phí với phân tích chi tiết theo ngày/tuần/tháng
- **Sessions** — Các phiên agent đang hoạt động kèm mô hình, token, hoạt động gần nhất
- **Crons** — Các tác vụ theo lịch trình kèm trạng thái, lần chạy tiếp theo, thời lượng
- **Logs** — Luồng nhật ký theo thời gian thực với mã màu
- **Memory** — Duyệt SOUL.md, MEMORY.md, AGENTS.md, ghi chú hàng ngày
- **Transcripts** — Giao diện dạng bong bóng chat để đọc lịch sử phiên
- **Alerts** — Giới hạn ngân sách, kích hoạt theo tỷ lệ lỗi, phát hiện agent ngoại tuyến; định tuyến đến Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Chặn các thao tác xóa mang tính phá hủy, force push, thay đổi cơ sở dữ liệu, sudo, cài đặt gói, cuộc gọi mạng đằng sau một cú nhấp phê duyệt

## Ảnh chụp màn hình

### 🧠 Brain — Luồng sự kiện agent trực tiếp
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tổng hợp sử dụng token & phiên
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Luồng gọi công cụ theo thời gian thực
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Phân tích chi phí theo mô hình & phiên
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Trình duyệt tệp không gian làm việc
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Tình trạng bảo mật & nhật ký kiểm tra
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Giới hạn ngân sách, kích hoạt theo tỷ lệ lỗi, webhook đến Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Chặn các lệnh gọi công cụ rủi ro đằng sau phê duyệt thủ công; quy tắc bảo vệ dựa trên chính sách
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Cài đặt

**Cài đặt một dòng lệnh (khuyến nghị):**
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

## Phát triển giao diện v2

Ứng dụng React v2 nằm trong `frontend/` và được phục vụ tại `/v2` khi
máy chủ Flask được khởi động với v2 được bật.

Sử dụng hai terminal khi phát triển:

```bash
# Terminal 1: Flask API/server trên cổng :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Máy chủ Vite dev trên cổng :5173
cd frontend
nvm use
npm ci
npm run dev
```

Mở `http://localhost:5173/v2/`. Vite sẽ proxy các yêu cầu `/api` đến
`http://localhost:8900`, để ứng dụng React có thể giao tiếp với máy chủ
Flask cục bộ mà không cần cấu hình CORS bổ sung.

Để build gói được đóng gói cùng với package Python:

```bash
cd frontend
npm run build
```

Bản build production sẽ được ghi vào `clawmetry/static/v2/dist/`.

## Khả năng tương thích Runtime / Agent

ClawMetry quan sát nhiều runtime AI-agent, không chỉ riêng OpenClaw. Mỗi runtime không phải OpenClaw đi kèm một adapter đọc chuyên dụng, chuyển đổi định dạng phiên gốc của nó sang cấu trúc thống nhất của ClawMetry; daemon nạp chúng vào cùng kho DuckDB + snapshot cloud, được gắn thẻ theo runtime, và tab Session replay hiển thị **bộ chuyển đổi runtime** khi có nhiều hơn một runtime hiện diện. Xem [`docs/compatibility.md`](docs/compatibility.md) để biết ma trận đầy đủ + hướng dẫn thêm runtime, và [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) để có bài giới thiệu về họ OpenClaw.

| Runtime / Agent | Trạng thái | Ghi chú |
|---|---|---|
| **OpenClaw** | Gốc | Runtime tham chiếu, tự động phát hiện |
| **PicoClaw** | Adapter beta | JSONL `providers.Message` phẳng (`~/.picoclaw/workspace/sessions`). Transcript, mô hình, lệnh gọi công cụ. |
| **NanoClaw** | Adapter beta | SQLite theo từng phiên (`data/v2-sessions`). Transcript + số lượng tin nhắn. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transcript, mô hình, token/chi phí. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcript, mô hình, lệnh gọi công cụ + suy luận, mức sử dụng token. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transcript, mô hình, lệnh gọi công cụ, mức sử dụng token. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transcript chat/composer, mô hình. |
| **Aider** | Adapter beta | `.aider.chat.history.md` cho mỗi dự án. Transcript, mô hình, số lượng token. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transcript, mô hình, lệnh gọi công cụ, tổng token. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transcript, mô hình, lệnh gọi công cụ, token + chi phí. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transcript, mô hình, lệnh gọi công cụ, mức sử dụng token. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transcript, mô hình, lệnh gọi công cụ, token + chi phí. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transcript, mô hình, lệnh gọi công cụ, token + chi phí. |

"Adapter beta" nghĩa là ClawMetry cung cấp một reader cho định dạng thực tế trên đĩa của runtime đó, mỗi cái được xây dựng + xác minh trên một bản cài đặt thật trên một máy thật (xem `tests/fixtures/runtimes/<rt>/`). Các adapter chỉ đọc; mỗi cái trung thực về những gì runtime của nó thực sự lưu trữ (ví dụ: PicoClaw/NanoClaw/Cursor không ghi chi phí token ra đĩa). Khi nhiều runtime chạy trên cùng một node, bộ chuyển đổi runtime sẽ thu hẹp phạm vi xem phiên về một runtime để dễ dàng đào sâu.

## Theo dõi bất kỳ SDK agent nào — thuộc tính chi phí ngoài vòng lặp

Các runtime ở trên đều ghi phiên ra đĩa. **Agent sản xuất** của riêng bạn, cái bạn xây dựng trên OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, hoặc một vòng lặp `httpx` thuần túy, thì không. Bộ chặn không cần cấu hình của ClawMetry vẫn ghi lại các lệnh gọi LLM của nó (chi phí, token, độ trễ, lỗi) bằng cách monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # kích hoạt bộ chặn
clawmetry.track.set_source("support-agent")   # đặt tên cho sản phẩm này

# ...agent của bạn chạy như bình thường; mọi lệnh gọi LLM giờ đã được theo dõi + gán thuộc tính.
```

`set_source()` (hoặc biến môi trường `CLAWMETRY_SOURCE=support-agent`) sẽ gắn thẻ mỗi lệnh gọi với một **nguồn được đặt tên**, để mỗi sản phẩm bạn chạy xuất hiện như một dòng riêng biệt, có thể gán thuộc tính chi phí hạng nhất trong thẻ **🔌 Out-loop sources** của dashboard trên Overview, số lệnh gọi, nhà cung cấp, độ trễ, tỷ lệ lỗi cho mỗi agent. Không đặt nguồn? Các lệnh gọi vẫn được theo dõi; thẻ đó chỉ đơn giản là bị ẩn.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Đây là cùng một lớp dữ liệu mà các adapter runtime nạp vào (DuckDB → snapshot cloud), vì vậy các nguồn ngoài vòng lặp đồng bộ hóa với dashboard cloud giống như mọi thứ khác, được mã hóa đầu cuối.

## OpenTelemetry — trung lập nhà cung cấp, gửi trace của bạn đến bất cứ đâu

ClawMetry giao tiếp bằng **OpenTelemetry** theo cả hai chiều, sử dụng **quy ước ngữ nghĩa GenAI**, để trace agent của bạn không bao giờ bị khóa vào một công cụ duy nhất.

**Xuất** mọi phiên, lệnh gọi LLM, công cụ, sub-agent, token, chi phí, dưới dạng span OTLP/HTTP GenAI đến bất kỳ collector nào (Datadog, Grafana, Honeycomb, hoặc OTel Collector của riêng bạn):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# tương đương:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Tiêu đề xác thực và khoảng thời gian polling là các biến môi trường tùy chọn:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # tiêu đề HTTP bổ sung
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # giây (mặc định 60)
```

**Nạp** — bộ thu OTLP tích hợp sẵn chấp nhận trace và metric từ bất kỳ nguồn nào khác tại `/v1/traces` và `/v1/metrics` (`pip install clawmetry[otel]` để nạp protobuf).

Bạn có được cả dashboard ClawMetry không cần cấu hình, ưu tiên cục bộ **và** dữ liệu của bạn trong bất kỳ backend nào đội của bạn đã sử dụng, không bị khóa, không cần cài thêm agent thứ hai.

## Cấu hình

Hầu hết mọi người không cần bất kỳ cấu hình nào. ClawMetry tự động phát hiện không gian làm việc, nhật ký, phiên, và cron của bạn.

Nếu bạn cần tùy chỉnh:

```bash
clawmetry --port 9000              # Cổng tùy chỉnh (mặc định: 8900)
clawmetry --host 127.0.0.1         # Chỉ liên kết với localhost
clawmetry --workspace ~/mybot      # Đường dẫn không gian làm việc tùy chỉnh
clawmetry --name "Alice"           # Tên của bạn trong hình ảnh trực quan Flow
```

Tất cả tùy chọn: `clawmetry --help`

## Các kênh được hỗ trợ

ClawMetry hiển thị hoạt động trực tiếp cho mọi kênh OpenClaw bạn đã cấu hình. Chỉ những kênh thực sự được thiết lập trong `openclaw.json` của bạn mới xuất hiện trong sơ đồ Flow, những kênh chưa được cấu hình sẽ tự động bị ẩn.

Nhấp vào bất kỳ nút kênh nào trong Flow để xem giao diện bong bóng chat trực tiếp với số lượng tin nhắn đến/đi.

| Kênh | Trạng thái | Popup trực tiếp | Ghi chú |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Đầy đủ | ✅ | Tin nhắn, thống kê, làm mới 10 giây |
| 💬 **iMessage** | ✅ Đầy đủ | ✅ | Đọc trực tiếp `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Đầy đủ | ✅ | Qua WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Đầy đủ | ✅ | Qua signal-cli |
| 🟣 **Discord** | ✅ Đầy đủ | ✅ | Phát hiện guild + kênh |
| 🟪 **Slack** | ✅ Đầy đủ | ✅ | Phát hiện workspace + kênh |
| 🌐 **Webchat** | ✅ Đầy đủ | ✅ | Phiên giao diện web tích hợp sẵn |
| 📡 **IRC** | ✅ Đầy đủ | ✅ | Giao diện bong bóng kiểu terminal |
| 🍏 **BlueBubbles** | ✅ Đầy đủ | ✅ | iMessage qua REST API của BlueBubbles |
| 🔵 **Google Chat** | ✅ Đầy đủ | ✅ | Qua webhook Chat API |
| 🟣 **MS Teams** | ✅ Đầy đủ | ✅ | Qua plugin bot Teams |
| 🔷 **Mattermost** | ✅ Đầy đủ | ✅ | Chat nhóm tự lưu trữ |
| 🟩 **Matrix** | ✅ Đầy đủ | ✅ | Phi tập trung, hỗ trợ E2EE |
| 🟢 **LINE** | ✅ Đầy đủ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Đầy đủ | ✅ | Tin nhắn riêng NIP-04 phi tập trung |
| 🟣 **Twitch** | ✅ Đầy đủ | ✅ | Chat qua kết nối IRC |
| 🔷 **Feishu/Lark** | ✅ Đầy đủ | ✅ | Đăng ký sự kiện WebSocket |
| 🔵 **Zalo** | ✅ Đầy đủ | ✅ | Zalo Bot API |

> **Tự động phát hiện:** ClawMetry đọc `~/.openclaw/openclaw.json` của bạn và chỉ hiển thị các kênh bạn thực sự đã cấu hình. Không cần thiết lập thủ công.

## Triển khai Docker

Muốn chạy ClawMetry trong container? Không thành vấn đề! 🐳

**Bắt đầu nhanh với Docker:**

```bash
# Build image
docker build -t clawmetry .

# Chạy với cài đặt mặc định
docker run -p 8900:8900 clawmetry

# Hoặc mount thư mục dữ liệu của agent (ví dụ: ~/.openclaw của OpenClaw)
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

> **Lưu ý:** Khi chạy trong Docker, hãy mount thư mục dữ liệu + nhật ký của agent (ví dụ: `~/.openclaw`, `~/.claude`, `~/.codex`) để ClawMetry có thể tự động phát hiện thiết lập của bạn.

## Yêu cầu hệ thống

- Python 3.8+
- Flask (được cài đặt tự động qua pip)
- Một runtime AI agent trên cùng máy: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, hoặc Deep Agents (hoặc các volume được mount cho Docker)
- Linux hoặc macOS

## Hỗ trợ NemoClaw / OpenShell

ClawMetry tự động phát hiện [NemoClaw](https://github.com/NVIDIA/NemoClaw), lớp bảo mật doanh nghiệp của NVIDIA cho OpenClaw, chạy agent bên trong các container OpenShell trong hộp cát (sandbox).

Trong hầu hết các trường hợp không cần cấu hình bổ sung. Sync daemon tự động khám phá các tệp phiên dù chúng nằm trong `~/.openclaw/` trên máy chủ hay bên trong một container OpenShell.

### Cách hoạt động

ClawMetry phát hiện NemoClaw theo hai cách:

1. **Phát hiện binary** — kiểm tra CLI `nemoclaw` và chạy `nemoclaw status` để lấy thông tin sandbox
2. **Phát hiện container** — quét các container Docker đang chạy để tìm image `openshell`, `nemoclaw`, hoặc `ghcr.io/nvidia/`, sau đó đọc phiên qua volume mount hoặc `docker cp`

Các tệp phiên được đồng bộ từ container NemoClaw được gắn thẻ với metadata `runtime=nemoclaw` và `container_id` trong dashboard cloud, để bạn có thể phân biệt chúng với các phiên OpenClaw tiêu chuẩn chỉ bằng một cái nhìn.

### Thiết lập được khuyến nghị: sync daemon trên HOST

Để có trải nghiệm tốt nhất, hãy chạy sync daemon của ClawMetry trên **máy chủ** (không phải bên trong sandbox). Điều này tránh được các hạn chế chính sách mạng của NemoClaw.

```bash
# Trên host (bên ngoài sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync daemon sẽ tự động tìm các phiên bên trong bất kỳ container OpenShell nào đang chạy.

### Tùy chọn: tên sandbox rõ ràng

Nếu tự động phát hiện không hoạt động, hãy trỏ ClawMetry đến đúng sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Chạy bên trong sandbox (nâng cao)

Nếu bạn phải chạy sync daemon **bên trong** sandbox OpenShell, hãy thêm quy tắc egress này vào chính sách mạng NemoClaw của bạn để nó có thể truy cập API nạp dữ liệu của ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Có (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Có (giao diện dashboard cục bộ) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Để khám phá phiên trong container |

Sync daemon chỉ thực hiện các lệnh gọi HTTPS đi ra đến `ingest.clawmetry.com`. Không cần cổng vào nào.

---

## Triển khai Cloud

Xem **[Hướng dẫn kiểm thử Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** để biết về SSH tunnel, reverse proxy, và Docker.

## Kiểm thử

Dự án này được kiểm thử với BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry gửi một tín hiệu ping ẩn danh "lần chạy đầu tiên" duy nhất đến
`https://app.clawmetry.com/api/install` trong lần đầu tiên bạn chạy CLI
`clawmetry` trên một máy mới. Chúng tôi dùng dữ liệu này để đếm số lượt
cài đặt (chỉ số marketing duy nhất mà chúng tôi có cho một dự án OSS) và
để biết người dùng của chúng tôi đã cài đặt những framework agent nào.

**Đúng một lần POST cho mỗi lần cài đặt**, chứa:

| Trường | Ví dụ | Lý do |
|---|---|---|
| `install_id` | UUID ngẫu nhiên được lưu tại `~/.clawmetry/install_id` | khử trùng lặp; không liên kết với email hoặc api_key của bạn |
| `version` | `0.12.167` | phiên bản nào đang được sử dụng ngoài thực tế |
| `os` / `os_version` | `Darwin` / `25.3.0` | ưu tiên hỗ trợ nền tảng |
| `python` | `3.11.15` | ma trận hỗ trợ phiên bản Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | chúng tôi nên tích hợp với agent nào tiếp theo |
| `is_ci` / `ci_provider` | `true` / `github_actions` | tách biệt cài đặt của con người với nhiễu từ CI |

**Những gì chúng tôi KHÔNG gửi**: IP (cloud lấy mã quốc gia phía server
từ request, sau đó loại bỏ IP), tên máy chủ, tên người dùng, đường dẫn
không gian làm việc, nội dung tệp, api_key của bạn, email của bạn,
bất cứ điều gì mang tính PII hoặc đặc thù không gian làm việc. Payload
truyền tải có thể được kiểm tra tại
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Từ chối tham gia** (bất kỳ một trong những cách sau sẽ vô hiệu hóa vĩnh viễn):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # theo từng shell
export DO_NOT_TRACK=1                          # tiêu chuẩn W3C liên công cụ
touch ~/.clawmetry/notelemetry                 # đánh dấu tệp cố định
```

Lỗi mạng ở đây không bao giờ chặn `clawmetry` chạy, tín hiệu ping này
là fire-and-forget trên một luồng daemon với thời gian chờ 3 giây.

## Lịch sử Star

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
