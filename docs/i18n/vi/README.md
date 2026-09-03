<!-- i18n-src:9767c8001c9c -->
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

**Xem tác nhân của bạn suy nghĩ.** Khả năng quan sát theo thời gian thực cho **30 runtime tác nhân AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 runtime khác. Một bảng điều khiển cho toàn bộ đội tác nhân của bạn.

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [xem thêm →](docs/i18n/)

Một câu lệnh. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900**. Không cần cấu hình: nó tìm ra các runtime tác nhân
bạn đã có sẵn, đọc chúng ở chế độ chỉ đọc, và không thay đổi bất cứ điều gì trong cách chúng chạy.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Hoạt động với 30 runtime tác nhân

**Miễn phí trong ứng dụng mã nguồn mở:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Trong gói trả phí:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Mọi runtime đều dùng chung một bảng điều khiển. Chạy nhiều runtime cùng lúc và bộ chuyển
đổi trên đầu trang sẽ định phạm vi lại mỗi tab theo runtime bạn chọn.

Đã tự xây dựng tác nhân của riêng bạn trên một SDK? Bộ chặn (interceptor) vẫn theo dõi
các lệnh gọi LLM của nó. Xem [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Bạn nhận được gì

- **Phiên & bản ghi hội thoại (transcript)**: mỗi tác nhân đã làm gì, theo từng lượt, có thể phát lại
- **Chi phí & token**: theo từng runtime, model, phiên và ngày, kèm cờ báo bất thường
- **Flow**: sơ đồ trực tiếp về các tin nhắn di chuyển qua các kênh, model và công cụ
- **Brain**: luồng sự kiện suy luận và gọi công cụ khi nó diễn ra
- **Tràn ngữ cảnh (context blowout)**: mức sử dụng cửa sổ được tính theo từng nhà cung cấp, so sánh nén (compaction) với tràn cưỡng bức, cùng bản đồ theo từng runtime về những gì chúng ta *không* thấy được ([cách hoạt động](docs/CONTEXT_BLOWOUT.md))
- **Bộ nhớ & kỹ năng**: các tệp và kỹ năng mà mỗi runtime thực sự đã tải
- **Sức khỏe & nhật ký**: dung lượng đĩa, bộ nhớ, tỷ lệ lỗi, giới hạn tốc độ, luồng nhật ký trực tiếp
- **Cảnh báo**: giới hạn ngân sách, đột biến lỗi, tác nhân ngoại tuyến, chuyển đến Slack, Discord, PagerDuty, Telegram, Email
- **Phê duyệt**: tạm dừng các lệnh gọi công cụ rủi ro *trước khi* chúng chạy và phê duyệt từ điện thoại của bạn ([cách hoạt động](docs/APPROVALS.md))

## Tràn ngữ cảnh, và chi phí của việc theo dõi

Hai câu hỏi đáng trả lời trước khi bạn tin tưởng bất kỳ công cụ so sánh tác nhân nào.

**Nó xử lý tình trạng tràn cửa sổ ngữ cảnh trên các runtime như thế nào?**

Tỷ lệ phần trăm sử dụng chỉ trung thực bằng với mẫu số dùng để chia nó. ClawMetry
tính kích thước cửa sổ theo từng nhà cung cấp từ [một bảng bạn có thể đọc và
gửi PR](clawmetry/context_windows.py), bao gồm Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama và GLM. Nó không đo cả 26 runtime bằng
thước đo của một nhà cung cấp duy nhất. Điều đó quan trọng: một lượt GPT-5 300K
được chấm điểm theo mức 200K của Anthropic sẽ đọc là ">100%, đã tràn" trong khi
thực tế chỉ ở mức 75% trong tổng 400K của GPT-5. Cùng một thước đo đó lại che
giấu một lượt DeepSeek 130K thực sự đã tràn thành một con số 65% có vẻ thoải mái.

Mỗi cửa sổ đi kèm nguồn gốc của nó: `model_table`, `explicit_marker`,
`observed_floor`, hoặc một giá trị `default` trung thực khi chúng ta không biết
model đó. Một đồng hồ đo được xây dựng trên một phỏng đoán sẽ không bao giờ hiển
thị với cùng độ tin cậy như một đồng hồ được xây dựng trên một tra cứu thực tế.

ClawMetry chỉ có thể thấy các sự kiện nén (compaction) trên một số runtime nhất
định. Vì vậy `GET /api/context-coverage` báo cáo, theo từng runtime, liệu một
**số 0 nghĩa là "chạy sạch" hay "chúng ta bị mù"**. Một số `0` thực sự có nghĩa
là bị mù sẽ được nói rõ như vậy. [Chi tiết đầy đủ](docs/CONTEXT_BLOWOUT.md)

**Việc đo lường (instrumentation) này tốn chi phí gì?**

| Đường dẫn | Thêm vào tác nhân của bạn | Mặc định? |
|---|---|---|
| Theo dõi tệp phiên (tất cả 30 runtime) | **0**. Tiến trình riêng biệt, không có mã ClawMetry trong tác nhân của bạn | bật |
| Bộ chặn HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** mỗi lệnh gọi LLM, tức 0.009% của một lệnh gọi 5s | tắt |
| Cổng hook tiền công cụ (bộ nhớ đệm ấm) | **+44 ms** mỗi lệnh gọi công cụ bị cổng chặn, trên nền 36 ms của trình thông dịch | tắt |
| Proxy thực thi | **+9.7 ms** mỗi lệnh gọi LLM | tắt |

Chi phí máy chủ daemon: **2.762 sự kiện/giây** nạp vào, **710 byte/sự kiện** trên
đĩa (67.7 MB trên mỗi 100 nghìn sự kiện), và **~12% một lõi** duy trì liên tục
trên một bản cài đặt bận rộn. Con số cuối cùng đó vượt quá ngân sách 5-10% mà
chúng tôi tự đặt ra, vì vậy nó được công bố như một lỗi cần khắc phục thay vì bị
bỏ qua khỏi trang này.

Được đo trên Apple M2 Pro bằng `benchmarks/overhead.py`. Bộ khai thác (harness)
chạy mỗi điều kiện trong một tiến trình riêng biệt, đảo thứ tự chúng, và **từ chối
in ra một con số khi các vòng chạy không đồng nhất về dấu (âm/dương)**. Chạy nó
trên máy của chính bạn trong một phút:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Mọi đường dẫn đều được đo, bao gồm cả các cổng hook và proxy thực thi, và bộ
khai thác chạy trên Linux, macOS và Windows trong CI. Hai kết quả đáng biết:
proxy tốn chi phí gấp khoảng bảy lần trên Windows so với trên Linux, và daemon
hiện đang duy trì khoảng 12% của một lõi, vượt quá ngân sách 5-10% mà chúng tôi
tự đặt ra. Dữ liệu JSON thô, phương pháp thực hiện, và những gì vẫn chưa được
đo nằm trong [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Giá cả

| Gói | Bao gồm những gì | Giá |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, bảng điều khiển đầy đủ, chỉ local | $0 |
| **Starter** | Mọi runtime khác ở trên, chế độ xem đội (fleet view), đồng bộ đám mây | $9 mỗi node / tháng |
| **Pro** | Starter + kiểm soát và đánh giá: phê duyệt, chính sách rủi ro công cụ, đánh giá (evals), phát hiện bất thường, tối ưu hóa chi phí, xuất OTel, nhật ký kiểm toán chống giả mạo | $19 mỗi node / tháng |

Các gói theo năm, Enterprise và các con số hiện tại được cập nhật tại
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Khóa giấy phép tự lưu
trữ hoạt động mà không cần đám mây (`clawmetry license`). Sự phân chia chính xác
giữa miễn phí/trả phí nằm trong [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Dữ liệu của bạn ở lại trên máy của bạn

ClawMetry đọc các tệp phiên và nhật ký cục bộ. **Không có dữ liệu phiên nào rời
khỏi máy của bạn trừ khi bạn chạy `clawmetry connect`** — không có lời nhắc,
phản hồi, tham số công cụ, nội dung tệp hay dòng nhật ký nào. Khi bạn kết nối,
bản ảnh chụp nhanh (snapshot) được mã hóa đầu cuối bằng một khóa không bao giờ
rời khỏi máy của bạn, và được giải mã trong trình duyệt của bạn. Nếu một node
không có khóa, việc tải lên sẽ bị bỏ qua thay vì được gửi ở dạng không mã hóa,
và không có phản hồi máy chủ nào có thể tắt điều đó.

Có hai điều chạy mặc định trước khi bạn kết nối, cả hai đều có thể tắt và không
mang theo dữ liệu phiên nào: một ping cài đặt ẩn danh và một kiểm tra phiên bản
với PyPI. Một bản cài đặt mặc định cũng tra cứu địa chỉ IP công khai của bạn một
lần cho một dòng biểu ngữ khởi động. Mọi điểm đến, những gì nó mang theo và cách
tắt nó được liệt kê trong [docs/EGRESS.md](docs/EGRESS.md); các bản cài đặt tự
lưu trữ, được định tuyến lại và cách ly mạng (air-gapped) không thực hiện bất kỳ
cuộc gọi ra ngoài tùy ý nào cả.

Việc giải mã diễn ra trong trình duyệt của bạn, bằng mã mà chúng tôi cung cấp cho
bạn. Điều đó trước đây là một lời hứa; giờ đây nó là điều bạn có thể kiểm tra.
Mọi dòng chạm vào khóa của bạn nằm trong một tệp dễ đọc,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), được đóng gói
bên trong wheel và phục vụ nguyên văn, được ghim với một mã băm Subresource
Integrity. Để xác nhận trình duyệt chạy đúng những gì chúng tôi đã công bố:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Điều đó không chứng minh được là: chúng tôi phục vụ trang tải tệp này, vì vậy
chúng tôi có thể phục vụ một trang khác. Mã băm integrity bảo vệ bạn khỏi một CDN
bị xâm phạm, chứ không phải khỏi chính nhà cung cấp. Điều bạn có được là bất kỳ
sự thay thế nào cũng phải là cố ý, hiển thị trong mã nguồn trang, và khác với một
artifact trên PyPI mà bất kỳ ai cũng có thể tải về. Việc tự lưu trữ hoặc chỉ dùng
cục bộ sẽ loại bỏ hoàn toàn sự phụ thuộc này.

## Cài đặt

```bash
pip install clawmetry     # sau đó: clawmetry
```

Hoặc dùng lệnh một dòng: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Yêu cầu Python 3.8+ trên macOS, Linux hoặc Windows, và ít nhất một runtime tác
nhân trên cùng máy. Hướng dẫn Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Tài liệu

| | |
|---|---|
| [Khả năng tương thích runtime](docs/compatibility.md) | Mỗi adapter đọc gì, và cách thêm một runtime |
| [Tràn ngữ cảnh](docs/CONTEXT_BLOWOUT.md) | Cửa sổ theo từng nhà cung cấp, so sánh nén và tràn, độ bao phủ theo từng runtime |
| [Chi phí phụ trội](docs/OVERHEAD.md) | Chi phí của việc đo lường, đã được đo, kèm bộ khai thác để tái tạo |
| [Quyền lợi (Entitlements)](docs/ENTITLEMENTS.md) | Miễn phí so với trả phí, ma trận cấp bậc, CLI giấy phép |
| [Phê duyệt & chính sách](docs/APPROVALS.md) | Cổng chặn trước khi thực thi, chấm điểm rủi ro, phê duyệt qua điện thoại |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Xuất trace tới bất cứ đâu, nạp OTLP từ bất cứ nguồn nào |
| [Mang theo tác nhân của riêng bạn](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain từ đầu đến cuối, kèm ví dụ có thể chạy được |
| [Theo dõi SDK](docs/SDK_TRACKING.md) | Quy kết chi phí cho các tác nhân bạn tự xây dựng |
| [Kênh trò chuyện](docs/CHANNELS.md) | Các adapter trò chuyện được hiển thị trong Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Các thiết lập NVIDIA NemoClaw trong sandbox |
| [Docker](docs/DOCKER.md) | Image, compose, gắn kết volume |
| [Kiến trúc](ARCHITECTURE.md) · [Phát triển](docs/DEVELOPMENT.md) | Cách hoạt động bên trong; chạy từ mã nguồn |
| [Telemetry](docs/TELEMETRY.md) | Các ping cài đặt ẩn danh và mở desktop, và cách tắt chúng |

## Ảnh chụp màn hình

Mỗi con số dưới đây đến từ một máy thật, chỉ đọc, không có gì được gieo sẵn (seeded).

**Nó cho bạn biết khi có điều gì đó sai, chứ không chỉ những gì đã xảy ra.**
Hai biểu ngữ bất thường ở trên cùng: chi tiêu chạy gấp 7 lần mức trung bình hàng
ngày, và một đợt tăng vọt chi phí 4.2 lần. Bên dưới chúng, 324 trong số 667 phiên
gần đây mang tín hiệu lãng phí, được liệt kê theo nguyên nhân.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Nó cho bạn thấy tiền đã đi đâu, trong mọi khung thời gian.**
$252.47 hôm nay, $513.15 tuần này, $1.312.92 tháng này, mỗi con số kèm theo
lượng token đứng sau nó và bao nhiêu phần trong đó đã được gói đăng ký của bạn
chi trả. Bên dưới đó, khoảng $1.128/tháng được liệt kê là có thể thu hồi và
$17.256/tháng đã được tiết kiệm nhờ tái sử dụng bộ nhớ đệm.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Nó vẽ ra cách một tin nhắn trở thành một câu trả lời.**
Sơ đồ luồng trực tiếp: bạn, kênh mà tin nhắn đến, gateway, model đang trả lời
ngay lúc này, và mọi công cụ mà nó đã sử dụng. Các nút sáng lên khi công việc
di chuyển qua chúng.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Mọi tác nhân trên máy, trong một bảng duy nhất.**
Nó đang chạy gì, chi phí bao nhiêu trong 24 giờ qua và trong toàn bộ vòng đời,
lần cuối được thấy khi nào, ai sở hữu nó, và liệu một gói đăng ký có đang chi
trả hóa đơn hay không. 14 tác nhân ở đây, 3 phiên đang làm việc, 13 đang yên lặng.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Nó cho thấy thời gian và tiền bạc của một lượt đã đi đâu, theo từng công cụ.**
Một lượt của một phiên thực: 11 công cụ trong 11.2 phút với giá $1.16. Mỗi lệnh
gọi Bash và lệnh gọi model có thanh riêng của nó trên dòng thời gian, để lệnh
chạy trong 4.1 phút và lệnh chạy trong 226ms được phân biệt chỉ với một cái liếc mắt.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Nó chấm điểm công việc, không chỉ chi tiêu.**
Một điểm A trong tuần này: 54 tác vụ trở lại gọn gàng, 2 tác vụ khó khăn tốn
$48.57, và các lượt chạy có quá ít hoạt động để đánh giá được loại khỏi bảng
điểm thay vì được tính là thành công. Mỗi lượt khó khăn liên kết đến trace của nó.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Nó cho thấy tại sao cửa sổ ngữ cảnh liên tục đầy lên.**
715K trong tổng cửa sổ 1M-token ở lượt mới nhất, một đỉnh 83.3%, 4 lần nén đều
được kích hoạt một cách chủ động thay vì do tràn, cùng mức sử dụng của mọi lượt
đứng sau nó.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Việc phát hiện hoạt động mà không cần bạn cấu hình gì cả.**
Các bộ phát hiện tích hợp sẵn được bật ngay từ khi cài đặt: tác nhân im lặng,
nguồn cấp telemetry ngừng hoạt động, đột biến chi phí, bùng nổ token, lỗi tăng
dần, đột biến lỗi, ngưỡng ngân sách, chữ ký mối đe dọa khớp, phát hiện từ công
cụ bảo mật, thay đổi tư thế bảo mật. Các quy tắc của riêng bạn là tùy chọn thêm vào.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Việc giữ lại một lệnh gọi rủi ro là tùy chọn, và được vận chuyển ở trạng thái tắt.**
Xóa đệ quy, force push, sudo, bí mật (secrets), cài đặt gói và các lệnh gọi ra
ngoài đều có một quy tắc bạn có thể bật. Cho đến khi bạn bật, ClawMetry chỉ theo
dõi và không thay đổi gì cả. Khi một quy tắc được bật, các lệnh gọi khớp sẽ chờ
ở đây (hoặc trên điện thoại của bạn) để được phê duyệt hoặc từ chối.

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
