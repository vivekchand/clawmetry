<!-- i18n-src:88be2deff5d5 -->
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

**Xem agent của bạn suy nghĩ.** Khả năng quan sát theo thời gian thực cho **30 runtime AI agent**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 runtime khác. Một dashboard duy nhất cho toàn bộ đội hình agent của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một lệnh duy nhất. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900**. Không cần cấu hình: nó tìm ra các runtime agent
bạn đã có sẵn, đọc chúng ở chế độ chỉ đọc, và không thay đổi bất cứ điều gì trong cách chúng vận hành.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Hoạt động với 30 runtime agent

**Miễn phí trong ứng dụng mã nguồn mở:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Trên gói trả phí:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Mọi runtime đều có cùng một dashboard. Chạy nhiều runtime cùng lúc và bộ chuyển
đổi trên tiêu đề sẽ định phạm vi lại mỗi tab theo runtime bạn chọn.

Đã tự xây dựng agent riêng trên một SDK thay vì dùng sẵn? Bộ interceptor cũng
theo dõi các lệnh gọi LLM của nó. Xem [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Bạn nhận được gì

- **Phiên làm việc & bản ghi (transcripts)**: từng agent đã làm gì, theo từng lượt, kèm khả năng phát lại
- **Chi phí & token**: theo từng runtime, model, phiên làm việc và từng ngày, có cờ báo bất thường
- **Flow**: sơ đồ trực tiếp thể hiện tin nhắn di chuyển qua các kênh, model và công cụ
- **Brain**: luồng sự kiện suy luận và gọi công cụ ngay khi nó xảy ra
- **Context blowout (tràn ngữ cảnh)**: mức sử dụng cửa sổ ngữ cảnh được đo theo từng nhà cung cấp, so sánh nén (compaction) với tràn cưỡng bức, cùng bản đồ theo từng runtime về những gì chúng ta *không thể* thấy ([cách thực hiện](docs/CONTEXT_BLOWOUT.md))
- **Bộ nhớ & kỹ năng**: các tệp và kỹ năng mà từng runtime thực sự đã nạp
- **Sức khỏe & log**: đĩa, bộ nhớ, tỷ lệ lỗi, giới hạn tốc độ, luồng log trực tiếp
- **Cảnh báo**: giới hạn ngân sách, đột biến lỗi, agent ngoại tuyến, được định tuyến tới Slack, Discord, PagerDuty, Telegram, Email
- **Phê duyệt**: tạm dừng các lệnh gọi công cụ rủi ro *trước khi* chúng chạy và phê duyệt từ điện thoại của bạn ([cách thực hiện](docs/APPROVALS.md))

## Tràn ngữ cảnh, và chi phí của việc quan sát

Hai câu hỏi đáng được trả lời trước khi bạn tin tưởng bất kỳ công cụ so sánh agent nào.

**Nó xử lý tình trạng tràn cửa sổ ngữ cảnh (context-window blowout) trên các runtime như thế nào?**

Tỷ lệ phần trăm sử dụng chỉ trung thực bằng với mẫu số dùng để chia nó. ClawMetry
đo kích thước cửa sổ theo từng nhà cung cấp từ [một bảng bạn có thể đọc và
gửi PR](clawmetry/context_windows.py), bao gồm Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama và GLM. Nó không đo cả 30
runtime bằng thước đo của một nhà cung cấp duy nhất. Điều đó quan trọng: một lượt GPT-5 300K token
khi so với ngưỡng 200K của Anthropic sẽ đọc là ">100%, đã tràn" trong khi thực ra nó chỉ ở mức 75% của
400K của GPT-5. Cùng một thước đo đó lại che giấu một lượt DeepSeek 130K thực sự đã tràn
như thể nó thoải mái ở mức 65%.

Mỗi cửa sổ đều đi kèm nguồn gốc của nó: `model_table`, `explicit_marker`,
`observed_floor`, hoặc một giá trị `default` trung thực khi chúng tôi không biết model đó là gì. Một
đồng hồ đo dựa trên phỏng đoán không bao giờ hiển thị với cùng độ tin cậy như một đồng hồ dựa trên
một bảng tra cứu.

ClawMetry chỉ có thể thấy các sự kiện nén (compaction) trên một số runtime. Vì vậy
`GET /api/context-coverage` báo cáo, theo từng runtime, liệu giá trị 0 có nghĩa là
"chạy sạch" hay "chúng ta đang mù". Một giá trị `0` mà thực chất có nghĩa là mù sẽ nói rõ điều đó.
[Chi tiết đầy đủ](docs/CONTEXT_BLOWOUT.md)

**Việc đo lường (instrumentation) này tốn chi phí bao nhiêu?**

| Đường dẫn | Thêm vào agent của bạn | Mặc định? |
|---|---|---|
| Theo dõi tệp phiên (tailing) (cả 30 runtime) | **0**. Tiến trình riêng biệt, không có mã ClawMetry trong agent của bạn | bật |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** cho mỗi lệnh gọi LLM, tương đương 0.009% của một lệnh gọi 5 giây | tắt |
| Cổng hook trước-công-cụ (pre-tool hook gate) (bộ nhớ đệm ấm) | **+44 ms** cho mỗi lệnh gọi công cụ bị chặn, trên một mức sàn trình thông dịch 36 ms | tắt |
| Proxy thực thi (enforcement proxy) | **+9.7 ms** cho mỗi lệnh gọi LLM | tắt |

Chi phí máy chủ daemon: **2.762 sự kiện/giây** khi nạp dữ liệu, **710 byte/sự kiện** trên đĩa
(67.7 MB trên mỗi 100 nghìn sự kiện), và **~12% một lõi CPU** duy trì liên tục trên một bản cài đặt
bận rộn. Con số cuối cùng này vượt quá ngân sách 5-10% mà chúng tôi đã đề ra, vì vậy nó được
công bố như một lỗi cần khắc phục thay vì bị bỏ qua khỏi trang này.

Đo trên một Apple M2 Pro bằng `benchmarks/overhead.py`. Bộ khai thác (harness) chạy
mỗi điều kiện trong một tiến trình riêng biệt, luân phiên thứ tự của chúng, và **từ chối
in ra một con số khi các vòng chạy không thống nhất về dấu của nó**. Chạy nó trên máy
của chính bạn trong vòng một phút:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Mọi đường dẫn đều được đo, bao gồm cả các cổng hook và proxy thực thi,
và bộ khai thác này chạy trên Linux, macOS và Windows trong CI. Hai kết quả đáng
lưu ý: proxy tốn chi phí gấp khoảng bảy lần trên Windows so với Linux, và
daemon hiện đang duy trì khoảng 12% một lõi CPU, vượt quá ngân sách 5-10% của chính chúng tôi.
Dữ liệu JSON thô, phương pháp thực hiện, và những gì vẫn chưa được đo nằm trong
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Giá cả

| Gói | Bao gồm những gì | Giá |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard đầy đủ, chỉ chạy cục bộ | $0 |
| **Starter** | Mọi runtime khác ở trên, chế độ xem đội hình (fleet view), đồng bộ đám mây | $9 mỗi node / tháng |
| **Pro** | Starter + kiểm soát và đánh giá: phê duyệt, chính sách rủi ro công cụ, đánh giá (evals), phát hiện bất thường, tối ưu chi phí, xuất OTel, nhật ký kiểm toán chống giả mạo | $19 mỗi node / tháng |

Các gói hàng năm, Enterprise và các con số hiện tại nằm tại
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Khóa giấy phép tự lưu trữ
hoạt động mà không cần đám mây (`clawmetry license`). Sự phân chia chính xác giữa miễn phí/trả phí
nằm trong [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Dữ liệu của bạn luôn nằm trên máy của bạn

ClawMetry đọc các tệp phiên làm việc và log cục bộ. **Không dữ liệu phiên nào rời khỏi máy của bạn
trừ khi bạn chạy `clawmetry connect`** — không lời nhắc (prompt), phản hồi, tham số công cụ, nội dung tệp
hay dòng log nào cả. Khi bạn kết nối, snapshot được mã hóa đầu cuối (end-to-end)
với một khóa không bao giờ rời khỏi máy của bạn, và được giải mã ngay trong trình duyệt của bạn. Nếu một
node không có khóa, việc tải lên sẽ bị bỏ qua thay vì được gửi ở dạng không mã hóa, và không có
phản hồi nào từ máy chủ có thể tắt điều đó đi.

Có hai việc chạy mặc định trước khi bạn kết nối, cả hai đều có thể tắt (opt-out) và không mang
theo dữ liệu phiên: một ping cài đặt ẩn danh và một kiểm tra phiên bản so với
PyPI. Bản cài đặt mặc định cũng tra cứu địa chỉ IP công khai của bạn một lần cho dòng biểu ngữ
khởi động. Mọi điểm đến, những gì nó mang theo và cách tắt nó được liệt kê trong
[docs/EGRESS.md](docs/EGRESS.md); các bản cài đặt tự lưu trữ, được định tuyến lại và cô lập mạng (air-gapped)
không thực hiện bất kỳ lệnh gọi đi ra ngoài tùy ý nào cả.

Việc giải mã diễn ra trong trình duyệt của bạn, bằng mã mà chúng tôi cung cấp cho bạn. Điều đó từng
chỉ là một lời hứa; giờ đây nó là điều bạn có thể kiểm chứng. Mọi dòng chạm vào khóa của bạn
nằm trong một tệp có thể đọc được, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
tệp này đi kèm bên trong wheel và được phục vụ nguyên văn, được ghim bằng một mã băm Subresource
Integrity. Để xác nhận trình duyệt đang chạy đúng thứ chúng tôi đã công bố:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Điều đó không chứng minh được: chúng tôi phục vụ trang tải tệp đó, vì vậy chúng tôi có thể
phục vụ một trang khác. Các mã băm integrity bảo vệ bạn khỏi một CDN bị xâm nhập,
chứ không phải khỏi chính nhà cung cấp. Những gì bạn nhận được là bất kỳ sự thay thế nào cũng phải
có chủ đích, hiển thị trong mã nguồn trang, và khác với một tạo phẩm (artifact) trên PyPI
mà bất kỳ ai cũng có thể tải về. Việc tự lưu trữ hoặc chỉ dùng cục bộ sẽ loại bỏ hoàn toàn
sự phụ thuộc này.

## Cài đặt

```bash
pip install clawmetry     # sau đó: clawmetry
```

Hoặc dùng lệnh một dòng: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Cần Python 3.8+ trên macOS, Linux hoặc Windows, và ít nhất một runtime agent trên
cùng máy. Hướng dẫn Docker: [docs/DOCKER.md](docs/DOCKER.md).

Hoặc để agent thiết lập giúp bạn. Kỹ năng [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
dạy Claude Code, Codex, Cursor, Gemini CLI, Copilot hoặc OpenCode cách
cài đặt ClawMetry, báo cáo những gì các agent trên máy đang làm và đang chi tiêu,
dừng một phiên làm việc theo yêu cầu, và giữ lại các lệnh gọi công cụ rủi ro để chờ phê duyệt:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Tài liệu

| | |
|---|---|
| [Khả năng tương thích runtime](docs/compatibility.md) | Mỗi adapter đọc gì, và cách thêm một runtime |
| [Tràn ngữ cảnh](docs/CONTEXT_BLOWOUT.md) | Cửa sổ theo từng nhà cung cấp, nén so với tràn, độ phủ theo từng runtime |
| [Chi phí phát sinh (Overhead)](docs/OVERHEAD.md) | Chi phí đo lường của việc instrumentation, kèm bộ khai thác để tái tạo lại |
| [Quyền lợi (Entitlements)](docs/ENTITLEMENTS.md) | Miễn phí so với trả phí, ma trận hạng mức, CLI giấy phép |
| [Phê duyệt & chính sách](docs/APPROVALS.md) | Chặn trước khi thực thi, chấm điểm rủi ro, phê duyệt qua điện thoại |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Xuất trace ra bất cứ đâu, nạp OTLP từ bất cứ đâu |
| [Mang theo agent của riêng bạn](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain từ đầu đến cuối, kèm ví dụ chạy được |
| [Theo dõi SDK](docs/SDK_TRACKING.md) | Quy kết chi phí cho các agent bạn tự xây dựng |
| [Kênh trò chuyện](docs/CHANNELS.md) | Các adapter trò chuyện được hiển thị trong Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Các thiết lập NVIDIA NemoClaw trong sandbox |
| [Docker](docs/DOCKER.md) | Image, compose, gắn volume |
| [Kiến trúc](ARCHITECTURE.md) · [Phát triển](docs/DEVELOPMENT.md) | Cách nó hoạt động bên trong; chạy từ mã nguồn |
| [Telemetry](docs/TELEMETRY.md) | Các ping cài đặt và mở desktop ẩn danh, và cách tắt chúng |

## Ảnh chụp màn hình

Mỗi con số dưới đây đến từ một máy thật, chỉ đọc, không có gì được gieo trước.

**Nó cho bạn biết khi có gì đó sai, không chỉ là điều gì đã xảy ra.**
Hai biểu ngữ bất thường ở trên cùng: chi tiêu đang chạy gấp 7 lần mức trung bình hằng ngày, và một
đợt tăng vọt chi phí 4.2 lần. Bên dưới, 324 trong số 667 phiên làm việc gần đây mang một
tín hiệu lãng phí, được liệt kê theo từng nguyên nhân.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Nó cho bạn thấy tiền đã đi đâu, trong mọi khung thời gian.**
$252.47 hôm nay, $513.15 tuần này, $1.312.92 tháng này, mỗi con số đi kèm với token
đứng sau nó và bao nhiêu trong số đó gói đăng ký của bạn đã chi trả. Bên dưới đó,
khoảng $1.128/tháng được liệt kê là có thể thu hồi và $17.256/tháng đã được tiết kiệm
nhờ tái sử dụng bộ nhớ đệm (cache).

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Nó vẽ ra cách một tin nhắn trở thành một câu trả lời.**
Sơ đồ flow trực tiếp: bạn, kênh mà tin nhắn đến, gateway, model
đang trả lời ngay lúc này, và mọi công cụ mà nó đã sử dụng. Các node sáng lên khi công việc
di chuyển qua chúng.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Mọi agent trên máy, trong một bảng duy nhất.**
Nó chạy gì, chi phí bao nhiêu trong 24 giờ qua và trong suốt vòng đời của nó, khi
nào nó được nhìn thấy lần cuối, ai sở hữu nó, và liệu một gói đăng ký có đang chi trả cho
hóa đơn hay không. 14 agent tại đây, 3 phiên đang làm việc, 13 phiên yên lặng.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Nó cho thấy thời gian và tiền bạc của một lượt trao đổi đã đi đâu, theo từng công cụ.**
Một lượt trao đổi của một phiên thực: 11 công cụ trong 11.2 phút với giá $1.16. Mỗi lệnh gọi
Bash và lệnh gọi model đều có thanh riêng của nó trên dòng thời gian, để lệnh chạy
trong 4.1 phút và lệnh chạy trong 226ms được phân biệt rõ ràng chỉ trong một cái nhìn.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Nó chấm điểm công việc, không chỉ chi tiêu.**
Một điểm A trong tuần này: 54 tác vụ hoàn thành sạch sẽ, 2 tác vụ gập ghềnh tốn $48.57, và các
lượt chạy có quá ít hoạt động để đánh giá được loại bỏ khỏi điểm số thay vì được tính là
thành công. Mỗi lượt chạy gập ghềnh đều liên kết tới trace của nó.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Nó cho thấy tại sao cửa sổ ngữ cảnh liên tục bị lấp đầy.**
715K trong tổng số 1M token cửa sổ trong lượt trao đổi mới nhất, đỉnh 83.3%, 4 lần nén
đều xảy ra một cách chủ động thay vì do tràn, và mức sử dụng của mỗi lượt trao đổi
đứng sau nó.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Việc phát hiện hoạt động mà không cần bạn cấu hình bất cứ điều gì.**
Các bộ phát hiện tích hợp sẵn được bật ngay từ khi cài đặt: agent im lặng, luồng telemetry
dừng lại, chi phí tăng vọt, bùng nổ token, lỗi gia tăng, đột biến lỗi, ngưỡng
ngân sách, khớp mẫu đe dọa (threat signature), phát hiện từ công cụ bảo mật, thay đổi tư thế
bảo mật. Các quy tắc của riêng bạn là tùy chọn thêm vào.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Việc giữ lại một lệnh gọi rủi ro là tùy chọn (opt-in), và được xuất xưởng ở trạng thái tắt.**
Xóa đệ quy, force push, sudo, thông tin bí mật (secrets), cài đặt gói và các lệnh gọi ra ngoài
đều có một quy tắc riêng mà bạn có thể bật. Cho tới khi bạn làm vậy, ClawMetry chỉ quan sát và
không thay đổi gì cả. Một khi được bật, các lệnh gọi khớp sẽ chờ tại đây (hoặc trên điện thoại của bạn)
để được phê duyệt hoặc từ chối.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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
