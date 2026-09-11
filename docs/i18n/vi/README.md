<!-- i18n-src:12b97259721e -->
> Tiếng Việt translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Một agent có thể thực hiện hàng trăm lệnh gọi công cụ mà không đạt được tiến triển nào.** ClawMetry
đọc các tệp session mà các coding agent của bạn đã tự viết ra, và đưa dòng thời gian,
các lệnh gọi công cụ và bất kỳ dữ liệu token, chi phí nào mà runtime cung cấp vào một
giao diện duy nhất — để bạn có thể phân biệt một tiến trình dài đang hoạt động hiệu quả với một tiến trình đang bị kẹt.

Hoạt động với **31 runtime AI agent** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 27 runtime khác. Một dashboard cho toàn bộ đội agent của bạn. ([danh sách đầy đủ](SUPPORTED_RUNTIMES.txt), được tạo ra từ danh mục.)

> 🌐 **Đọc bằng ngôn ngữ khác:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [thêm →](docs/i18n/)

Một lệnh duy nhất. Không cần cấu hình. Tự động phát hiện mọi thứ.

```bash
pip install clawmetry && clawmetry
```

Mở tại **http://localhost:8900**. Không cần cấu hình: nó tìm ra các runtime agent
bạn đã có sẵn, đọc chúng ở chế độ chỉ đọc, và không thay đổi gì về cách chúng chạy.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Trước khi cài đặt

| | |
|---|---|
| **Nó làm gì** | Đọc các tệp session và log mà agent của bạn đã tự viết ra. Không cần SDK, không cần thay đổi code, không cần thêm instrumentation vào ứng dụng của bạn. |
| **Bạn thấy gì** | Dòng thời gian session, replay theo từng công cụ, phân tích token và chi phí, và các tín hiệu về đường đi (lặp vòng, lỗi lặp lại) — theo từng runtime. |
| **Cái gì miễn phí** | `pip install clawmetry` đọc được **OpenClaw, NVIDIA NemoClaw và Goose** không cần tài khoản, không cần key và không cần kết nối mạng. 27 runtime còn lại — Claude Code, Codex, Cursor và các runtime khác — được đọc bởi companion mã nguồn đóng `clawmetry-pro`, đi kèm với bản dùng thử 7 ngày hoặc một gói trả phí — xem [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) để biết cách phân chia chính xác. |
| **Cách bắt đầu** | `pip install clawmetry && clawmetry`, sau đó mở localhost:8900. Máy này chưa có agent nào? `clawmetry --sample` sẽ mở với ba session giả lập được đánh nhãn rõ ràng. |
| **Cái gì rời khỏi máy của bạn** | Không có dữ liệu session nào, trừ khi bạn chạy `clawmetry connect`. Có hai thứ chạy theo mặc định, cả hai đều có thể tắt và không mang theo nội dung session: một ping cài đặt ẩn danh và một kiểm tra phiên bản trên PyPI. Mọi điểm đến đều được kiểm kê trong [docs/EGRESS.md](docs/EGRESS.md), được xây dựng lại từ việc chụp lưu lượng mạng thực tế chứ không phải từ việc đọc comment trong code. |

Có hai giới hạn cần biết trước khi bạn đánh giá kết quả: các runtime cung cấp
dữ liệu rất khác nhau (một số không công bố chi phí nào cả — [bảng so sánh](docs/compatibility.md)
cho biết runtime nào, cụ thể), và việc quan sát một hành động không giống với việc có thể
chặn nó ([những kiểm soát nào là thật, theo từng runtime](docs/APPROVALS.md)).


## Hoạt động với 31 runtime agent

**Miễn phí trong ứng dụng mã nguồn mở:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Trong gói trả phí:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Mọi runtime đều nhận cùng một dashboard. Chạy nhiều runtime cùng lúc và bộ chuyển
đổi ở phần header sẽ đưa mọi tab về phạm vi của từng runtime đó.

