<!-- i18n-src:61beb8393e2f -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**一個代理程式可以進行上百次工具呼叫卻毫無進展。** ClawMetry
讀取你的編碼代理程式已經在寫入的工作階段檔案，並將時間軸、
工具呼叫以及執行環境公開的任何 token 與成本資料整合到單一
視圖中——讓你能夠分辨一次正在正常運作的長時間執行，和一次卡住的執行。

支援 **30 種 AI 代理執行環境**——Claude Code、OpenAI Codex、Hermes、OpenClaw 及其他 26 種。一個儀表板管理你整個代理艦隊。（[完整清單](SUPPORTED_RUNTIMES.txt)，由目錄自動產生。）

> 🌐 **以其他語言閱讀：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟。零設定：它會找到你機器上已有的代理執行環境，
以唯讀方式讀取它們，且不會改變它們的任何運作方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安裝前須知

| | |
|---|---|
| **它做什麼** | 讀取你的代理程式已經在寫入的工作階段檔案與日誌。無需 SDK、無需修改程式碼、不會在你的應用程式中植入任何檢測代碼。 |
| **你能看到什麼** | 工作階段時間軸、逐工具重播、token 與成本分析，以及軌跡訊號（迴圈、重複失敗）——依執行環境分類。 |
| **哪些是免費的** | `pip install clawmetry` 可讀取 **OpenClaw、NVIDIA NemoClaw 與 Goose**，不需要帳號、金鑰或任何網路連線。其他 27 種——Claude Code、Codex、Cursor 及其餘——則由閉源的 `clawmetry-pro` 附加元件讀取，這會隨 7 天試用或方案一起提供——確切的區分請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何開始** | `pip install clawmetry && clawmetry`，然後開啟 localhost:8900。這台機器上還沒有任何代理程式？`clawmetry --sample` 會以三個標示清楚的合成工作階段開啟。 |
| **哪些資料會離開你的機器** | 除非你執行 `clawmetry connect`，否則沒有任何工作階段資料會離開。預設會執行兩件事，兩者皆可選擇退出，且都不攜帶工作階段內容：一個匿名安裝回報和一個 PyPI 版本檢查。每個目的地都記錄在 [docs/EGRESS.md](docs/EGRESS.md) 中，該文件是根據網路封包擷取重建，而非僅憑閱讀程式碼註解。 |

在你評判輸出結果之前，有兩個限制值得了解：不同執行環境公開的資料差異很大
（有些完全不公布成本——[相容性矩陣](docs/compatibility.md)會列出每個執行環境的情況），
而且觀察一個動作和能夠阻止它並不相同（[各執行環境的實際控制能力](docs/APPROVALS.md)）。


## 支援 30 種代理執行環境

**開源應用中免費：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每個執行環境都採用相同的儀表板。同時執行多個執行環境時，
頂端的切換器會將每個分頁重新對應到其中一個環境。

用 SDK 打造了自己的代理程式？攔截器（interceptor）也能追蹤它的 LLM 呼叫。
請見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能獲得什麼

- **工作階段與逐字稿**：每個代理程式逐輪做了什麼，並可重播
- **成本與 token**：依執行環境、模型、工作階段與日期劃分，並附異常標記
- **流程（Flow）**：訊息在頻道、模型與工具之間流動的即時圖表
- **大腦（Brain）**：即時發生的推理與工具呼叫事件串流
- **情境爆量（Context blowout）**：依供應商調整大小的視窗使用率、壓縮 vs 強制溢位，以及每個執行環境「我們看不到的部分」地圖（[原理](docs/CONTEXT_BLOWOUT.md)）
- **記憶與技能**：每個執行環境實際載入的檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、代理離線，可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **審批**：在有風險的工具呼叫*執行前*先暫停，並可在手機上批准（[原理](docs/APPROVALS.md)）

## 情境爆量，以及監控的成本

在你信任任何代理比較工具之前，有兩個問題值得先弄清楚。

**它如何處理跨執行環境的情境視窗爆量？**

使用率百分比的可信度，取決於它所除以的分母是否誠實。ClawMetry
依供應商從[一份你可以閱讀並提交 PR 的表格](clawmetry/context_windows.py)
來決定視窗大小，涵蓋 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 與 GLM。它不會用單一廠商的尺標
去衡量全部 30 種執行環境。這很重要：一個 30 萬 token 的 GPT-5 回合
若拿 Anthropic 的 20 萬上限來衡量，會顯示「>100%，已爆量」，
但實際上只是 GPT-5 40 萬上限的 75%。同樣的尺標也會把一個真正
溢位的 13 萬 token DeepSeek 回合，誤判成看似安全的 65%。

