<!-- i18n-src:61beb8393e2f -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Một agent có thể thực hiện hàng trăm lệnh gọi công cụ mà không hề đạt được tiến triển nào.** ClawMetry
đọc các tệp phiên làm việc mà các agent lập trình của bạn đã ghi lại, rồi tổng hợp dòng thời gian,
các lệnh gọi công cụ và bất kỳ dữ liệu token, chi phí nào mà runtime cung cấp vào một
màn hình duy nhất — nhờ đó bạn có thể phân biệt một phiên chạy dài đang hoạt động tốt với một phiên đang bị kẹt.

Hoạt động với **30 runtime AI agent** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 26 runtime khác. Một bảng điều khiển duy nhất cho toàn bộ đội agent của bạn. ([danh sách đầy đủ](SUPPORTED_RUNTIMES.txt), được tạo tự động từ catalogue.)

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một lệnh duy nhất. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900**. Không cần cấu hình: nó tìm ra các runtime agent
mà bạn đã có sẵn, đọc chúng ở chế độ chỉ đọc, và không thay đổi bất cứ điều gì trong cách chúng vận hành.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Trước khi bạn cài đặt

| | |
|---|---|
| **Nó làm gì** | Đọc các tệp phiên làm việc và log mà các agent của bạn đã ghi sẵn. Không cần SDK, không cần thay đổi mã nguồn, không cần thêm bất kỳ đoạn đo lường nào vào ứng dụng của bạn. |
| **Bạn thấy gì** | Dòng thời gian phiên làm việc, phát lại từng công cụ một, phân tích token và chi phí, cùng các tín hiệu quỹ đạo (lặp vòng, lỗi lặp lại) — theo từng runtime. |
| **Cái gì miễn phí** | `pip install clawmetry` đọc được **OpenClaw, NVIDIA NemoClaw và Goose** mà không cần tài khoản, không cần khóa và không có bất kỳ lệnh gọi mạng nào. 27 runtime còn lại — Claude Code, Codex, Cursor và các runtime khác — được đọc bởi phần bổ trợ mã nguồn đóng `clawmetry-pro`, đi kèm với bản dùng thử 7 ngày hoặc một gói trả phí — xem [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) để biết chi tiết chính xác về sự phân chia này. |
| **Cách bắt đầu** | `pip install clawmetry && clawmetry`, sau đó mở localhost:8900. Chưa có agent nào trên máy này? `clawmetry --sample` sẽ mở với ba phiên tổng hợp mẫu được gắn nhãn rõ ràng. |
| **Điều gì rời khỏi máy của bạn** | Không có dữ liệu phiên làm việc nào, trừ khi bạn chạy `clawmetry connect`. Mặc định có hai thứ chạy sẵn, cả hai đều có thể tắt và không mang theo bất kỳ nội dung phiên nào: một tín hiệu ping cài đặt ẩn danh và một lượt kiểm tra phiên bản PyPI. Mọi đích đến đều được liệt kê trong [docs/EGRESS.md](docs/EGRESS.md), được dựng lại từ việc bắt gói tin trên đường truyền chứ không phải từ việc đọc chú thích mã nguồn. |

Có hai giới hạn đáng biết trước khi bạn đánh giá kết quả: các runtime cung cấp
dữ liệu rất khác nhau (một số hoàn toàn không công bố chi phí — [bảng so sánh](docs/compatibility.md)
cho biết runtime nào, cho từng runtime), và việc quan sát một hành động không đồng nghĩa với việc có thể
chặn nó ([những quyền kiểm soát nào là thật, theo từng runtime](docs/APPROVALS.md)).


## Hoạt động với 30 runtime agent

**Miễn phí trong ứng dụng mã nguồn mở:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Trên gói trả phí:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Mọi runtime đều được hiển thị trên cùng một bảng điều khiển. Chạy nhiều runtime cùng lúc và
bộ chuyển đổi trên tiêu đề sẽ định phạm vi lại cho mỗi tab theo runtime bạn chọn.