Bạn tự xây agent riêng dựa trên một SDK thay vì dùng runtime có sẵn? Interceptor cũng theo dõi
các lệnh gọi LLM của nó. Xem [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Bạn nhận được gì

- **Session & bản ghi hội thoại**: mỗi agent đã làm gì, theo từng lượt, có thể replay lại
- **Chi phí & token**: theo từng runtime, model, session và ngày, có cờ báo bất thường
- **Flow**: sơ đồ trực tiếp về luồng tin nhắn đi qua các channel, model và công cụ
- **Brain**: luồng sự kiện suy luận và gọi công cụ ngay khi nó xảy ra
- **Context blowout**: mức sử dụng context window được tính theo từng nhà cung cấp, so sánh compaction với tràn buộc, cùng bản đồ theo từng runtime về những gì chúng ta *không* thấy được ([cách thực hiện](docs/CONTEXT_BLOWOUT.md))
- **Memory & skill**: các tệp và skill mà mỗi runtime thực sự đã tải
- **Health & log**: đĩa, bộ nhớ, tỷ lệ lỗi, rate limit, luồng log trực tiếp
- **Cảnh báo**: giới hạn ngân sách, đột biến lỗi, agent-offline, gửi tới Slack, Discord, PagerDuty, Telegram, Email
- **Approvals (Phê duyệt)**: tạm dừng các lệnh gọi công cụ có rủi ro *trước khi* chúng chạy và phê duyệt ngay từ điện thoại của bạn ([cách thực hiện](docs/APPROVALS.md))

## Context blowout, và chi phí của việc theo dõi

Hai câu hỏi đáng được trả lời trước khi bạn tin tưởng bất kỳ công cụ so sánh agent nào.

**Nó xử lý việc tràn context-window trên các runtime khác nhau như thế nào?**

Một tỷ lệ phần trăm sử dụng chỉ đáng tin cậy bằng đúng mẫu số mà nó dùng để chia. ClawMetry
định cỡ window theo từng nhà cung cấp từ [một bảng bạn có thể đọc và
gửi PR](clawmetry/context_windows.py), bao gồm Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama và GLM. Nó không đo cả 31
runtime bằng thước đo của một nhà cung cấp duy nhất. Điều này quan trọng: một lượt GPT-5 300K token
nếu tính theo mức 200K của Anthropic sẽ đọc là ">100%, đã tràn" trong khi thực ra nó chỉ ở mức 75% của
mức 400K của GPT-5. Cùng một thước đo đó lại che giấu một lượt DeepSeek 130K bị tràn thật
thành một mức 65% có vẻ an toàn.

Mỗi window đều đi kèm nguồn gốc của nó: `model_table`, `explicit_marker`,
`observed_floor`, hoặc một giá trị `default` trung thực khi chúng ta không biết model đó. Một
đồng hồ đo được xây dựng trên một sự đoán không bao giờ hiển thị với cùng độ tin cậy như một
đồng hồ được xây dựng trên việc tra cứu thực tế.

ClawMetry chỉ có thể thấy các sự kiện compaction trên một số runtime. Vì vậy
`GET /api/context-coverage` báo cáo, theo từng runtime, liệu một giá trị **0 có nghĩa là
"chạy sạch" hay là "chúng ta không thấy được"**. Một `0` mà thực chất có nghĩa là mù sẽ được nói rõ như vậy.
[Chi tiết đầy đủ](docs/CONTEXT_BLOWOUT.md)

**Việc thêm instrumentation tốn chi phí gì?**

| Đường dẫn | Thêm vào agent của bạn | Mặc định? |
|---|---|---|
| Tailing tệp session (cả 31 runtime) | **0**. Tiến trình riêng biệt, không có code ClawMetry nào trong agent của bạn | bật |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** cho mỗi lệnh gọi LLM, tức 0.009% của một lệnh gọi 5s | tắt |
| Pre-tool hook gate (cache đã warm) | **+44 ms** cho mỗi lệnh gọi công cụ bị gate, trên nền tảng interpreter là 36 ms | tắt |
| Enforcement proxy | **+9.7 ms** cho mỗi lệnh gọi LLM | tắt |

Chi phí trên máy chủ daemon: **2.762 sự kiện/giây** ingest, **710 byte/sự kiện** trên đĩa
(67.7 MB cho mỗi 100 nghìn sự kiện), và **khoảng 12% của một core** duy trì trên một
máy cài đặt đang bận. Con số cuối cùng đó vượt ngân sách 5-10% mà chúng ta tự đặt ra, vì vậy nó được
công bố như một lỗi cần khắc phục thay vì bị bỏ qua khỏi trang này.

Đo trên Apple M2 Pro bằng `benchmarks/overhead.py`. Bộ đo này chạy
mỗi điều kiện trong một tiến trình riêng biệt, đảo thứ tự của chúng, và **từ chối
in ra một số khi các vòng đo không đồng ý về dấu của nó**. Chạy nó trên máy của bạn
trong một phút:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Mọi đường dẫn đều được đo, bao gồm cả hook gate và enforcement proxy,
và bộ đo chạy trên Linux, macOS và Windows trong CI. Có hai kết quả đáng biết:
proxy tốn khoảng gấp bảy lần chi phí trên Windows so với trên Linux, và
daemon hiện đang duy trì khoảng 12% của một core, vượt ngân sách 5-10% mà chúng ta tự đặt ra. Dữ liệu JSON thô, phương pháp đo, và những gì vẫn chưa được đo đều có trong
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Giá cả

| Gói | Bao gồm những gì | Giá |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard đầy đủ, chỉ chạy local | $0 |
| **Starter** | Mọi runtime khác ở trên, chế độ xem fleet, đồng bộ cloud | $9 mỗi node / tháng |
| **Pro** | Starter + kiểm soát và đánh giá: approvals, chính sách rủi ro công cụ, evals, phát hiện bất thường, cost optimizer, xuất OTel, tamper-evident audit log | $19 mỗi node / tháng |

Các gói trả theo năm, Enterprise và các con số hiện tại được cập nhật tại
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Các license key self-hosted hoạt động
không cần cloud (`clawmetry license`). Cách phân chia miễn phí/trả phí chính xác nằm
trong [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Dữ liệu của bạn ở lại trên máy của bạn

ClawMetry đọc các tệp session và log local. **Không có dữ liệu session nào rời khỏi máy của bạn
trừ khi bạn chạy `clawmetry connect`** — không prompt, không phản hồi, không tham số công cụ, không nội dung
tệp hay dòng log. Khi bạn kết nối, snapshot được mã hóa đầu cuối (end-to-end)
bằng một key không bao giờ rời khỏi máy của bạn, và được giải mã ngay trong trình duyệt của bạn. Nếu một
node không có key, việc upload sẽ bị bỏ qua thay vì được gửi ở dạng không mã hóa, và không
phản hồi nào từ server có thể tắt điều đó.

Có hai thứ chạy theo mặc định trước khi bạn kết nối, cả hai đều có thể tắt và không
mang theo dữ liệu session: một ping cài đặt ẩn danh và một kiểm tra phiên bản so với
PyPI. Một lần cài đặt mặc định cũng tra cứu địa chỉ IP công khai của bạn một lần cho dòng banner khởi động.
Mọi điểm đến, những gì nó mang theo và cách tắt nó đều được liệt kê trong
[docs/EGRESS.md](docs/EGRESS.md); các bản cài self-hosted, được định tuyến lại và air-gapped
không thực hiện bất kỳ lệnh gọi ra ngoài tùy ý nào cả.

Việc giải mã diễn ra trong trình duyệt của bạn, bằng code mà chúng tôi phục vụ cho bạn. Đó từng
là một lời hứa; giờ đây nó là điều bạn có thể kiểm chứng. Mọi dòng code chạm vào key của bạn
nằm trong một tệp có thể đọc được duy nhất, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
được đóng gói kèm trong wheel và phục vụ nguyên bản, được pin bằng một hash Subresource
Integrity. Để xác nhận trình duyệt chạy đúng cái chúng tôi đã công bố:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Điều đó không chứng minh được: chúng tôi phục vụ trang tải tệp này, vì vậy chúng tôi có thể
phục vụ một trang khác. Các hash integrity bảo vệ bạn khỏi một CDN bị xâm nhập,
không phải khỏi nhà cung cấp. Điều bạn đạt được là bất kỳ sự thay thế nào cũng phải
có chủ đích, hiển thị trong mã nguồn trang, và khác với một artifact trên PyPI
mà bất kỳ ai cũng có thể lấy về. Tự host hoặc chỉ chạy local hoàn toàn loại bỏ
sự phụ thuộc này.

## Cài đặt

```bash
pip install clawmetry     # sau đó: clawmetry
```

Hoặc dùng lệnh một dòng: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Cần Python 3.8+ trên macOS, Linux hoặc Windows, và ít nhất một runtime agent trên
cùng máy. Hướng dẫn Docker: [docs/DOCKER.md](docs/DOCKER.md).

Hoặc để agent tự thiết lập cho bạn. Skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
dạy cho Claude Code, Codex, Cursor, Gemini CLI, Copilot hoặc OpenCode cách
cài đặt ClawMetry, báo cáo những gì các agent trên máy đang làm và đang chi tiêu,
dừng một session theo yêu cầu, và giữ lại các lệnh gọi công cụ rủi ro để chờ phê duyệt:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Tài liệu

| | |
|---|---|
| [Tương thích runtime](docs/compatibility.md) | Mỗi adapter đọc được gì, và cách thêm một runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Window theo từng nhà cung cấp, compaction so với overflow, độ phủ theo từng runtime |
| [Overhead](docs/OVERHEAD.md) | Chi phí của instrumentation, đã được đo đạc, cùng bộ công cụ để tái tạo lại |
| [Entitlements](docs/ENTITLEMENTS.md) | Miễn phí so với trả phí, bảng phân hạng, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Gate trước khi thực thi, tính điểm rủi ro, phê duyệt qua điện thoại |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Xuất trace tới bất cứ đâu, ingest OTLP từ bất cứ đâu |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain từ đầu đến cuối, kèm ví dụ có thể chạy được |
| [SDK tracking](docs/SDK_TRACKING.md) | Quy về chi phí cho các agent bạn tự xây dựng |
| [Chat channels](docs/CHANNELS.md) | Các adapter chat hiển thị trong Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Các thiết lập NVIDIA NemoClaw trong sandbox |
| [Docker](docs/DOCKER.md) | Image, compose, gắn volume |
| [Kiến trúc](ARCHITECTURE.md) · [Phát triển](docs/DEVELOPMENT.md) | Cách nó hoạt động bên trong; chạy từ source |
| [Telemetry](docs/TELEMETRY.md) | Ping cài đặt và ping mở desktop ẩn danh, và cách tắt chúng |

## Ảnh chụp màn hình

Mọi số liệu dưới đây đều từ một máy thật, chỉ đọc, không có gì được gieo sẵn.

**Nó cho bạn biết khi có gì đó sai, không chỉ là điều gì đã xảy ra.**
Hai banner cảnh báo bất thường ở phía trên: chi tiêu đang chạy gấp 7 lần mức trung bình hàng ngày, và một
đợt đột biến chi phí 4.2 lần. Bên dưới, 324 trong 667 session gần đây mang
một tín hiệu lãng phí, được phân loại theo nguyên nhân.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Nó cho bạn thấy tiền đã đi đâu, trong mọi khoảng thời gian.**
$252.47 hôm nay, $513.15 tuần này, $1.312.92 tháng này, mỗi con số kèm theo số token
đứng sau nó và mức nào trong đó đã được subscription của bạn chi trả. Bên dưới đó,
khoảng $1.128/tháng được phân loại là có thể khôi phục và $17.256/tháng đã được tiết kiệm
nhờ việc dùng lại cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Nó vẽ ra cách một tin nhắn trở thành một câu trả lời.**
Sơ đồ flow trực tiếp: bạn, channel mà tin nhắn đến, gateway, model
đang trả lời ngay lúc này, và mọi công cụ nó đã gọi tới. Các node sáng lên khi công việc
di chuyển qua chúng.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Mọi agent trên máy, trong một bảng duy nhất.**
Nó chạy gì, tốn bao nhiêu trong 24 giờ qua và trong toàn bộ thời gian hoạt động, khi
nào nó được thấy lần cuối, ai sở hữu nó, và liệu một subscription có đang chi trả cho
hóa đơn hay không. 14 agent ở đây, 3 session đang hoạt động, 13 đang im lặng.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Nó cho thấy thời gian và tiền bạc của một lượt đã đi đâu, theo từng công cụ.**
Một lượt của một session thật: 11 công cụ trong 11.2 phút với $1.16. Mỗi
lệnh gọi Bash và lệnh gọi model đều có thanh riêng của nó trên dòng thời gian, để lệnh
chạy trong 4.1 phút và lệnh chạy trong 226ms được phân biệt ngay từ cái nhìn đầu tiên.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Nó đánh giá chất lượng công việc, không chỉ chi tiêu.**
Một hạng A trong tuần này: 54 nhiệm vụ hoàn thành sạch sẽ, 2 nhiệm vụ gặp trục trặc tốn
$48.57, và các lượt chạy có quá ít hoạt động để đánh giá được loại ra khỏi điểm số
thay vì bị tính là thành công. Mỗi lượt chạy gặp trục trặc đều có link tới trace của nó.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Nó cho thấy tại sao context window liên tục bị đầy.**
715K trong một window 1M token ở lượt gần nhất, một mức đỉnh 83.3%, 4 lần compaction
tất cả đều kích hoạt chủ động thay vì do bị tràn, và mức sử dụng của
mọi lượt trước đó.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Việc phát hiện chạy mà bạn không cần cấu hình gì cả.**
Các detector tích hợp sẵn được bật ngay từ khi cài đặt: agent im lặng, luồng telemetry
bị dừng, đột biến chi phí, đột biến token, lỗi tăng dần, đột biến lỗi, ngưỡng
ngân sách, khớp dấu hiệu đe dọa, phát hiện từ công cụ bảo mật, thay đổi tình trạng bảo mật.
Các quy tắc riêng của bạn là tùy chọn thêm vào.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Việc giữ một lệnh gọi rủi ro là tùy chọn, và mặc định tắt.**
Xóa đệ quy, force push, sudo, secret, cài đặt package và các lệnh gọi ra ngoài đều
có một quy tắc bạn có thể bật. Cho đến khi bạn bật, ClawMetry chỉ quan sát và
không thay đổi gì. Khi một quy tắc được bật, các lệnh gọi khớp sẽ chờ ở đây (hoặc trên điện thoại của bạn)
để được phê duyệt hoặc từ chối.

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
