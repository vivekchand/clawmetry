<!-- i18n-src:12b97259721e -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**一個代理程式可以呼叫上百次工具卻毫無進展。** ClawMetry
讀取你的編碼代理程式已經在寫入的 session 檔案，並將時間軸、
工具呼叫，以及執行環境所公開的任何 token 與成本資料整合到單一
畫面中，讓你能分辨出正在順利運作的長時間執行與卡住的執行。

支援 **31 種 AI 代理程式執行環境**：Claude Code、OpenAI Codex、Hermes、OpenClaw 以及另外 27 種。單一儀表板管理你整個代理程式艦隊。（[完整清單](SUPPORTED_RUNTIMES.txt)，由目錄自動產生。）

> 🌐 **語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測所有東西。

```bash
pip install clawmetry && clawmetry
```

會在 **http://localhost:8900** 開啟。零設定：它會找到你機器上已有的
代理程式執行環境，以唯讀方式讀取，不會改變它們的任何執行方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安裝前你該知道的事

| | |
|---|---|
| **它做什麼** | 讀取你的代理程式已經在寫入的 session 檔案與日誌。沒有 SDK、不需要改程式碼、不會在你的應用程式中埋入任何檢測程式碼。 |
| **你會看到什麼** | Session 時間軸、逐工具重播、token 與成本細目，以及軌跡訊號（循環、重複失敗），每個執行環境都有。 |
| **哪些是免費的** | `pip install clawmetry` 可讀取 **OpenClaw、NVIDIA NemoClaw 與 Goose**，不需要帳號、金鑰或任何網路連線。其餘 27 種——Claude Code、Codex、Cursor 及其他——則由閉源的 `clawmetry-pro` 附加元件讀取，隨 7 天試用或方案一起提供——確切劃分請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何開始** | `pip install clawmetry && clawmetry`，然後開啟 localhost:8900。這台機器上還沒有代理程式？`clawmetry --sample` 會以三個標示清楚的合成 session 開啟。 |
| **哪些資料會離開你的機器** | 除非你執行 `clawmetry connect`，否則不會有任何 session 資料離開。有兩件事預設會執行，皆可選擇退出，且都不包含 session 內容：匿名安裝回報與 PyPI 版本檢查。所有目的地都列在 [docs/EGRESS.md](docs/EGRESS.md) 中，該文件是根據封包擷取重建，而非僅憑程式碼註解。 |

在你評判輸出結果之前，有兩個值得了解的限制：不同執行環境公開的資料
差異很大（有些完全不公開成本——詳見[相容性矩陣](docs/compatibility.md)
說明每個執行環境的情況），而觀察一個動作並不等同於能夠阻止它
（[各執行環境實際可用的控制項](docs/APPROVALS.md)）。


## 支援 31 種代理程式執行環境

**開源應用程式中免費：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案中提供：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每個執行環境都使用相同的儀表板。同時執行多個，
上方的切換器會將每個分頁重新對應到其中一個環境。

自己用 SDK 打造了代理程式？攔截器同樣能追蹤它的 LLM 呼叫。
詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你會得到什麼

- **Sessions 與逐字稿**：每個代理程式做了什麼，逐輪呈現，並可重播
- **成本與 token**：依執行環境、模型、session 及日期呈現，並附異常標記
- **Flow**：訊息在頻道、模型與工具之間流動的即時圖表
- **Brain**：推理與工具呼叫事件即時串流
- **Context 爆量**：依供應商調整大小的視窗使用率、壓縮 vs 被迫溢出，
  以及每個執行環境無法看見範圍的地圖（[如何做到](docs/CONTEXT_BLOWOUT.md)）
- **記憶與技能**：每個執行環境實際載入的檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、代理程式離線，可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **核准**：在有風險的工具呼叫執行*之前*先暫停，並可從手機核准（[如何做到](docs/APPROVALS.md)）

## Context 爆量，以及監控的成本

在你信任任何代理程式比較工具之前，有兩個問題值得先弄清楚。

**它如何處理跨執行環境的 context 視窗爆量？**

使用率百分比的可信度，取決於它拿來當分母的數字是否誠實。ClawMetry
會依供應商，從[一張你可以閱讀並提交 PR 的表格](clawmetry/context_windows.py)
決定視窗大小，涵蓋 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 與 GLM。它不會用某一家供應商的尺規
去衡量全部 31 種執行環境。這點很重要：一個 300K 的 GPT-5 回合，
如果拿 Anthropic 的 200K 來評分，會顯示「>100%，爆量」，但實際上
只是 GPT-5 的 400K 視窗中的 75%。同一把尺規也會把一個實際上已經
溢出的 130K DeepSeek 回合，隱藏成看似安全的 65%。