Bạn tự xây dựng agent của riêng mình dựa trên một SDK? Bộ chặn (interceptor) cũng theo dõi
các lệnh gọi LLM của nó. Xem [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Bạn nhận được gì

- **Phiên làm việc & bản ghi hội thoại**: từng agent đã làm gì, theo từng lượt, kèm khả năng phát lại
- **Chi phí & token**: theo runtime, mô hình, phiên làm việc và theo ngày, kèm cờ báo bất thường
- **Flow (luồng dữ liệu)**: sơ đồ trực quan thời gian thực về tin nhắn di chuyển qua các kênh, mô hình và công cụ
- **Brain (bộ não)**: dòng sự kiện suy luận và gọi công cụ khi nó diễn ra
- **Tràn ngữ cảnh (context blowout)**: mức sử dụng cửa sổ ngữ cảnh theo từng nhà cung cấp, so sánh nén (compaction) với tràn cưỡng bức, cùng một bản đồ theo từng runtime về những gì chúng ta *không thể* thấy ([cách hoạt động](docs/CONTEXT_BLOWOUT.md))
- **Bộ nhớ & kỹ năng (skills)**: các tệp và kỹ năng mà mỗi runtime thực sự đã tải
- **Sức khỏe hệ thống & log**: dung lượng đĩa, bộ nhớ, tỷ lệ lỗi, giới hạn tốc độ, luồng log trực tiếp
- **Cảnh báo**: giới hạn ngân sách, đột biến lỗi, agent ngoại tuyến, được định tuyến tới Slack, Discord, PagerDuty, Telegram, Email
- **Phê duyệt**: tạm dừng các lệnh gọi công cụ rủi ro *trước khi* chúng chạy và phê duyệt ngay từ điện thoại của bạn ([cách hoạt động](docs/APPROVALS.md))

## Tràn ngữ cảnh, và cái giá của việc theo dõi nó

Hai câu hỏi đáng được trả lời trước khi bạn tin tưởng bất kỳ công cụ so sánh agent nào.

**Nó xử lý tình trạng tràn cửa sổ ngữ cảnh giữa các runtime như thế nào?**

Một tỷ lệ phần trăm sử dụng chỉ trung thực khi mẫu số của nó chính xác. ClawMetry
định cỡ cửa sổ theo từng nhà cung cấp từ [một bảng mà bạn có thể đọc và
gửi PR](clawmetry/context_windows.py), bao gồm Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama và GLM. Nó không đo cả 30
runtime bằng thước đo của một nhà cung cấp duy nhất. Điều này quan trọng: một lượt GPT-5 300K
token khi được đánh giá theo mức 200K của Anthropic sẽ hiển thị ">100%, đã tràn" trong khi thực ra
nó chỉ đang ở mức 75% trong tổng 400K của GPT-5. Cùng một thước đo đó lại che giấu một lượt
DeepSeek 130K thực sự đã tràn thành một con số 65% có vẻ thoải mái.

Mỗi cửa sổ đi kèm với nguồn gốc của nó: `model_table`, `explicit_marker`,
`observed_floor`, hoặc một giá trị `default` trung thực khi chúng tôi không biết mô hình đó là gì. Một
đồng hồ đo dựng trên một phỏng đoán không bao giờ hiển thị với cùng độ tin cậy như một đồng hồ dựng
trên một bảng tra cứu thực tế.

ClawMetry chỉ có thể thấy các sự kiện nén (compaction) trên một số runtime. Vì vậy
`GET /api/context-coverage` báo cáo, theo từng runtime, liệu giá trị **0 có nghĩa là "chạy sạch"
hay "chúng ta bị mù"**. Một giá trị `0` mà thực chất có nghĩa là mù thì sẽ nói rõ điều đó.
[Chi tiết đầy đủ](docs/CONTEXT_BLOWOUT.md)

**Việc đo lường này tốn kém bao nhiêu?**

| Đường dẫn | Thêm vào agent của bạn | Mặc định? |
|---|---|---|
| Theo dõi tệp phiên làm việc (tailing, cả 30 runtime) | **0**. Là một tiến trình riêng biệt, không có mã ClawMetry nào trong agent của bạn | bật |
| Bộ chặn HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** cho mỗi lệnh gọi LLM, tương đương 0,009% của một lệnh gọi 5 giây | tắt |
| Cổng hook trước-công-cụ (bộ nhớ đệm ấm) | **+44 ms** cho mỗi lệnh gọi công cụ bị chặn, trên nền tảng interpreter mất 36 ms | tắt |
| Proxy thực thi chính sách | **+9,7 ms** cho mỗi lệnh gọi LLM | tắt |

Chi phí máy chủ daemon: **2.762 sự kiện/giây** khi tiếp nhận, **710 byte/sự kiện** trên đĩa
(67,7 MB cho mỗi 100 nghìn sự kiện), và **~12% một lõi CPU** duy trì trên một bản cài đặt
đang hoạt động bận rộn. Con số cuối cùng này vượt quá ngân sách 5-10% mà chúng tôi đã công bố, nên nó
được công bố như một lỗi cần khắc phục thay vì bị lược bỏ khỏi trang tài liệu.

Đo trên Apple M2 Pro bằng `benchmarks/overhead.py`. Bộ khai thác này chạy
mỗi điều kiện trong một tiến trình riêng biệt, luân phiên thứ tự của chúng, và **từ chối
in ra một con số khi các vòng đo không đồng nhất về dấu**. Bạn có thể tự chạy nó trên
máy của mình trong vòng một phút:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Mọi đường dẫn đều được đo lường, bao gồm cả các cổng hook và proxy thực thi chính sách,
và bộ khai thác chạy trên Linux, macOS và Windows trong CI. Có hai kết quả đáng chú ý: proxy
tốn kém gấp khoảng bảy lần trên Windows so với trên Linux, và
daemon hiện đang duy trì khoảng 12% một lõi CPU, vượt quá ngân sách 5-10% mà chúng tôi đã đề ra.
Dữ liệu JSON thô, phương pháp đo, và những gì vẫn chưa được đo lường đều có trong
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Bảng giá

| Gói | Bao gồm những gì | Giá |
|---|---|---|
| **Miễn phí** | OpenClaw + NVIDIA NemoClaw + Goose, bảng điều khiển đầy đủ, chỉ chạy cục bộ | $0 |
| **Starter** | Mọi runtime khác ở trên, chế độ xem đội (fleet view), đồng bộ đám mây | $9 mỗi node / tháng |
| **Pro** | Starter + kiểm soát và đánh giá: phê duyệt, chính sách rủi ro công cụ, đánh giá (evals), phát hiện bất thường, tối ưu chi phí, xuất OTel, nhật ký kiểm toán chống giả mạo | $19 mỗi node / tháng |

Các gói hàng năm, gói Enterprise và các con số hiện hành đều có tại
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Khóa giấy phép tự lưu trữ (self-hosted)
hoạt động mà không cần đám mây (`clawmetry license`). Sự phân chia chính xác giữa miễn phí/trả phí
được nêu trong [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Dữ liệu của bạn luôn nằm trên máy của bạn

ClawMetry đọc các tệp phiên làm việc và log cục bộ. **Không có dữ liệu phiên làm việc nào rời khỏi
máy của bạn trừ khi bạn chạy `clawmetry connect`** — không có prompt, phản hồi, tham số công cụ, nội dung
tệp hay dòng log nào cả. Khi bạn kết nối, bản chụp nhanh (snapshot) sẽ được mã hóa đầu-cuối
bằng một khóa không bao giờ rời khỏi máy của bạn, và được giải mã ngay trong trình duyệt của bạn. Nếu một
node không có khóa, việc tải lên sẽ bị bỏ qua thay vì được gửi đi ở dạng không mã hóa, và không có
phản hồi nào từ máy chủ có thể tắt đi cơ chế đó.

Có hai thứ chạy sẵn theo mặc định trước khi bạn kết nối, cả hai đều có thể tắt và không mang theo
dữ liệu phiên làm việc nào: một tín hiệu ping cài đặt ẩn danh và một lượt kiểm tra phiên bản so với
PyPI. Một bản cài đặt mặc định cũng tra cứu địa chỉ IP công khai của bạn một lần để hiển thị dòng
banner khởi động. Mọi đích đến, những gì nó mang theo và cách tắt nó đều được liệt kê trong
[docs/EGRESS.md](docs/EGRESS.md); các bản cài đặt tự lưu trữ, được định tuyến lại, và cách ly khỏi
mạng (air-gapped) sẽ không thực hiện bất kỳ lệnh gọi ra ngoài tùy ý nào cả.

Việc giải mã diễn ra ngay trong trình duyệt của bạn, bằng mã nguồn mà chúng tôi cung cấp cho bạn. Điều đó
từng chỉ là một lời hứa; giờ đây nó là điều bạn có thể kiểm chứng. Mọi dòng mã chạm vào khóa của bạn
đều nằm trong một tệp dễ đọc duy nhất, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
được đóng gói bên trong wheel và phục vụ nguyên văn, được ghim bằng một hash Subresource
Integrity. Để xác nhận trình duyệt đang chạy đúng những gì chúng tôi đã công bố:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Điều mà việc này không chứng minh được: chúng tôi phục vụ trang tải tệp đó, nên chúng tôi vẫn có thể
phục vụ một trang khác. Các hash toàn vẹn (integrity hash) bảo vệ bạn khỏi một CDN bị xâm phạm,
chứ không phải khỏi chính nhà cung cấp dịch vụ. Điều bạn đạt được là bất kỳ sự thay thế nào cũng phải
là có chủ đích, hiển thị rõ trong mã nguồn trang, và khác với một artifact trên PyPI mà bất kỳ ai
cũng có thể tải về. Việc tự lưu trữ hoặc chỉ dùng cục bộ sẽ loại bỏ hoàn toàn sự phụ thuộc này.

## Cài đặt

```bash
pip install clawmetry     # sau đó: clawmetry
```

Hoặc dùng lệnh một dòng: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Cần Python 3.8+ trên macOS, Linux hoặc Windows, và ít nhất một runtime agent trên
cùng một máy. Hướng dẫn Docker: [docs/DOCKER.md](docs/DOCKER.md).

Hoặc để agent tự thiết lập giúp bạn. Kỹ năng [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
dạy cho Claude Code, Codex, Cursor, Gemini CLI, Copilot hoặc OpenCode cách
cài đặt ClawMetry, báo cáo những gì các agent trên máy đang làm và đang chi tiêu,
dừng một phiên làm việc theo yêu cầu, và giữ lại các lệnh gọi công cụ rủi ro để chờ phê duyệt:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Tài liệu

| | |
|---|---|
| [Khả năng tương thích runtime](docs/compatibility.md) | Mỗi adapter đọc được gì, và cách thêm một runtime |
| [Tràn ngữ cảnh](docs/CONTEXT_BLOWOUT.md) | Cửa sổ theo từng nhà cung cấp, nén so với tràn, mức độ bao phủ theo từng runtime |
| [Chi phí phát sinh (Overhead)](docs/OVERHEAD.md) | Chi phí của việc đo lường, đã được đo đạc, kèm bộ khai thác để tái tạo lại |
| [Quyền lợi (Entitlements)](docs/ENTITLEMENTS.md) | Miễn phí so với trả phí, ma trận các gói, CLI giấy phép |
| [Phê duyệt & chính sách](docs/APPROVALS.md) | Chặn trước khi thực thi, chấm điểm rủi ro, phê duyệt qua điện thoại |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Xuất trace ra bất kỳ đâu, tiếp nhận OTLP từ bất kỳ nguồn nào |
| [Mang theo agent của riêng bạn](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain từ đầu đến cuối, kèm ví dụ có thể chạy được |
| [Theo dõi SDK](docs/SDK_TRACKING.md) | Quy kết chi phí cho các agent bạn tự xây dựng |
| [Kênh trò chuyện](docs/CHANNELS.md) | Các adapter trò chuyện được hiển thị trong Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Các thiết lập NVIDIA NemoClaw trong môi trường cách ly (sandbox) |
| [Docker](docs/DOCKER.md) | Image, compose, gắn kết volume |
| [Kiến trúc](ARCHITECTURE.md) · [Phát triển](docs/DEVELOPMENT.md) | Cách nó hoạt động bên trong; chạy từ mã nguồn |
| [Đo lường (Telemetry)](docs/TELEMETRY.md) | Các tín hiệu ping cài đặt và mở ứng dụng desktop ẩn danh, và cách tắt chúng |

## Ảnh chụp màn hình

Mỗi con số dưới đây đều đến từ một máy thật, chỉ đọc, không có dữ liệu nào được gieo sẵn.

**Nó cho bạn biết khi nào có điều gì đó sai, chứ không chỉ những gì đã xảy ra.**
Hai banner cảnh báo bất thường ở phía trên: chi tiêu đang chạy gấp 7 lần mức trung bình hàng ngày, và một
đợt đột biến chi phí gấp 4,2 lần. Bên dưới đó, 324 trong số 667 phiên gần đây mang
tín hiệu lãng phí, được phân loại theo nguyên nhân.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Nó cho bạn thấy tiền đã đi đâu, trong mọi khung thời gian.**
$252,47 hôm nay, $513,15 tuần này, $1.312,92 tháng này, mỗi con số kèm theo số token
đứng sau nó và gói đăng ký của bạn đã bao trả bao nhiêu trong số đó. Bên dưới đó, khoảng
$1.128/tháng được liệt kê là có thể thu hồi được và $17.256/tháng đã tiết kiệm được nhờ
tái sử dụng bộ nhớ đệm (cache).

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Nó vẽ ra cách một tin nhắn trở thành một câu trả lời.**
Sơ đồ luồng trực tiếp: bạn, kênh mà tin nhắn đến, gateway, mô hình
đang trả lời ngay lúc này, và mọi công cụ mà nó đã sử dụng. Các nút sáng lên khi công việc
di chuyển qua chúng.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Mọi agent trên máy, trong một bảng duy nhất.**
Nó chạy gì, tốn bao nhiêu chi phí trong 24 giờ qua và trong suốt vòng đời của nó, khi
nào nó được thấy lần cuối, ai sở hữu nó, và liệu có gói đăng ký nào đang chi trả hóa đơn
hay không. 14 agent ở đây, 3 phiên đang hoạt động, 13 phiên đang yên lặng.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Nó cho thấy thời gian và tiền bạc của một lượt đã đi đâu, công cụ này đến công cụ khác.**
Một lượt của một phiên làm việc thật: 11 công cụ trong 11,2 phút với giá $1,16. Mỗi
lệnh gọi Bash và lệnh gọi mô hình đều có thanh riêng của nó trên dòng thời gian, nhờ đó lệnh chạy
trong 4,1 phút và lệnh chạy trong 226ms được phân biệt rõ ràng chỉ bằng một cái liếc mắt.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Nó chấm điểm chất lượng công việc, chứ không chỉ chi tiêu.**
Một điểm A trong tuần này: 54 tác vụ hoàn thành gọn gàng, 2 tác vụ gập ghềnh tốn $48,57, và các
lượt chạy có quá ít hoạt động để đánh giá thì bị loại khỏi việc chấm điểm thay vì
bị tính là thành công. Mỗi lượt chạy gập ghềnh đều liên kết đến trace của nó.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Nó cho thấy tại sao cửa sổ ngữ cảnh cứ liên tục đầy lên.**
715K trong tổng số cửa sổ 1M token trên lượt gần nhất, đỉnh 83,3%, 4 lần nén
đều được kích hoạt chủ động chứ không phải do bị tràn, cùng mức sử dụng của
mọi lượt phía sau nó.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Việc phát hiện chạy mà không cần bạn cấu hình bất cứ điều gì.**
Các bộ phát hiện tích hợp sẵn được bật ngay từ khi cài đặt: agent im lặng, luồng
đo lường bị ngắt, chi phí đột biến, bùng nổ token, lỗi tăng dần, đột biến lỗi, ngưỡng
ngân sách, chữ ký mối đe dọa khớp, phát hiện từ công cụ bảo mật, thay đổi tình trạng bảo mật.
Các quy tắc riêng của bạn là tùy chọn thêm vào bên trên.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Việc giữ lại một lệnh gọi rủi ro là tùy chọn, và mặc định ở trạng thái tắt.**
Xóa đệ quy, force push, sudo, thông tin bí mật, cài đặt gói và các lệnh gọi ra ngoài
đều có một quy tắc riêng mà bạn có thể bật. Cho đến khi bạn bật nó, ClawMetry chỉ theo dõi và
không thay đổi gì cả. Một khi được bật, các lệnh gọi khớp điều kiện sẽ chờ tại đây (hoặc trên
điện thoại của bạn) để được phê duyệt hoặc từ chối.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Nhiều hơn nữa, theo từng runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Ghi nhận

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