每個視窗都會附帶其來源：`model_table`、`explicit_marker`、
`observed_floor`，或在我們不知道模型時誠實地標示為 `default`。
基於猜測建構的量表，永遠不該以查表所得結果同等的權威性呈現。

ClawMetry 只能在部分執行環境上看到壓縮（compaction）事件。因此
`GET /api/context-coverage` 會針對每個執行環境回報，**零值究竟代表
「乾淨執行完畢」還是「我們看不到」**。若某個 `0` 其實代表看不到，它會如實說明。
[完整說明](docs/CONTEXT_BLOWOUT.md)

**這套檢測本身的成本是多少？**

| 路徑 | 對你的代理程式增加的成本 | 預設開啟？ |
|---|---|---|
| 工作階段檔案追蹤（全部 30 種執行環境） | **0**。獨立行程，你的代理程式中不含任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 呼叫 **+0.44 毫秒**，相當於 5 秒呼叫的 0.009% | 關閉 |
| 工具前置攔截閘道（暖快取） | 每次受管制的工具呼叫 **+44 毫秒**，超出 36 毫秒的直譯器底線 | 關閉 |
| 強制執行代理（proxy） | 每次 LLM 呼叫 **+9.7 毫秒** | 關閉 |

守護行程（daemon）的主機成本：擷取速度 **2,762 事件/秒**，磁碟上
**每事件 710 位元組**（每 10 萬事件 67.7 MB），繁忙安裝環境下持續佔用
**約 12% 的單一核心**。最後這個數字超出了我們自訂的 5-10% 預算，
因此我們將其視為需要追蹤解決的 bug 公開，而非略過不提。