每個視窗都附帶其來源標記：`model_table`、`explicit_marker`、
`observed_floor`，或是在我們不知道模型時誠實標示為 `default`。
建立在猜測之上的量表，永遠不該與建立在查表之上的量表擁有同等的權威性。

ClawMetry 只能在部分執行環境上看到壓縮事件。因此
`GET /api/context-coverage` 會針對每個執行環境回報，
「顯示 0」到底代表**「乾淨執行」還是「我們看不到」**。
真正意義是「看不到」的 `0`，會如實標示出來。
[完整說明](docs/CONTEXT_BLOWOUT.md)

**這套檢測工具的成本是多少？**

| 路徑 | 對你的代理程式增加的成本 | 預設開啟？ |
|---|---|---|
| Session 檔案追蹤（全部 31 種執行環境） | **0**。獨立處理程序，代理程式中沒有任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 呼叫 **+0.44 毫秒**，相當於 5 秒呼叫的 0.009% | 關閉 |
| 工具執行前掛鉤（暖快取） | 每次受管控的工具呼叫 **+44 毫秒**，超出 36 毫秒的直譯器底線 | 關閉 |
| 強制執行代理 | 每次 LLM 呼叫 **+9.7 毫秒** | 關閉 |

Daemon 主機成本：擷取速度 **每秒 2,762 個事件**，每個事件在磁碟上佔用
**710 位元組**（每 10 萬個事件 67.7 MB），繁忙的安裝環境下持續
佔用**約一個核心的 12%**。最後這個數字超出了我們自訂的 5-10% 預算，
因此我們把它當成一個要追蹤修正的 bug 公開出來，而不是隱瞞。

