<!-- i18n-src:0e34918f8f2e -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Xem agent của bạn suy nghĩ.** Khả năng quan sát theo thời gian thực cho **14 runtime AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex và 10 runtime khác. Một dashboard duy nhất cho toàn bộ đội hình agent của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một câu lệnh. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900** và thế là xong.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Hoạt động với 14 runtime agent

ClawMetry khởi đầu là công cụ quan sát cho OpenClaw, và giờ đây đo lường **toàn bộ đội hình agent** của bạn trong một dashboard duy nhất, tự động phát hiện từng runtime trên máy của bạn:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw và NemoClaw miễn phí trong ứng dụng mã nguồn mở; các runtime khác được kích hoạt với ClawMetry Cloud hoặc giấy phép Pro tự lưu trữ. Chuyển đổi runtime từ thanh tiêu đề và mọi tab (chi phí, token, công cụ, trace) sẽ tự động điều chỉnh phạm vi theo runtime đó. Xem **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** để biết chi tiết chính xác về phân chia miễn phí/trả phí, ma trận các gói, cấu trúc `/api/entitlement`, và CLI `clawmetry license`.

## Bạn nhận được gì

- **Flow** — Sơ đồ động trực tiếp hiển thị luồng tin nhắn đi qua các kênh, brain, công cụ, và quay lại
- **Overview** — Kiểm tra tình trạng, bản đồ nhiệt hoạt động, số lượng phiên, thông tin mô hình
- **Usage** — Theo dõi token và chi phí với phân tích theo ngày/tuần/tháng
- **Sessions** — Các phiên agent đang hoạt động với mô hình, token, hoạt động gần nhất
- **Crons** — Các tác vụ đã lên lịch với trạng thái, lần chạy tiếp theo, thời lượng
- **Logs** — Luồng nhật ký thời gian thực có mã màu
- **Memory** — Duyệt SOUL.md, MEMORY.md, AGENTS.md, ghi chú hàng ngày
- **Transcripts** — Giao diện dạng bong bóng trò chuyện để đọc lịch sử phiên
- **Alerts** — Giới hạn ngân sách, kích hoạt tỷ lệ lỗi, phát hiện agent ngoại tuyến; định tuyến đến Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Chặn các thao tác xóa mang tính phá hủy, force push, thay đổi cơ sở dữ liệu, sudo, cài đặt gói, cuộc gọi mạng bằng một lần phê duyệt

## Ảnh chụp màn hình

