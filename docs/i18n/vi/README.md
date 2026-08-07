<!-- i18n-src:7cfb63716507 -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Xem agent của bạn suy nghĩ.** Khả năng quan sát theo thời gian thực cho **14 runtime AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex và 10 runtime khác. Một dashboard duy nhất cho toàn bộ đội agent của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một lệnh duy nhất. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900** và thế là xong.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Hoạt động với 14 runtime agent

ClawMetry khởi đầu là công cụ quan sát cho OpenClaw, và giờ đây đo lường **toàn bộ đội agent** của bạn trong một dashboard, tự động phát hiện từng runtime trên máy bạn:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw và NemoClaw miễn phí trong ứng dụng mã nguồn mở; các runtime còn lại được kích hoạt với ClawMetry Cloud hoặc giấy phép Pro tự lưu trữ. Chuyển đổi runtime từ phần đầu trang, và mọi tab, chi phí, token, công cụ, dấu vết, sẽ tự động chuyển phạm vi theo runtime đó. Xem **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** để biết chi tiết chính xác về phân chia miễn phí/trả phí, ma trận cấp bậc, cấu trúc `/api/entitlement`, và CLI `clawmetry license`.

## Bạn nhận được gì

- **Flow** — Sơ đồ động trực tiếp hiển thị luồng tin nhắn đi qua các kênh, brain, công cụ và quay lại
- **Overview** — Kiểm tra tình trạng, bản đồ nhiệt hoạt động, số lượng phiên, thông tin mô hình
- **Usage** — Theo dõi token và chi phí với phân tích theo ngày/tuần/tháng
- **Sessions** — Các phiên agent đang hoạt động cùng mô hình, token, hoạt động gần nhất
- **Crons** — Các tác vụ theo lịch với trạng thái, lần chạy tiếp theo, thời lượng
- **Logs** — Luồng log trực tiếp có mã màu
- **Memory** — Duyệt SOUL.md, MEMORY.md, AGENTS.md, ghi chú hàng ngày
- **Transcripts** — Giao diện dạng bong bóng chat để đọc lịch sử phiên
- **Alerts** — Giới hạn ngân sách, kích hoạt theo tỷ lệ lỗi, phát hiện agent ngoại tuyến; định tuyến đến Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Chặn các thao tác xóa mang tính phá hủy, force push, thay đổi cơ sở dữ liệu, sudo, cài đặt gói, cuộc gọi mạng đằng sau một lần phê duyệt duy nhất

## Ảnh chụp màn hình