在 Apple M2 Pro 上以 `benchmarks/overhead.py` 測得。此測試工具會在
獨立行程中執行每個條件，交替其順序，且**當多輪結果的正負號不一致時
拒絕輸出數字**。你可以在自己的機器上花一分鐘執行：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過測量，包括攔截閘道與強制執行代理，且此測試工具
在 CI 中於 Linux、macOS 與 Windows 上皆會執行。有兩個結果值得留意：
該代理（proxy）在 Windows 上的成本約為 Linux 上的七倍，而守護行程
目前持續佔用約 12% 的單一核心，超出我們自訂的 5-10% 預算。
原始 JSON 資料、方法說明，以及尚未測量的部分都在
[docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定價

| 方案 | 涵蓋內容 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose，完整儀表板，僅限本機 | $0 |
| **Starter** | 上述以外的所有執行環境、艦隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 控制與評估：審批、工具風險政策、評估、異常偵測、成本最佳化工具、OTel 匯出、防竄改稽核日誌 | 每節點每月 $19 |

年繳方案、企業方案及目前價格都列於
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰
無需雲端即可使用（`clawmetry license`）。確切的免費/付費區分請見
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你的機器上

ClawMetry 讀取本機的工作階段檔案與日誌。**除非你執行 `clawmetry connect`，
否則不會有任何工作階段資料離開你的機器**——不論是提示詞、回覆、工具參數、
檔案內容或日誌行皆然。當你確實連線時，快照會以你機器上永遠不會外流的
金鑰進行端對端加密，並在你的瀏覽器中解密。如果某個節點沒有金鑰，
上傳會被跳過而不是以明文傳送，且任何伺服器回應都無法關閉這項保護。

在你連線之前，預設會執行兩件事，兩者皆可選擇退出，且都不攜帶
工作階段資料：一個匿名安裝回報，以及對 PyPI 的版本檢查。預設安裝
也會查詢一次你的公開 IP，用於啟動時的橫幅顯示。每個目的地、
它攜帶的內容以及如何關閉，都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；
自架、重新導向或氣隙（air-gapped）安裝完全不會進行任何非必要的外送呼叫。

解密發生在你的瀏覽器中，使用我們提供給你的程式碼。這件事以前只是
一個承諾；現在它是可以被驗證的。所有觸及你金鑰的程式碼都放在
一個可讀的檔案中，[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)，
它隨 wheel 套件一起發布，並以逐字方式提供服務，並以子資源完整性
（Subresource Integrity）雜湊值釘選。若要確認瀏覽器執行的是我們發布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這無法證明的是：我們提供載入該檔案的頁面，所以我們理論上可以
提供不同的頁面。完整性雜湊值能保護你免受遭入侵的 CDN 影響，
但無法保護你免受供應商本身的影響。你所獲得的保障是，任何替換
都必須是刻意為之、在頁面原始碼中可見，且與任何人都能從 PyPI
取得的成品不同。自架或僅使用本機模式則完全消除了這種依賴。

## 安裝

```bash
pip install clawmetry     # 接著執行：clawmetry
```

或使用一行指令安裝：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8 以上版本，以及
同一台機器上至少一個代理執行環境。Docker 安裝說明：[docs/DOCKER.md](docs/DOCKER.md)。

或者讓代理程式為你設定。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能可以教會 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode
安裝 ClawMetry、回報機器上代理程式正在做什麼與花費多少、
依需求停止某個工作階段，並暫留高風險的工具呼叫以待審批：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個轉接器（adapter）讀取什麼，以及如何新增一個執行環境 |
| [情境爆量](docs/CONTEXT_BLOWOUT.md) | 依供應商劃分的視窗、壓縮 vs 溢位、各執行環境的涵蓋範圍 |
| [額外開銷](docs/OVERHEAD.md) | 檢測工具的實際成本，附可重現的測試工具 |
| [權限（Entitlements）](docs/ENTITLEMENTS.md) | 免費 vs 付費、方案等級矩陣、授權 CLI |
| [審批與政策](docs/APPROVALS.md) | 執行前攔截、風險評分、手機審批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤資料匯出至任何地方，並從任何來源擷取 OTLP |
| [自帶代理程式（Bring your own agent）](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 端對端範例，附可執行程式碼 |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為你自行打造的代理程式做成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、磁碟區掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理；從原始碼執行 |
| [遙測（Telemetry）](docs/TELEMETRY.md) | 匿名安裝與桌面開啟回報，以及如何關閉它們 |

## 螢幕截圖

以下每個數字都來自一台真實機器，以唯讀方式讀取，沒有任何預先安排的資料。

**它會告訴你哪裡出了問題，而不只是發生了什麼事。**
頂端有兩個異常橫幅：花費達到日均的 7 倍，以及一次 4.2 倍的成本激增。
下方則是最近 667 個工作階段中有 324 個帶有浪費訊號，並依原因逐項列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它會顯示每個時間區間內的錢花到哪裡去了。**
今天 $252.47、本週 $513.15、本月 $1,312.92，每項都附上背後的 token 數，
以及你的訂閱方案已涵蓋的比例。下方則是約每月 $1,128 可回收成本的
逐項清單，以及快取重用已節省的每月 $17,256。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它會繪製訊息如何變成答案的過程。**
即時流程圖：你、訊息抵達的頻道、閘道（gateway）、目前正在回答的模型，
以及它呼叫的每個工具。當工作在其中流動時，節點會亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每個代理程式，都在一張表格中。**
它執行的內容、過去 24 小時與整個生命週期的花費、最後一次出現的時間、
擁有者，以及是否有訂閱方案涵蓋這筆費用。這裡有 14 個代理程式，
3 個工作階段正在運作，13 個閒置中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它會逐工具顯示一個回合的時間與金錢花在哪裡。**
一個真實工作階段的一個回合：11.2 分鐘內執行了 11 個工具，花費 $1.16。
每次 Bash 呼叫和模型呼叫都有自己的時間軸長條，因此執行了 4.1 分鐘的
指令和只執行了 226 毫秒的指令一眼就能區分。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它評的是工作品質，而不只是花費。**
本週得到 A 等：54 項任務乾淨完成，2 項較粗糙的任務花費 $48.57，
而活動量不足以判斷的執行紀錄則會被排除在評分之外，而不是被算作成功。
每個較粗糙的執行紀錄都連結到其追蹤記錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它會顯示情境視窗為何持續被填滿。**
最新回合使用了 100 萬 token 視窗中的 71.5 萬，峰值 83.3%，發生了 4 次
壓縮，且全都是主動觸發而非因溢位而觸發，並顯示其背後每個回合的使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能無需任何設定即可運作。**
內建偵測器從安裝起就已啟用：代理程式無回應、遙測資料流中斷、
成本激增、token 用量暴增、錯誤攀升、錯誤激增、預算門檻、
威脅特徵比對、安全工具發現、安全態勢變化。你自己的規則則是額外可選項目。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**攔截高風險呼叫是選擇性開啟的功能，出廠時預設關閉。**
遞迴刪除、強制推送（force push）、sudo、機密資訊、套件安裝以及
外送呼叫，每一項都有可自行開啟的規則。在你開啟之前，ClawMetry
只會觀察而不會改變任何事。一旦開啟，符合條件的呼叫就會在這裡
（或你的手機上）等待批准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多內容，依執行環境分類：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 肯定與獎項

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star 歷史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 授權

MIT · 由 [@vivekchand](https://github.com/vivekchand) 打造 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