### 🧠 Brain — Luồng sự kiện agent trực tiếp
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tổng quan sử dụng token & phiên
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Luồng cuộc gọi công cụ theo thời gian thực
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Phân tích chi phí theo mô hình & phiên
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Trình duyệt tệp không gian làm việc
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Tình trạng bảo mật & nhật ký kiểm tra
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Giới hạn ngân sách, kích hoạt tỷ lệ lỗi, webhook đến Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Chặn các cuộc gọi công cụ rủi ro bằng phê duyệt thủ công; quy tắc bảo vệ dựa trên chính sách
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Chặn trước khi thực thi cho Claude Code** — một câu lệnh cài đặt
hook PreToolUse tạm dừng các cuộc gọi công cụ khớp *trước khi* chúng chạy và chờ
quyết định của bạn (chỉ một chạm từ điện thoại khi bật
[thông báo đẩy trên cloud](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Từ chối chỉ chặn đúng một cuộc gọi công cụ đó, agent vẫn giữ phiên của nó và có thể
thử một cách tiếp cận khác. Phê duyệt trên điện thoại của bạn sẽ bỏ qua lời nhắc quyền
riêng của Claude Code (bạn đã trả lời rồi). Các công cụ không khớp tốn khoảng ~40ms và
chuyển tiếp vào luồng quyền thông thường của Claude Code. Bạn cũng nhận được thông báo đẩy trên điện thoại khi chính Claude Code
đang chờ bạn (thông báo `permission_prompt` /
`idle_prompt`).

## Cài đặt

**Một dòng lệnh (khuyến nghị):**
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

Mở `http://localhost:5173/v2/`. Vite chuyển tiếp các yêu cầu `/api` đến
`http://localhost:8900`, để ứng dụng React có thể giao tiếp với máy chủ Flask cục bộ
mà không cần thiết lập CORS bổ sung.

Để xây dựng bundle được đóng gói cùng gói Python:

```bash
cd frontend
npm run build
```

Bundle sản xuất được ghi vào `clawmetry/static/v2/dist/`.

## Khả năng tương thích Runtime / Agent

ClawMetry quan sát nhiều runtime AI agent, không chỉ riêng OpenClaw. Mỗi runtime không phải OpenClaw đi kèm một adapter đọc chuyên dụng chuyển đổi định dạng phiên gốc của nó thành các cấu trúc thống nhất của ClawMetry; daemon nạp chúng vào cùng kho lưu trữ DuckDB + snapshot cloud, được gắn nhãn theo runtime, và tab Session replay hiển thị **bộ chuyển đổi runtime** khi có nhiều hơn một runtime hiện diện. Xem [`docs/compatibility.md`](docs/compatibility.md) để biết ma trận đầy đủ + hướng dẫn thêm runtime, và [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) để biết bài giới thiệu về họ OpenClaw.

Đang chạy công cụ bảo mật agent [numbat của Perplexity](https://github.com/perplexityai/numbat)? ClawMetry nạp các phát hiện và quyết định thực thi của nó ngay khi cài đặt, xem [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Trạng thái | Ghi chú |
|---|---|---|
| **OpenClaw** | Gốc | Runtime tham chiếu, tự động phát hiện |
| **PicoClaw** | Adapter beta | JSONL `providers.Message` phẳng (`~/.picoclaw/workspace/sessions`). Bản ghi hội thoại, mô hình, cuộc gọi công cụ. |
| **NanoClaw** | Adapter beta | SQLite theo từng phiên (`data/v2-sessions`). Bản ghi hội thoại + số lượng tin nhắn. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Bản ghi hội thoại, mô hình, token/chi phí. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ + suy luận, mức sử dụng token. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ, mức sử dụng token. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Bản ghi hội thoại chat/composer, mô hình. |
| **Aider** | Adapter beta | `.aider.chat.history.md` theo từng dự án. Bản ghi hội thoại, mô hình, số lượng token. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ, tổng token. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ, token + chi phí. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ, mức sử dụng token. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ, token + chi phí. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Bản ghi hội thoại, mô hình, cuộc gọi công cụ, token + chi phí. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Lần chạy workflow, lần chạy node, lời nhắc AI Agent, mô hình + token khi n8n ghi lại. |
| **Antigravity** | Adapter beta | Brain JSONL trong `~/.gemini/<flavor>/brain/`. Hội thoại, các bước công cụ, suy luận, phân tách token Gemini theo từng lần sinh + chi phí, mức tiêu hao sinh nền. |
| **GitHub Copilot** | Adapter beta | Copilot CLI `events.jsonl` trong `~/.copilot/session-state/` + sổ cái sử dụng theo từng cuộc gọi `session-store.db`. Hội thoại, cuộc gọi công cụ, định tuyến mô hình, phân tách token nhận biết cache, chi phí AI-credit do nhà cung cấp tính phí. |

"Adapter beta" nghĩa là ClawMetry cung cấp bộ đọc cho định dạng thực tế trên đĩa của runtime đó, mỗi bộ được xây dựng + xác minh trên một bản cài đặt thực tế trên một máy thực tế (xem `tests/fixtures/runtimes/<rt>/`). Các adapter chỉ đọc; mỗi adapter trung thực về những gì runtime của nó thực sự lưu trữ (ví dụ: PicoClaw/NanoClaw/Cursor không ghi chi phí token ra đĩa). Khi nhiều runtime chạy trên một node, bộ chuyển đổi runtime giới hạn phạm vi khung xem phiên về một runtime để dễ tìm hiểu sâu.

## Theo dõi bất kỳ agent SDK nào — quy kết chi phí ngoài vòng lặp

Các runtime ở trên đều ghi phiên ra đĩa. **Agent sản xuất** của riêng bạn, cái mà bạn xây dựng trên OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, hoặc một vòng lặp `httpx` đơn giản, thì không. Bộ chặn không cần cấu hình của ClawMetry vẫn nắm bắt các cuộc gọi LLM của nó (chi phí, token, độ trễ, lỗi) bằng cách monkey-patching `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (hoặc biến môi trường `CLAWMETRY_SOURCE=support-agent`) gắn nhãn mỗi cuộc gọi bằng một **nguồn có tên**, để mỗi sản phẩm bạn chạy xuất hiện như một dòng riêng biệt, hạng nhất, có thể quy kết chi phí trong thẻ **🔌 Nguồn ngoài vòng lặp** trên Overview của dashboard, số cuộc gọi, nhà cung cấp, độ trễ, tỷ lệ lỗi theo từng agent. Không đặt nguồn? Các cuộc gọi vẫn được theo dõi, thẻ chỉ đơn giản là ẩn đi.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Đây là cùng lớp dữ liệu mà các adapter runtime cung cấp (DuckDB → snapshot cloud), vì vậy các nguồn ngoài vòng lặp cũng đồng bộ với dashboard cloud giống như mọi thứ khác, được mã hóa đầu cuối.

## OpenTelemetry — trung lập nhà cung cấp, gửi trace của bạn đến bất cứ đâu

ClawMetry giao tiếp bằng **OpenTelemetry** theo cả hai hướng, sử dụng **quy ước ngữ nghĩa GenAI**, vì vậy trace agent của bạn không bao giờ bị khóa vào một công cụ duy nhất.

**Xuất** mỗi phiên, cuộc gọi LLM, công cụ, sub-agent, token, chi phí, dưới dạng span GenAI OTLP/HTTP đến bất kỳ collector nào (Datadog, Grafana, Honeycomb, hoặc OTel Collector riêng của bạn):

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

**Nạp** — bộ nhận OTLP tích hợp sẵn chấp nhận trace và metric từ bất kỳ nguồn nào khác tại `/v1/traces` và `/v1/metrics` (`pip install clawmetry[otel]` để nạp protobuf).

Bạn có được dashboard ClawMetry không cần cấu hình, ưu tiên cục bộ **và** dữ liệu của bạn trong bất kỳ backend nào đội bạn đã dùng, không khóa nhà cung cấp, không cần cài thêm agent thứ hai.

## Cấu hình

Hầu hết mọi người không cần bất kỳ cấu hình nào. ClawMetry tự động phát hiện không gian làm việc, nhật ký, phiên, và cron của bạn.

Nếu bạn cần tùy chỉnh:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tất cả tùy chọn: `clawmetry --help`

## Các kênh được hỗ trợ

ClawMetry hiển thị hoạt động trực tiếp cho mọi kênh OpenClaw bạn đã cấu hình. Chỉ những kênh thực sự được thiết lập trong `openclaw.json` của bạn mới xuất hiện trong sơ đồ Flow, các kênh chưa cấu hình sẽ tự động bị ẩn.

Nhấp vào bất kỳ node kênh nào trong Flow để xem giao diện bong bóng trò chuyện trực tiếp với số lượng tin nhắn đến/đi.

| Kênh | Trạng thái | Popup trực tiếp | Ghi chú |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Đầy đủ | ✅ | Tin nhắn, thống kê, làm mới 10 giây |
| 💬 **iMessage** | ✅ Đầy đủ | ✅ | Đọc trực tiếp `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Đầy đủ | ✅ | Qua WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Đầy đủ | ✅ | Qua signal-cli |
| 🟣 **Discord** | ✅ Đầy đủ | ✅ | Phát hiện guild + kênh |
| 🟪 **Slack** | ✅ Đầy đủ | ✅ | Phát hiện workspace + kênh |
| 🌐 **Webchat** | ✅ Đầy đủ | ✅ | Các phiên giao diện web tích hợp sẵn |
| 📡 **IRC** | ✅ Đầy đủ | ✅ | Giao diện bong bóng dạng terminal |
| 🍏 **BlueBubbles** | ✅ Đầy đủ | ✅ | iMessage qua BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Đầy đủ | ✅ | Qua Chat API webhook |
| 🟣 **MS Teams** | ✅ Đầy đủ | ✅ | Qua plugin bot Teams |
| 🔷 **Mattermost** | ✅ Đầy đủ | ✅ | Team chat tự lưu trữ |
| 🟩 **Matrix** | ✅ Đầy đủ | ✅ | Phi tập trung, hỗ trợ E2EE |
| 🟢 **LINE** | ✅ Đầy đủ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Đầy đủ | ✅ | Tin nhắn riêng NIP-04 phi tập trung |
| 🟣 **Twitch** | ✅ Đầy đủ | ✅ | Trò chuyện qua kết nối IRC |
| 🔷 **Feishu/Lark** | ✅ Đầy đủ | ✅ | Đăng ký sự kiện WebSocket |
| 🔵 **Zalo** | ✅ Đầy đủ | ✅ | Zalo Bot API |

> **Tự động phát hiện:** ClawMetry đọc `~/.openclaw/openclaw.json` của bạn và chỉ hiển thị các kênh mà bạn đã thực sự cấu hình. Không cần thiết lập thủ công.

## Triển khai Docker

Muốn chạy ClawMetry trong container? Không vấn đề gì! 🐳

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

> **Lưu ý:** Khi chạy trong Docker, hãy gắn thư mục dữ liệu + nhật ký của agent bạn (ví dụ: `~/.openclaw`, `~/.claude`, `~/.codex`) để ClawMetry có thể tự động phát hiện cấu hình của bạn.

## Yêu cầu

- Python 3.8+
- Flask (được cài đặt tự động qua pip)
- Một runtime AI agent trên cùng máy: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, hoặc GitHub Copilot (hoặc các volume được gắn cho Docker)
- Linux hoặc macOS

## Hỗ trợ NemoClaw / OpenShell

ClawMetry tự động phát hiện [NemoClaw](https://github.com/NVIDIA/NemoClaw), lớp bảo mật doanh nghiệp của NVIDIA cho OpenClaw chạy agent bên trong các container OpenShell được cách ly.

Trong hầu hết các trường hợp không cần cấu hình bổ sung. Daemon đồng bộ tự động khám phá các tệp phiên dù chúng nằm trong `~/.openclaw/` trên host hay bên trong một container OpenShell.

### Cách hoạt động

ClawMetry phát hiện NemoClaw theo hai cách:

1. **Phát hiện qua binary** — kiểm tra CLI `nemoclaw` và chạy `nemoclaw status` để lấy thông tin sandbox
2. **Phát hiện qua container** — quét các container Docker đang chạy để tìm các image `openshell`, `nemoclaw`, hoặc `ghcr.io/nvidia/`, sau đó đọc phiên qua volume mount hoặc `docker cp`

Các tệp phiên đồng bộ từ container NemoClaw được gắn nhãn với `runtime=nemoclaw` và metadata `container_id` trong dashboard cloud, để bạn có thể phân biệt chúng với các phiên OpenClaw tiêu chuẩn ngay từ cái nhìn đầu tiên.

### Thiết lập được khuyến nghị: daemon đồng bộ trên HOST

Để có trải nghiệm tốt nhất, hãy chạy daemon đồng bộ của ClawMetry trên **máy host** (không phải bên trong sandbox). Điều này tránh các hạn chế chính sách mạng của NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon đồng bộ sẽ tự động tìm các phiên bên trong bất kỳ container OpenShell nào đang chạy.

### Tùy chọn: chỉ định rõ tên sandbox

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

### Cổng và endpoint

| Endpoint | Cổng | Giao thức | Bắt buộc |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Có (daemon đồng bộ → cloud) |
| `localhost:8900` | 8900 | HTTP | Có (giao diện dashboard cục bộ) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Để khám phá phiên container |

Daemon đồng bộ chỉ thực hiện các cuộc gọi HTTPS đi đến `ingest.clawmetry.com`. Không yêu cầu cổng vào nào.

---

## Triển khai Cloud

Xem **[Hướng dẫn kiểm thử Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** để biết về SSH tunnel, reverse proxy, và Docker.

## Kiểm thử

Dự án này được kiểm thử với BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Đo lường từ xa

ClawMetry gửi các ping vòng đời cài đặt ẩn danh đến
`https://app.clawmetry.com/api/install`: một ping `install` lần đầu tiên
bạn chạy CLI `clawmetry` trên một máy mới, một ping `update`
lần chạy đầu tiên sau khi nâng cấp lên phiên bản mới, và một ping `onboarded`
khi bạn hoàn tất lựa chọn onboarding trong dashboard. Chúng tôi dùng dữ liệu này
để đếm số lượt cài đặt thực tế (số liệu tải xuống thô từ PyPI có khoảng 98% là mirror, CI,
và các lượt tải lại tự động cập nhật) và để biết những framework agent và
phiên bản nào đang thực sự được sử dụng.

**Tối đa một POST cho mỗi sự kiện vòng đời trên mỗi phiên bản**, chứa:

| Trường | Ví dụ | Lý do |
|---|---|---|
| `install_id` | UUID ngẫu nhiên lưu tại `~/.clawmetry/install_id` | khử trùng lặp; ẩn danh cho đến khi bạn kết nối rõ ràng đồng bộ Cloud (nhịp tim daemon đã xác thực khi đó sẽ mang theo nó, liên kết bản cài đặt này với tài khoản của bạn) |
| `event` | `install` / `update` / `onboarded` | cài đặt mới so với nâng cấp bản đã có |
| `version` | `0.12.167` | phiên bản nào đang được sử dụng |
| `os` / `os_version` | `Darwin` / `25.3.0` | ưu tiên hỗ trợ nền tảng |
| `python` | `3.11.15` | ma trận hỗ trợ phiên bản Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | chúng tôi nên tích hợp với agent nào tiếp theo |
| `is_ci` / `ci_provider` | `true` / `github_actions` | tách biệt cài đặt của con người khỏi nhiễu CI |

**Những gì chúng tôi KHÔNG gửi**: IP (cloud lấy mã quốc gia phía server
từ request, sau đó loại bỏ IP), hostname, tên người dùng, đường dẫn không gian làm việc,
nội dung tệp, api_key của bạn, email của bạn, bất cứ điều gì PII hoặc
liên quan đến không gian làm việc. Payload truyền tải có thể được kiểm tra tại
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Từ chối tham gia** (bất kỳ cách nào trong số này đều vô hiệu hóa vĩnh viễn):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Lỗi mạng ở đây không bao giờ chặn `clawmetry` chạy, ping
này là fire-and-forget trên một luồng daemon với thời gian chờ 3 giây.

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