### 🧠 Brain — Luồng sự kiện agent trực tiếp
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tóm tắt sử dụng token & phiên
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Nguồn cấp cuộc gọi công cụ theo thời gian thực
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Phân tích chi phí theo mô hình & phiên
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Trình duyệt tệp không gian làm việc
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Tình trạng bảo mật & nhật ký kiểm toán
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Giới hạn ngân sách, kích hoạt theo tỷ lệ lỗi, webhook đến Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Chặn các cuộc gọi công cụ rủi ro đằng sau phê duyệt thủ công; quy tắc bảo vệ dựa trên chính sách
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Chặn trước khi thực thi cho Claude Code** — một lệnh duy nhất cài đặt
hook PreToolUse để tạm dừng các cuộc gọi công cụ khớp *trước khi* chúng chạy và chờ
quyết định của bạn (chỉ cần một lần chạm từ điện thoại khi bật
[thông báo đẩy trên cloud](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Một lần từ chối chỉ chặn cuộc gọi công cụ đó, agent vẫn giữ nguyên phiên và có thể
thử cách tiếp cận khác. Việc phê duyệt trên điện thoại của bạn sẽ bỏ qua lời nhắc
quyền của chính Claude Code (vì bạn đã trả lời rồi). Các công cụ không khớp chỉ tốn
khoảng 40ms và sẽ chuyển sang luồng quyền bình thường của Claude Code. Bạn cũng nhận
được thông báo đẩy trên điện thoại khi chính Claude Code đang chờ bạn (thông báo
`permission_prompt` / `idle_prompt`).

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

## Phát triển giao diện v2

Ứng dụng React v2 nằm trong `frontend/` và được phục vụ tại `/v2` khi máy chủ
Flask được khởi động với v2 được bật.

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
`http://localhost:8900`, để ứng dụng React có thể giao tiếp với máy chủ Flask
cục bộ mà không cần cấu hình CORS thêm.

Để xây dựng gói được đóng gói cùng gói Python:

```bash
cd frontend
npm run build
```

Gói sản phẩm cuối cùng được ghi vào `clawmetry/static/v2/dist/`.

## Khả năng tương thích Runtime / Agent

ClawMetry quan sát nhiều runtime AI agent, không chỉ OpenClaw. Mỗi runtime không phải OpenClaw đi kèm một adapter đọc chuyên biệt, chuyển đổi định dạng phiên gốc của nó thành các cấu trúc thống nhất của ClawMetry; daemon nạp chúng vào cùng kho DuckDB + snapshot cloud, được gắn thẻ theo runtime, và tab phát lại phiên (Session replay) hiển thị **bộ chuyển runtime** khi có nhiều hơn một runtime hiện diện. Xem [`docs/compatibility.md`](docs/compatibility.md) để biết ma trận đầy đủ + hướng dẫn thêm runtime, và [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) để có bài giới thiệu về họ OpenClaw.

Đang chạy công cụ bảo mật agent [numbat của Perplexity](https://github.com/perplexityai/numbat)? ClawMetry nạp các phát hiện và quyết định thực thi của nó ngay từ đầu, xem [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Trạng thái | Ghi chú |
|---|---|---|
| **OpenClaw** | Gốc | Runtime tham chiếu, tự động phát hiện |
| **PicoClaw** | Adapter Beta | JSONL phẳng `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcript, mô hình, cuộc gọi công cụ. |
| **NanoClaw** | Adapter Beta | SQLite theo từng phiên (`data/v2-sessions`). Transcript + số lượng tin nhắn. |
| **Hermes** | Adapter Beta | SQLite `~/.hermes/state.db`. Transcript, mô hình, token/chi phí. |
| **Claude Code** | Adapter Beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcript, mô hình, cuộc gọi công cụ + suy luận (thinking), sử dụng token. |
| **Codex** | Adapter Beta | Rollout JSONL `~/.codex/sessions/...`. Transcript, mô hình, cuộc gọi công cụ, sử dụng token. |
| **Cursor** | Adapter Beta | SQLite `state.vscdb`. Transcript chat/composer, mô hình. |
| **Aider** | Adapter Beta | `.aider.chat.history.md` cho mỗi dự án. Transcript, mô hình, số lượng token. |
| **Goose** | Adapter Beta | SQLite `~/.local/share/goose`. Transcript, mô hình, cuộc gọi công cụ, tổng token. |
| **opencode** | Adapter Beta | SQLite `~/.local/share/opencode`. Transcript, mô hình, cuộc gọi công cụ, token + chi phí. |
| **Qwen Code** | Adapter Beta | JSONL `~/.qwen/projects/.../chats`. Transcript, mô hình, cuộc gọi công cụ, sử dụng token. |
| **Pi** | Adapter Beta | JSONL `~/.pi/agent/sessions`. Transcript, mô hình, cuộc gọi công cụ, token + chi phí. |
| **Deep Agents** | Adapter Beta | SQLite `~/.deepagents/.state/sessions.db`. Transcript, mô hình, cuộc gọi công cụ, token + chi phí. |
| **n8n** | Adapter Beta | SQLite `~/.n8n/database.sqlite`. Lần thực thi workflow, lần chạy node, prompt AI Agent, mô hình + token nếu n8n ghi lại. |
| **Antigravity** | Adapter Beta | Brain JSONL tại `~/.gemini/<flavor>/brain/`. Cuộc hội thoại, các bước công cụ, suy luận (thinking), phân tách token Gemini theo từng lần sinh + chi phí, mức tiêu hao sinh nền. |
| **GitHub Copilot** | Adapter Beta | `events.jsonl` của Copilot CLI tại `~/.copilot/session-state/` + sổ cái sử dụng theo từng cuộc gọi `session-store.db`. Cuộc hội thoại, cuộc gọi công cụ, định tuyến mô hình, phân tách token nhận biết cache, chi phí AI-credit do nhà cung cấp tính phí. |
| **Grok** | Adapter Beta | xAI Grok Build CLI (binary Rust tại `~/.grok/bin/grok`): nhật ký sự kiện toàn cục `~/.grok/logs/unified.jsonl` + theo từng phiên `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Cuộc hội thoại, phân tách token theo từng lượt, định tuyến mô hình, và tải trọng repo gửi đi của CLI được lưu tạm tại `~/.grok/upload_queue/` để bạn thấy dữ liệu gì đã rời khỏi máy của mình. |

"Adapter Beta" nghĩa là ClawMetry cung cấp một reader cho định dạng thực tế trên đĩa của runtime đó, mỗi cái được xây dựng + xác minh trên một bản cài đặt thực trên một máy thực (xem `tests/fixtures/runtimes/<rt>/`). Các adapter chỉ đọc; mỗi adapter trung thực về những gì runtime của nó thực sự lưu trữ (ví dụ: PicoClaw/NanoClaw/Cursor không ghi chi phí token ra đĩa). Khi nhiều runtime chạy trên một node, bộ chuyển runtime sẽ giới hạn phạm vi xem phiên về một runtime để dễ dàng đào sâu.

## Theo dõi bất kỳ agent SDK nào — quy kết chi phí ngoài vòng lặp

Các runtime ở trên đều ghi phiên ra đĩa. **Agent sản xuất** của riêng bạn, cái bạn xây dựng trên OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, hoặc một vòng lặp `httpx` đơn giản, thì không. Trình chặn không cần cấu hình của ClawMetry vẫn ghi lại các cuộc gọi LLM của nó (chi phí, token, độ trễ, lỗi) bằng cách vá động (monkey-patching) `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (hoặc biến môi trường `CLAWMETRY_SOURCE=support-agent`) gắn thẻ mỗi cuộc gọi với một **nguồn được đặt tên**, để mỗi sản phẩm bạn chạy xuất hiện như một dòng riêng biệt, có thể quy kết chi phí trong thẻ **🔌 Nguồn ngoài vòng lặp** của dashboard trên tab Overview, số cuộc gọi, nhà cung cấp, độ trễ, tỷ lệ lỗi cho từng agent. Không đặt nguồn? Các cuộc gọi vẫn được theo dõi; thẻ chỉ đơn giản là ẩn đi.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Đây là cùng một lớp dữ liệu mà các adapter runtime cung cấp (DuckDB → snapshot cloud), vì vậy các nguồn ngoài vòng lặp cũng đồng bộ với dashboard cloud giống như mọi thứ khác, được mã hóa đầu cuối.

## OpenTelemetry — trung lập nhà cung cấp, gửi dấu vết của bạn đến bất kỳ đâu

ClawMetry nói được **OpenTelemetry** theo cả hai chiều, sử dụng **quy ước ngữ nghĩa GenAI**, vì vậy dấu vết agent của bạn không bao giờ bị khóa vào một công cụ duy nhất.

**Xuất** mỗi phiên, cuộc gọi LLM, công cụ, sub-agent, token, chi phí, dưới dạng dấu vết GenAI OTLP/HTTP đến bất kỳ bộ thu thập nào (Datadog, Grafana, Honeycomb, hoặc OTel Collector của riêng bạn):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Tiêu đề xác thực và khoảng thời gian thăm dò là các biến môi trường tùy chọn:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Nạp** — bộ thu OTLP tích hợp sẵn chấp nhận dấu vết và số liệu từ bất kỳ nguồn nào khác tại `/v1/traces` và `/v1/metrics` (`pip install clawmetry[otel]` để nạp protobuf).

Bạn có được dashboard ClawMetry không cần cấu hình, ưu tiên cục bộ **và** dữ liệu của bạn trong bất kỳ backend nào đội của bạn đã sử dụng, không bị khóa nhà cung cấp, không cần cài thêm agent thứ hai.

## Cấu hình

Hầu hết mọi người không cần bất kỳ cấu hình nào. ClawMetry tự động phát hiện không gian làm việc, log, phiên và cron của bạn.

Nếu bạn cần tùy chỉnh:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tất cả tùy chọn: `clawmetry --help`

## Các kênh được hỗ trợ

ClawMetry hiển thị hoạt động trực tiếp cho mọi kênh OpenClaw mà bạn đã cấu hình. Chỉ những kênh thực sự được thiết lập trong `openclaw.json` của bạn mới xuất hiện trong sơ đồ Flow, các kênh chưa cấu hình sẽ tự động bị ẩn.

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
| 🍏 **BlueBubbles** | ✅ Đầy đủ | ✅ | iMessage qua BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Đầy đủ | ✅ | Qua webhook Chat API |
| 🟣 **MS Teams** | ✅ Đầy đủ | ✅ | Qua plugin bot Teams |
| 🔷 **Mattermost** | ✅ Đầy đủ | ✅ | Chat nhóm tự lưu trữ |
| 🟩 **Matrix** | ✅ Đầy đủ | ✅ | Phi tập trung, hỗ trợ E2EE |
| 🟢 **LINE** | ✅ Đầy đủ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Đầy đủ | ✅ | Tin nhắn riêng NIP-04 phi tập trung |
| 🟣 **Twitch** | ✅ Đầy đủ | ✅ | Chat qua kết nối IRC |
| 🔷 **Feishu/Lark** | ✅ Đầy đủ | ✅ | Đăng ký sự kiện WebSocket |
| 🔵 **Zalo** | ✅ Đầy đủ | ✅ | Zalo Bot API |

> **Tự động phát hiện:** ClawMetry đọc `~/.openclaw/openclaw.json` của bạn và chỉ hiển thị những kênh bạn đã thực sự cấu hình. Không cần thiết lập thủ công.

## Triển khai Docker

Muốn chạy ClawMetry trong container? Không vấn đề gì! 🐳

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

> **Lưu ý:** Khi chạy trong Docker, hãy gắn thư mục dữ liệu + log của agent (ví dụ `~/.openclaw`, `~/.claude`, `~/.codex`) để ClawMetry có thể tự động phát hiện thiết lập của bạn.

## Yêu cầu

- Python 3.8+
- Flask (được cài đặt tự động qua pip)
- Một runtime AI agent trên cùng máy: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, hoặc QM (hoặc các volume được gắn cho Docker)
- Linux hoặc macOS

## Hỗ trợ NemoClaw / OpenShell

ClawMetry tự động phát hiện [NemoClaw](https://github.com/NVIDIA/NemoClaw), lớp bảo mật doanh nghiệp của NVIDIA cho OpenClaw, chạy agent bên trong các container OpenShell được cách ly (sandbox).

Không cần cấu hình thêm trong hầu hết trường hợp. Daemon đồng bộ tự động phát hiện các tệp phiên dù chúng nằm trong `~/.openclaw/` trên máy chủ hay bên trong container OpenShell.

### Cách hoạt động

ClawMetry phát hiện NemoClaw theo hai cách:

1. **Phát hiện binary** — kiểm tra CLI `nemoclaw` và chạy `nemoclaw status` để lấy thông tin sandbox
2. **Phát hiện container** — quét các container Docker đang chạy để tìm hình ảnh `openshell`, `nemoclaw`, hoặc `ghcr.io/nvidia/`, sau đó đọc phiên qua volume mount hoặc `docker cp`

Các tệp phiên đồng bộ từ container NemoClaw được gắn thẻ với `runtime=nemoclaw` và metadata `container_id` trong dashboard cloud, để bạn có thể phân biệt chúng với các phiên OpenClaw tiêu chuẩn ngay khi nhìn qua.

### Thiết lập được khuyến nghị: daemon đồng bộ trên MÁY CHỦ

Để có trải nghiệm tốt nhất, hãy chạy daemon đồng bộ của ClawMetry trên **máy chủ** (không phải bên trong sandbox). Điều này tránh các hạn chế chính sách mạng của NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon đồng bộ sẽ tự động tìm các phiên bên trong bất kỳ container OpenShell nào đang chạy.

### Tùy chọn: tên sandbox rõ ràng

Nếu tự động phát hiện không hoạt động, hãy chỉ định ClawMetry đến đúng sandbox:

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
| Socket Docker (`/var/run/docker.sock`) | — | Unix socket | Để phát hiện phiên container |

Daemon đồng bộ chỉ thực hiện các cuộc gọi HTTPS đi đến `ingest.clawmetry.com`. Không cần cổng vào (inbound).

---

## Triển khai Cloud

Xem **[Hướng dẫn kiểm thử Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** để biết về SSH tunnel, reverse proxy, và Docker.

## Kiểm thử

Dự án này được kiểm thử với BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Đo lường từ xa (Telemetry)

ClawMetry gửi các tín hiệu vòng đời cài đặt ẩn danh đến
`https://app.clawmetry.com/api/install`: một tín hiệu `install` vào lần đầu
tiên bạn chạy CLI `clawmetry` trên một máy mới, một tín hiệu `update`
vào lần chạy đầu tiên sau khi nâng cấp lên phiên bản mới, và một tín hiệu
`onboarded` khi bạn hoàn thành lựa chọn giới thiệu (onboarding) trong dashboard.
Chúng tôi dùng dữ liệu này để đếm số lượt cài đặt thực (số liệu tải xuống PyPI thô
có khoảng 98% là mirror, CI, và tải lại tự động cập nhật) và để biết những
framework agent và phiên bản nào thực sự đang được sử dụng.

**Tối đa một POST cho mỗi sự kiện vòng đời cho mỗi phiên bản**, chứa:

| Trường | Ví dụ | Lý do |
|---|---|---|
| `install_id` | UUID ngẫu nhiên lưu tại `~/.clawmetry/install_id` | khử trùng lặp; ẩn danh cho đến khi bạn kết nối rõ ràng Cloud sync (heartbeat của daemon đã xác thực sau đó sẽ mang theo nó, liên kết bản cài đặt này với tài khoản của bạn) |
| `event` | `install` / `update` / `onboarded` | cài đặt mới hay nâng cấp bản có sẵn |
| `version` | `0.12.167` | phiên bản nào đang được sử dụng |
| `os` / `os_version` | `Darwin` / `25.3.0` | ưu tiên hỗ trợ nền tảng |
| `python` | `3.11.15` | ma trận hỗ trợ phiên bản Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | agent nào chúng tôi nên tích hợp tiếp theo |
| `is_ci` / `ci_provider` | `true` / `github_actions` | tách biệt cài đặt của con người khỏi nhiễu CI |

**Những gì chúng tôi KHÔNG gửi**: IP (cloud lấy mã quốc gia phía server
từ yêu cầu, sau đó loại bỏ IP), tên máy chủ, tên người dùng, đường dẫn
không gian làm việc, nội dung tệp, api_key của bạn, email của bạn, bất kỳ
thông tin PII hoặc thông tin đặc thù không gian làm việc nào. Tải trọng
truyền tải có thể kiểm toán trong
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Từ chối tham gia** (bất kỳ cách nào trong số này sẽ vô hiệu hóa vĩnh viễn):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Lỗi mạng ở đây không bao giờ chặn `clawmetry` chạy, tín hiệu này được gửi
theo kiểu bắn-rồi-quên (fire-and-forget) trên một luồng daemon với thời gian
chờ 3 giây.

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
