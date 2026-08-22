<!-- i18n-src:6795052055e2 -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Xem agent của bạn suy nghĩ.** Khả năng quan sát theo thời gian thực cho **26 runtime AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 22 runtime khác. Một dashboard duy nhất cho toàn bộ đội agent của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [xem thêm →](docs/i18n/)

Một lệnh duy nhất. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900**. Không cần cấu hình: nó tự tìm các runtime agent bạn đã có, đọc chúng ở chế độ chỉ đọc, và không thay đổi gì trong cách chúng vận hành.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Hoạt động với 26 runtime agent

**Miễn phí trong ứng dụng mã nguồn mở:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Trong gói trả phí:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Mỗi runtime đều nhận cùng một dashboard. Chạy nhiều runtime cùng lúc và bộ chuyển đổi ở phần đầu sẽ định phạm vi lại cho mọi tab về một trong số chúng.

Đã tự xây dựng agent của riêng bạn trên một SDK? Bộ interceptor cũng theo dõi các lệnh gọi LLM của nó. Xem [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Bạn nhận được gì

- **Phiên làm việc & bản ghi (transcript)**: mỗi agent đã làm gì, từng lượt một, có thể phát lại
- **Chi phí & token**: theo runtime, mô hình, phiên làm việc và ngày, kèm cảnh báo bất thường
- **Flow**: sơ đồ trực tiếp của các thông điệp di chuyển qua các kênh, mô hình và công cụ
- **Brain**: luồng sự kiện suy luận và gọi công cụ khi nó diễn ra
- **Memory & skills**: các tệp và kỹ năng mà mỗi runtime thực sự đã tải
- **Health & logs**: đĩa, bộ nhớ, tỷ lệ lỗi, giới hạn tốc độ, luồng log trực tiếp
- **Alerts**: giới hạn ngân sách, tăng đột biến lỗi, agent ngoại tuyến, chuyển tới Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: tạm dừng các lệnh gọi công cụ rủi ro *trước khi* chúng chạy và phê duyệt từ điện thoại của bạn ([cách thực hiện](docs/APPROVALS.md))

## Bảng giá

| Gói | Bao gồm | Giá |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard đầy đủ, chỉ chạy cục bộ | $0 |
| **Starter** | Mọi runtime khác ở trên, chế độ xem đội (fleet view), đồng bộ đám mây | $9 mỗi node / tháng |
| **Pro** | Starter + quản trị: phê duyệt, chính sách rủi ro công cụ, đánh giá (evals), phát hiện bất thường, tối ưu chi phí, xuất OTel | $19 mỗi node / tháng |

Các gói hàng năm, Enterprise và mức giá hiện tại có tại
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Khóa bản quyền tự lưu trữ
hoạt động không cần đám mây (`clawmetry license`). Sự phân chia chính xác giữa miễn phí/trả phí
nằm trong [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Dữ liệu của bạn luôn ở trên máy của bạn

ClawMetry đọc các tệp phiên làm việc và log cục bộ. Không có gì rời khỏi máy của bạn trừ khi
bạn chạy `clawmetry connect`. Ngay cả khi đó, ảnh chụp nhanh (snapshot) cũng được mã hóa đầu cuối
với một khóa không bao giờ rời khỏi máy của bạn, và được giải mã ngay trên trình duyệt của bạn.

## Cài đặt

```bash
pip install clawmetry     # sau đó: clawmetry
```

Hoặc dùng lệnh một dòng: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Cần Python 3.8+ trên macOS, Linux hoặc Windows, và ít nhất một runtime agent trên
cùng một máy. Hướng dẫn Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Tài liệu

| | |
|---|---|
| [Khả năng tương thích runtime](docs/compatibility.md) | Mỗi adapter đọc gì, và cách thêm một runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Miễn phí so với trả phí, bảng cấp độ, CLI license |
| [Phê duyệt & chính sách](docs/APPROVALS.md) | Kiểm soát trước khi thực thi, chấm điểm rủi ro, phê duyệt qua điện thoại |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Xuất trace tới bất kỳ đâu, nhập OTLP từ bất kỳ đâu |
| [Theo dõi SDK](docs/SDK_TRACKING.md) | Quy kết chi phí cho các agent bạn tự xây dựng |
| [Kênh chat](docs/CHANNELS.md) | Các adapter chat được hiển thị trong Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Các thiết lập NVIDIA NemoClaw dạng sandbox |
| [Docker](docs/DOCKER.md) | Image, compose, gắn kết volume |
| [Kiến trúc](ARCHITECTURE.md) · [Phát triển](docs/DEVELOPMENT.md) | Cách nó hoạt động bên trong; chạy từ mã nguồn |
| [Telemetry](docs/TELEMETRY.md) | Các ping ẩn danh khi cài đặt và mở desktop, và cách tắt chúng |

## Ảnh chụp màn hình

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: token, phiên làm việc, sức khỏe hệ thống | **Brain**: luồng sự kiện agent trực tiếp |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: theo mô hình và phiên làm việc | **Approvals**: kiểm soát các lệnh gọi công cụ rủi ro |

Thêm nữa, theo từng runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Lịch sử Star

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Giấy phép

MIT · Được xây dựng bởi [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
