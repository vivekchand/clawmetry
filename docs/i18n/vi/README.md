<!-- i18n-src:8252f6b1d31d -->
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

Mở tại **http://localhost:8900** và thế là xong.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Hoạt động với 14 runtime agent

ClawMetry khởi đầu như một công cụ quan sát cho OpenClaw, và giờ đây đo lường **toàn bộ đội agent** của bạn trong một dashboard duy nhất, tự động phát hiện từng runtime trên máy của bạn:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw và NemoClaw miễn phí trong ứng dụng mã nguồn mở; các runtime khác được kích hoạt với ClawMetry Cloud hoặc giấy phép Pro tự lưu trữ. Chuyển đổi runtime từ thanh header và mọi tab (chi phí, token, công cụ, dấu vết) sẽ tự động thu hẹp phạm vi theo runtime đó. Xem **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** để biết chi tiết chính xác về phân chia miễn phí/trả phí, ma trận các gói, cấu trúc `/api/entitlement`, và CLI `clawmetry license`.

## Bạn nhận được gì

- **Flow** — Sơ đồ hoạt hình trực tiếp cho thấy tin nhắn di chuyển qua các kênh, brain, công cụ, và quay lại
- **Overview** — Kiểm tra sức khỏe, bản đồ nhiệt hoạt động, số lượng phiên, thông tin mô hình
- **Usage** — Theo dõi token và chi phí với phân tích chi tiết theo ngày/tuần/tháng
- **Sessions** — Các phiên agent đang hoạt động cùng mô hình, token, hoạt động gần nhất
- **Crons** — Các tác vụ theo lịch với trạng thái, lần chạy tiếp theo, thời lượng
- **Logs** — Truyền log thời gian thực có mã màu
- **Memory** — Duyệt qua SOUL.md, MEMORY.md, AGENTS.md, ghi chú hàng ngày
- **Transcripts** — Giao diện dạng bong bóng chat để đọc lịch sử phiên
- **Alerts** — Giới hạn ngân sách, kích hoạt tỷ lệ lỗi, phát hiện agent ngoại tuyến; định tuyến đến Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Chặn các thao tác xóa mang tính phá hủy, force push, thay đổi cơ sở dữ liệu, sudo, cài đặt gói, các cuộc gọi mạng đằng sau một lần phê duyệt duy nhất

## Ảnh chụp màn hình