在 Apple M2 Pro 上使用 `benchmarks/overhead.py` 測得。測試工具會將
每種情境放在獨立的處理程序中執行、交替其順序，並且**當多輪結果的
正負號不一致時拒絕印出數字**。你可以在自己的機器上花一分鐘執行它：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過測量，包含掛鉤閘門與強制執行代理，
測試工具在 CI 中於 Linux、macOS 與 Windows 上執行。有兩個結果值得
留意：這個代理在 Windows 上的成本大約是 Linux 上的七倍，而 daemon
目前持續佔用約一個核心的 12%，超出我們自訂的 5-10% 預算。原始
JSON 資料、方法，以及目前尚未測量的部分，都記錄在
[docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 價格方案

| 方案 | 涵蓋內容 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose，完整儀表板，僅限本機 | $0 |
| **Starter** | 上述以外的所有其他執行環境、艦隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 控制與評估：核准機制、工具風險政策、評估、異常偵測、成本優化器、OTel 匯出、防竄改稽核紀錄 | 每節點每月 $19 |

年繳方案、企業版與目前的最新價格請見
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰
不需要雲端服務即可使用（`clawmetry license`）。免費與付費的確切劃分
請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你自己的機器上

ClawMetry 讀取本機的 session 檔案與日誌。**除非你執行
`clawmetry connect`，否則不會有任何 session 資料離開你的機器**——
不含提示詞、回覆、工具參數、檔案內容或日誌行。當你確實連線時，
快照會以端對端加密方式傳輸，金鑰永遠不會離開你的機器，並在你的
瀏覽器中解密。如果某個節點沒有金鑰，上傳會被跳過，而不是以明文
傳送，且沒有任何伺服器回應可以關閉這項保護。

連線之前，預設有兩件事會執行，皆可選擇退出，且都不包含 session
資料：匿名安裝回報與針對 PyPI 的版本檢查。預設安裝也會查詢一次
你的公開 IP，用於啟動橫幅的其中一行。每個目的地、它攜帶的內容，
以及如何關閉，都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；自架、
重新指向或氣隙（air-gapped）安裝完全不會發出任何可選的外部呼叫。

解密發生在你的瀏覽器中，使用我們提供給你的程式碼。這曾經只是
一項承諾；現在你可以自行查核。所有觸及你金鑰的程式碼都放在單一
可讀檔案 [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)
中，隨 wheel 一起發布並原封不動地提供，並以子資源完整性
（Subresource Integrity）雜湊值釘選。若要確認瀏覽器執行的是我們
發布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這個做法無法證明的是：我們提供載入該檔案的頁面，所以我們理論上
可以提供不同的頁面。完整性雜湊值能保護你免受 CDN 遭入侵的影響，
但無法防範供應商本身的行為。你得到的保障是，任何替換都必須是
刻意的、在頁面原始碼中可見，且與任何人都能從 PyPI 抓取的成品不同。
自架或維持僅限本機運作，可以完全消除這種依賴。

## 安裝

```bash
pip install clawmetry     # 然後執行：clawmetry
```

或使用一行指令安裝：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+，以及同一台機器上至少
一種代理程式執行環境。Docker 安裝說明：[docs/DOCKER.md](docs/DOCKER.md)。

或者讓代理程式幫你設定。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能可以教會 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode
安裝 ClawMetry、回報機器上各代理程式正在做什麼與花費多少、依要求
停止某個 session，並暫停有風險的工具呼叫以等待核准：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個轉接器讀取哪些內容，以及如何新增執行環境 |
| [Context 爆量](docs/CONTEXT_BLOWOUT.md) | 依供應商劃分的視窗、壓縮 vs 溢出、每個執行環境的涵蓋範圍 |
| [額外開銷](docs/OVERHEAD.md) | 檢測工具實際測量出的成本，以及可重現測試的工具 |
| [權限方案](docs/ENTITLEMENTS.md) | 免費與付費比較、方案等級矩陣、授權金鑰 CLI |
| [核准與政策](docs/APPROVALS.md) | 執行前把關、風險評分、手機核准 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤資料匯出至任何地方，從任何來源擷取 OTLP |
| [自帶代理程式](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 端到端範例，附可執行的程式碼 |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為自行打造的代理程式做成本歸屬 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、磁碟區掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理；從原始碼執行 |
| [遙測](docs/TELEMETRY.md) | 匿名安裝與桌面開啟回報，以及如何關閉它們 |

## 螢幕截圖

以下每個數字都來自一台真實機器，全程唯讀，沒有任何預先植入的資料。

**它會告訴你哪裡出了問題，而不只是發生了什麼事。**
頂部有兩個異常橫幅：支出是日均值的 7 倍，以及一次 4.2 倍的成本
激增。下方則是最近 667 個 session 中有 324 個帶有浪費訊號，並按
原因逐項列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它會顯示每一個時間窗口裡錢花到哪去了。**
今天 $252.47、本週 $513.15、本月 $1,312.92，各自附上背後的 token
數量，以及訂閱方案已涵蓋的比例。下方則列出約每月 $1,128 可回收的
項目，以及快取重複使用已經節省的每月 $17,256。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它會描繪一則訊息如何變成一個答案。**
即時流程圖：你、訊息抵達的頻道、閘道、目前正在回答的模型，以及
它呼叫過的每個工具。節點會隨著工作的流動而亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每個代理程式，全都在一張表格裡。**
它在執行什麼、過去 24 小時與整個生命週期的成本、上次出現的時間、
歸屬於誰，以及是否有訂閱方案涵蓋這筆費用。這裡有 14 個代理程式，
3 個 session 正在運作，13 個閒置中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它會逐一工具地顯示一個回合的時間與金錢花在哪裡。**
一次真實 session 的其中一個回合：11 個工具、11.2 分鐘、花費 $1.16。
每次 Bash 呼叫與模型呼叫都在時間軸上有自己的橫條，因此執行了
4.1 分鐘的指令與只執行了 226 毫秒的指令能夠一眼分辨。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它評判的是工作成果，而不只是花費。**
本週得到 A 級：54 項任務乾淨完成，2 項有問題的任務花費 $48.57，
而活動量太少、不足以評判的執行則被排除在評分之外，而不是被計為
成功。每個有問題的執行都連結到它的追蹤紀錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它會顯示 context 視窗為什麼會不斷被填滿。**
在最新回合中，1M token 視窗用掉了 715K，尖峰達 83.3%，發生了 4 次
壓縮，且全部都是主動觸發、而非因溢出而觸發，並附上其之前每個
回合的使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能不需要你做任何設定即可運作。**
內建偵測器從安裝時就已啟用：代理程式沉寂、遙測資料流中斷、成本
激增、token 突增、錯誤攀升、錯誤激增、預算門檻、符合威脅特徵、
安全工具發現問題、安全態勢變化。你也可以額外加上自己的規則。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**攔截風險呼叫是選擇性開啟的功能，出廠時是關閉的。**
遞迴刪除、強制推送、sudo、機密資訊、套件安裝以及對外呼叫，
每一項都有可各自開啟的規則。在你開啟之前，ClawMetry 只會觀察，
不會改變任何東西。一旦開啟，符合條件的呼叫會在這裡（或你的手機
上）等待核准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多依執行環境分類的截圖：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 獲獎肯定

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star 歷史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 授權條款

MIT · 由 [@vivekchand](https://github.com/vivekchand) 打造 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