### 🧠 Brain — Luồng sự kiện agent trực tiếp
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tổng hợp mức sử dụng token & phiên làm việc
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Nguồn cấp dữ liệu lời gọi công cụ theo thời gian thực
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Phân tích chi phí theo mô hình & phiên
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Trình duyệt tệp không gian làm việc
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Tình trạng bảo mật & nhật ký kiểm tra
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Giới hạn ngân sách, kích hoạt tỷ lệ lỗi, webhook đến Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Chặn các lời gọi công cụ rủi ro đằng sau phê duyệt thủ công; quy tắc bảo vệ dựa trên chính sách
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Chặn trước khi thực thi cho Claude Code** — một lệnh duy nhất sẽ cài đặt
một hook PreToolUse tạm dừng các lời gọi công cụ khớp *trước khi* chúng chạy và chờ
quyết định của bạn (chỉ một chạm từ điện thoại khi bật
[thông báo đẩy trên cloud](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Một lần từ chối chỉ chặn lời gọi công cụ đó, agent vẫn giữ phiên làm việc và có thể
thử một cách tiếp cận khác. Phê duyệt trên điện thoại sẽ bỏ qua lời nhắc quyền
riêng của Claude Code (bạn đã trả lời rồi). Các công cụ không khớp tốn khoảng ~40ms và
rơi xuống luồng quyền thông thường của Claude Code. Bạn cũng nhận được thông báo đẩy trên
điện thoại khi chính Claude Code đang chờ bạn (thông báo `permission_prompt` /
`idle_prompt`).

## Cài đặt

**Lệnh đơn (khuyến nghị):**
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

## Phát triển v2 Frontend

Ứng dụng React v2 nằm trong `frontend/` và được phục vụ tại `/v2` khi
máy chủ Flask được khởi động với v2 được bật.

Sử dụng hai terminal khi phát triển:

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

Mở `http://localhost:5173/v2/`. Vite proxy các yêu cầu `/api` đến
`http://localhost:8900`, để ứng dụng React có thể giao tiếp với máy chủ Flask cục bộ
mà không cần cấu hình CORS bổ sung.

Để xây dựng bundle đi kèm với gói Python:

```bash
cd frontend
npm run build
```

Bundle sản xuất được ghi vào `clawmetry/static/v2/dist/`.

## Khả năng tương thích Runtime / Agent

ClawMetry quan sát nhiều runtime AI agent, không chỉ riêng OpenClaw. Mỗi runtime không phải OpenClaw đi kèm một bộ điều hợp đọc chuyên dụng chuyển đổi định dạng phiên gốc của nó thành các hình dạng thống nhất của ClawMetry; daemon nạp chúng vào cùng kho DuckDB + ảnh chụp nhanh cloud, được gắn thẻ theo runtime, và tab phát lại phiên hiển thị một **bộ chuyển đổi runtime** khi có nhiều hơn một runtime hiện diện. Xem [`docs/compatibility.md`](docs/compatibility.md) để biết ma trận đầy đủ + hướng dẫn thêm runtime, và [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) cho tài liệu giới thiệu về họ OpenClaw.

| Runtime / Agent | Trạng thái | Ghi chú |
|---|---|---|
| **OpenClaw** | Gốc | Runtime tham chiếu, tự động phát hiện |
| **PicoClaw** | Bộ điều hợp Beta | JSONL `providers.Message` phẳng (`~/.picoclaw/workspace/sessions`). Bản ghi transcript, mô hình, lời gọi công cụ. |
| **NanoClaw** | Bộ điều hợp Beta | SQLite theo từng phiên (`data/v2-sessions`). Bản ghi transcript + số lượng tin nhắn. |
| **Hermes** | Bộ điều hợp Beta | SQLite `~/.hermes/state.db`. Bản ghi transcript, mô hình, token/chi phí. |
| **Claude Code** | Bộ điều hợp Beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Bản ghi transcript, mô hình, lời gọi công cụ + suy nghĩ, mức sử dụng token. |
| **Codex** | Bộ điều hợp Beta | Rollout JSONL `~/.codex/sessions/...`. Bản ghi transcript, mô hình, lời gọi công cụ, mức sử dụng token. |
| **Cursor** | Bộ điều hợp Beta | SQLite `state.vscdb`. Bản ghi transcript chat/composer, mô hình. |
| **Aider** | Bộ điều hợp Beta | `.aider.chat.history.md` theo từng dự án. Bản ghi transcript, mô hình, số lượng token. |
| **Goose** | Bộ điều hợp Beta | SQLite `~/.local/share/goose`. Bản ghi transcript, mô hình, lời gọi công cụ, tổng số token. |
| **opencode** | Bộ điều hợp Beta | SQLite `~/.local/share/opencode`. Bản ghi transcript, mô hình, lời gọi công cụ, token + chi phí. |
| **Qwen Code** | Bộ điều hợp Beta | JSONL `~/.qwen/projects/.../chats`. Bản ghi transcript, mô hình, lời gọi công cụ, mức sử dụng token. |
| **Pi** | Bộ điều hợp Beta | JSONL `~/.pi/agent/sessions`. Bản ghi transcript, mô hình, lời gọi công cụ, token + chi phí. |
| **Deep Agents** | Bộ điều hợp Beta | SQLite `~/.deepagents/.state/sessions.db`. Bản ghi transcript, mô hình, lời gọi công cụ, token + chi phí. |
| **n8n** | Bộ điều hợp Beta | SQLite `~/.n8n/database.sqlite`. Các lần thực thi workflow, lần chạy node, prompt AI Agent, mô hình + token nơi n8n ghi lại. |

"Bộ điều hợp Beta" nghĩa là ClawMetry cung cấp một trình đọc cho định dạng thực tế trên đĩa của runtime đó, mỗi cái được xây dựng + xác minh trên một bản cài đặt thực trên một máy thực (xem `tests/fixtures/runtimes/<rt>/`). Các bộ điều hợp chỉ đọc; mỗi bộ trung thực về những gì runtime của nó thực sự lưu trữ (ví dụ: PicoClaw/NanoClaw/Cursor không ghi chi phí token ra đĩa). Khi nhiều runtime chạy trên một node, bộ chuyển đổi runtime sẽ thu hẹp phạm vi xem phiên về một runtime để dễ dàng đào sâu.

## Theo dõi bất kỳ agent SDK nào — quy kết chi phí ngoài vòng lặp

Các runtime ở trên đều ghi phiên xuống đĩa. **Agent sản xuất** của riêng bạn, cái bạn xây dựng trên OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, hoặc một vòng lặp `httpx` thuần túy, thì không. Bộ chặn không cần cấu hình của ClawMetry vẫn nắm bắt các lời gọi LLM của nó (chi phí, token, độ trễ, lỗi) bằng cách monkey-patch `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (hoặc biến môi trường `CLAWMETRY_SOURCE=support-agent`) gắn thẻ mỗi lời gọi bằng một **nguồn được đặt tên**, để mỗi sản phẩm bạn chạy xuất hiện như một dòng riêng biệt, có thể quy kết chi phí trong thẻ **🔌 Nguồn ngoài vòng lặp** của dashboard trên tab Overview, số lượng lời gọi, nhà cung cấp, độ trễ, tỷ lệ lỗi theo từng agent. Không đặt nguồn? Các lời gọi vẫn được theo dõi; thẻ này chỉ đơn giản ẩn đi.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Đây là lớp dữ liệu giống với lớp mà các bộ điều hợp runtime cung cấp (DuckDB → ảnh chụp nhanh cloud), vì vậy các nguồn ngoài vòng lặp cũng đồng bộ lên dashboard cloud giống như mọi thứ khác, được mã hóa đầu cuối (E2E).

## OpenTelemetry — trung lập với nhà cung cấp, gửi dấu vết của bạn đến bất cứ đâu

ClawMetry nói **OpenTelemetry** theo cả hai chiều, sử dụng **quy ước ngữ nghĩa GenAI**, vì vậy dấu vết agent của bạn không bao giờ bị khóa vào một công cụ duy nhất.

**Xuất** mọi phiên, bao gồm lời gọi LLM, công cụ, sub-agent, token, chi phí, dưới dạng dấu vết GenAI OTLP/HTTP đến bất kỳ collector nào (Datadog, Grafana, Honeycomb, hoặc OTel Collector của riêng bạn):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Tiêu đề xác thực và khoảng thời gian polling là các biến môi trường tùy chọn:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Nạp dữ liệu** — bộ tiếp nhận OTLP tích hợp sẵn chấp nhận dấu vết và metric từ bất kỳ nguồn nào khác tại `/v1/traces` và `/v1/metrics` (`pip install clawmetry[otel]` để nạp protobuf).

Bạn có được dashboard ClawMetry không cần cấu hình, ưu tiên cục bộ **và** dữ liệu của bạn trong bất kỳ backend nào mà đội của bạn đang chạy, không bị khóa, không cần cài đặt agent thứ hai.

## Cấu hình

Hầu hết mọi người không cần bất kỳ cấu hình nào. ClawMetry tự động phát hiện không gian làm việc, log, phiên, và cron của bạn.

Nếu bạn cần tùy chỉnh:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tất cả các tùy chọn: `clawmetry --help`

## Các kênh được hỗ trợ

ClawMetry hiển thị hoạt động trực tiếp cho mọi kênh OpenClaw bạn đã cấu hình. Chỉ những kênh thực sự được thiết lập trong `openclaw.json` của bạn mới xuất hiện trong sơ đồ Flow, những kênh chưa cấu hình sẽ tự động bị ẩn.

Nhấp vào bất kỳ nút kênh nào trong Flow để xem giao diện bong bóng chat trực tiếp với số lượng tin nhắn đến/đi.

| Kênh | Trạng thái | Cửa sổ trực tiếp | Ghi chú |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Đầy đủ | ✅ | Tin nhắn, thống kê, làm mới 10 giây |
| 💬 **iMessage** | ✅ Đầy đủ | ✅ | Đọc trực tiếp từ `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Đầy đủ | ✅ | Qua WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Đầy đủ | ✅ | Qua signal-cli |
| 🟣 **Discord** | ✅ Đầy đủ | ✅ | Phát hiện guild + kênh |
| 🟪 **Slack** | ✅ Đầy đủ | ✅ | Phát hiện workspace + kênh |
| 🌐 **Webchat** | ✅ Đầy đủ | ✅ | Các phiên giao diện web tích hợp sẵn |
| 📡 **IRC** | ✅ Đầy đủ | ✅ | Giao diện bong bóng dạng terminal |
| 🍏 **BlueBubbles** | ✅ Đầy đủ | ✅ | iMessage qua REST API của BlueBubbles |
| 🔵 **Google Chat** | ✅ Đầy đủ | ✅ | Qua webhook của Chat API |
| 🟣 **MS Teams** | ✅ Đầy đủ | ✅ | Qua plugin bot Teams |
| 🔷 **Mattermost** | ✅ Đầy đủ | ✅ | Ứng dụng chat nhóm tự lưu trữ |
| 🟩 **Matrix** | ✅ Đầy đủ | ✅ | Phi tập trung, hỗ trợ E2EE |
| 🟢 **LINE** | ✅ Đầy đủ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Đầy đủ | ✅ | Tin nhắn riêng phi tập trung NIP-04 |
| 🟣 **Twitch** | ✅ Đầy đủ | ✅ | Chat qua kết nối IRC |
| 🔷 **Feishu/Lark** | ✅ Đầy đủ | ✅ | Đăng ký sự kiện WebSocket |
| 🔵 **Zalo** | ✅ Đầy đủ | ✅ | Zalo Bot API |

> **Tự động phát hiện:** ClawMetry đọc `~/.openclaw/openclaw.json` của bạn và chỉ hiển thị các kênh bạn thực sự đã cấu hình. Không cần thiết lập thủ công.

## Triển khai Docker

Muốn chạy ClawMetry trong một container? Không vấn đề gì! 🐳

**Bắt đầu nhanh với Docker:**

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

> **Lưu ý:** Khi chạy trong Docker, hãy mount thư mục dữ liệu + log của agent (ví dụ: `~/.openclaw`, `~/.claude`, `~/.codex`) để ClawMetry có thể tự động phát hiện thiết lập của bạn.

## Yêu cầu

- Python 3.8+
- Flask (được cài đặt tự động qua pip)
- Một runtime AI agent trên cùng máy: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, hoặc n8n (hoặc các volume được mount cho Docker)
- Linux hoặc macOS

## Hỗ trợ NemoClaw / OpenShell

ClawMetry tự động phát hiện [NemoClaw](https://github.com/NVIDIA/NemoClaw), lớp bảo mật doanh nghiệp của NVIDIA dành cho OpenClaw chạy các agent bên trong các container OpenShell được cách ly (sandbox).

Trong hầu hết các trường hợp không cần cấu hình bổ sung. Daemon đồng bộ tự động khám phá các tệp phiên dù chúng nằm trong `~/.openclaw/` trên máy chủ hoặc bên trong một container OpenShell.

### Cách hoạt động

ClawMetry phát hiện NemoClaw theo hai cách:

1. **Phát hiện qua binary** — kiểm tra CLI `nemoclaw` và chạy `nemoclaw status` để lấy thông tin sandbox
2. **Phát hiện qua container** — quét các container Docker đang chạy tìm `openshell`, `nemoclaw`, hoặc các image `ghcr.io/nvidia/`, sau đó đọc các phiên qua volume mount hoặc `docker cp`

Các tệp phiên được đồng bộ từ các container NemoClaw được gắn thẻ với metadata `runtime=nemoclaw` và `container_id` trong dashboard cloud, để bạn có thể phân biệt chúng với các phiên OpenClaw tiêu chuẩn chỉ bằng một cái nhìn thoáng qua.

### Thiết lập khuyến nghị: daemon đồng bộ trên HOST

Để có trải nghiệm tốt nhất, hãy chạy daemon đồng bộ của ClawMetry trên **máy chủ (host)** (không phải bên trong sandbox). Điều này tránh các hạn chế chính sách mạng của NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon đồng bộ sẽ tự động tìm các phiên bên trong bất kỳ container OpenShell nào đang chạy.

### Tùy chọn: tên sandbox rõ ràng

Nếu tự động phát hiện không hoạt động, hãy trỏ ClawMetry đến đúng sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Chạy bên trong sandbox (nâng cao)

Nếu bạn phải chạy daemon đồng bộ **bên trong** sandbox OpenShell, hãy thêm quy tắc egress này vào chính sách mạng NemoClaw của bạn để nó có thể truy cập API nạp dữ liệu của ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Có (daemon đồng bộ → cloud) |
| `localhost:8900` | 8900 | HTTP | Có (giao diện dashboard cục bộ) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Để khám phá phiên trong container |

Daemon đồng bộ chỉ thực hiện các lệnh gọi HTTPS đi đến `ingest.clawmetry.com`. Không cần cổng vào (inbound) nào.

---

## Triển khai Cloud

Xem **[Hướng dẫn kiểm thử Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** để biết về SSH tunnel, reverse proxy, và Docker.

## Kiểm thử

Dự án này được kiểm thử với BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry gửi các tín hiệu ping ẩn danh về vòng đời cài đặt đến
`https://app.clawmetry.com/api/install`: một tín hiệu ping `install` lần đầu tiên
bạn chạy CLI `clawmetry` trên một máy mới, một tín hiệu ping `update`
ở lần chạy đầu tiên sau khi nâng cấp lên phiên bản mới, và một tín hiệu ping
`onboarded` khi bạn hoàn tất lựa chọn giới thiệu trong dashboard. Chúng tôi sử dụng dữ liệu này để
đếm số lượt cài đặt thực (số liệu tải xuống thô từ PyPI có khoảng 98% là mirror, CI,
và các lần tải lại tự động cập nhật) và để tìm hiểu các framework agent và
phiên bản nào thực sự đang được sử dụng.

**Tối đa một lần POST cho mỗi sự kiện vòng đời trên mỗi phiên bản**, chứa:

| Trường | Ví dụ | Lý do |
|---|---|---|
| `install_id` | UUID ngẫu nhiên được lưu tại `~/.clawmetry/install_id` | khử trùng lặp; ẩn danh cho đến khi bạn kết nối rõ ràng đồng bộ Cloud (nhịp tim đã xác thực của daemon sau đó mang theo nó, liên kết cài đặt này với tài khoản của bạn) |
| `event` | `install` / `update` / `onboarded` | cài đặt mới hay nâng cấp một cài đặt hiện có |
| `version` | `0.12.167` | các phiên bản nào đang được sử dụng |
| `os` / `os_version` | `Darwin` / `25.3.0` | ưu tiên hỗ trợ nền tảng |
| `python` | `3.11.15` | ma trận hỗ trợ phiên bản Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | chúng tôi nên tích hợp với agent nào tiếp theo |
| `is_ci` / `ci_provider` | `true` / `github_actions` | tách biệt cài đặt của con người khỏi nhiễu CI |

**Những gì chúng tôi KHÔNG gửi**: IP (cloud lấy mã quốc gia phía máy chủ
từ yêu cầu, sau đó loại bỏ IP), tên máy chủ, tên người dùng, đường dẫn không gian làm việc,
nội dung tệp, api_key của bạn, email của bạn, bất cứ thứ gì mang tính cá nhân hoặc
đặc thù cho không gian làm việc. Tải trọng truyền tải có thể được kiểm toán tại
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Từ chối tham gia** (bất kỳ cách nào trong số này sẽ vô hiệu hóa vĩnh viễn):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Lỗi mạng ở đây không bao giờ chặn `clawmetry` chạy, tín hiệu ping này là
gửi-và-quên trên một luồng daemon với thời gian chờ 3 giây.

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
