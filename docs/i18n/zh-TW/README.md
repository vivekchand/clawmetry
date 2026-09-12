<!-- i18n-src:a855a14295b0 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**一個 agent 可以呼叫上百次工具卻毫無進展。** ClawMetry
讀取你的編碼 agent 已經在寫入的 session 檔案，並把時間軸、
工具呼叫，以及該 runtime 所公開的任何 token 和成本資料整合到單一
畫面中──讓你分辨出一次正在推進的長時間執行，與一次卡住的執行有何不同。

支援 **32 種 AI agent runtime**──Claude Code、OpenAI Codex、Hermes、OpenClaw 及其他 28 種。一個儀表板管理你整個 agent 機隊。([完整清單](SUPPORTED_RUNTIMES.txt)，由目錄自動產生。)

> 🌐 **其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

開啟於 **http://localhost:8900**。零設定：它會找出你機器上已安裝的
agent runtime，以唯讀方式讀取它們,而不會改變它們的任何運作方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安裝前先了解

| | |
|---|---|
| **它做什麼** | 讀取你的 agent 已經在寫入的 session 檔案與日誌。沒有 SDK、不需要修改程式碼、不會在你的應用程式中植入任何監測邏輯。 |
| **你會看到什麼** | Session 時間軸、逐一工具的回放、token 與成本細分，以及軌跡訊號（迴圈、重複失敗）──依 runtime 區分。 |
| **免費的部分** | `pip install clawmetry` 可讀取 **OpenClaw、NVIDIA NemoClaw 和 Goose**，不需要帳號、金鑰,也不會有任何網路呼叫。其他 27 種──Claude Code、Codex、Cursor 及其餘──由閉源的 `clawmetry-pro` 配套元件讀取,隨 7 天試用或付費方案提供──確切劃分請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何開始** | `pip install clawmetry && clawmetry`，然後開啟 localhost:8900。這台機器上還沒有任何 agent？執行 `clawmetry --sample` 會以三個標示清楚的合成 session 開啟。 |
| **哪些資料會離開你的機器** | 除非你執行 `clawmetry connect`，否則沒有任何 session 資料會離開。預設情況下確實會執行兩件事，皆可選擇退出且都不帶有 session 內容：一次匿名安裝 ping 和一次 PyPI 版本檢查。每個目的地都記錄在 [docs/EGRESS.md](docs/EGRESS.md) 中,並且是根據封包擷取重建的,而非僅憑程式碼註解。 |

在你評斷輸出結果之前,有兩個限制值得了解：不同 runtime 公開的資料
差異很大（有些完全不公開成本──[相容性矩陣](docs/compatibility.md)
列出了各 runtime 的情況），而且「觀察到一個動作」不等於「有能力
阻止它」（[各 runtime 的實際可控項目](docs/APPROVALS.md)）。


## 支援 32 種 agent runtime

**開源應用中免費：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每個 runtime 都使用同一個儀表板。同時執行多個 runtime 時,
頂端的切換器會把每個分頁重新聚焦到其中一個。

自己用 SDK 打造了 agent？攔截器也能追蹤它的 LLM 呼叫。
詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你會得到什麼

- **Session 與逐字稿**：每個 agent 做了什麼,逐輪呈現,並可回放
- **成本與 token**：依 runtime、模型、session 與日期區分,並附有異常標記
- **Flow**：訊息流經頻道、模型與工具的即時圖表
- **Brain**：推理與工具呼叫事件串流,即時呈現
- **上下文爆量**：依供應商調整大小的視窗使用率、壓縮 vs. 強制溢出,以及每個 runtime 我們「看不到」的部分地圖（[原理](docs/CONTEXT_BLOWOUT.md)）
- **記憶與技能**：每個 runtime 實際載入的檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、agent 離線,轉發至 Slack、Discord、PagerDuty、Telegram、Email
- **審批**：在高風險工具呼叫執行**之前**暫停它,並可從你的手機核准（[原理](docs/APPROVALS.md)）

## 上下文爆量,以及觀測本身的代價

在你信任任何 agent 比較工具之前,有兩個問題值得先釐清。

**它如何處理跨 runtime 的上下文視窗爆量？**

一個使用率百分比,誠實與否取決於它所除以的分母是否誠實。ClawMetry
根據 [一份你可以閱讀並送出 PR 的表格](clawmetry/context_windows.py)
依供應商調整視窗大小,涵蓋 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不會用某一家廠商的
量尺去衡量全部 32 種 runtime。這很重要：一次 300K 的 GPT-5 對話輪,
若拿 Anthropic 的 200K 來評分,會顯示「>100%,已爆量」,但實際上
只佔 GPT-5 400K 視窗的 75%。同一把量尺也會把一次真正溢出的
130K DeepSeek 對話輪,誤判為看似安全的 65%。

每個視窗都附帶其來源標記：`model_table`、`explicit_marker`、
`observed_floor`,或是在我們不知道模型時誠實標示的 `default`。
一個建立在猜測上的量表,絕不會呈現出與建立在查表上相同的可信度。

ClawMetry 只能在部分 runtime 上看到壓縮事件。因此
`GET /api/context-coverage` 會針對每個 runtime 回報**一個零值代表
「乾淨執行完畢」還是「我們看不見」**。真正代表「看不見」的零值
會如實標明。[完整說明](docs/CONTEXT_BLOWOUT.md)

**這套監測的代價是什麼？**

| 路徑 | 加到你 agent 上的開銷 | 預設值？ |
|---|---|---|
| Session 檔案追蹤（全部 32 種 runtime） | **0**。獨立的行程,你的 agent 裡沒有任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 呼叫 **+0.44 毫秒**,約為一次 5 秒呼叫的 0.009% | 關閉 |
| 工具前置 hook 閘門（暖快取） | 每次受閘門控管的工具呼叫 **+44 毫秒**,高出直譯器基準 36 毫秒 | 關閉 |
| 強制執行代理 | 每次 LLM 呼叫 **+9.7 毫秒** | 關閉 |

Daemon 主機成本：ingest 速率 **2,762 事件/秒**、磁碟上
**每事件 710 位元組**（每 10 萬事件 67.7 MB）,以及在繁忙安裝上
持續佔用**約 12% 的單一核心**。最後這個數字超出了我們自己訂下的
5-10% 預算,因此我們把它當作待追蹤的問題公開,而非隱而不宣。

以 Apple M2 Pro 使用 `benchmarks/overhead.py` 測得。此測試框架會在
獨立行程中執行每種情境、交替其執行順序,並且**在多輪結果正負號
不一致時拒絕印出任何數字**。你可以在自己的機器上一分鐘內執行它：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過測量,包括 hook 閘門與強制執行代理,測試框架也在
CI 中於 Linux、macOS 和 Windows 上執行。有兩個結果值得留意：
代理在 Windows 上的成本大約是 Linux 上的七倍,而 daemon 目前
持續佔用約 12% 的單一核心,超出我們自訂的 5-10% 預算。原始
JSON 資料、測量方法,以及尚未測量的部分都在
[docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定價

| 方案 | 涵蓋範圍 | 價格 |
|---|---|---|
| **免費** | OpenClaw + NVIDIA NemoClaw + Goose,完整儀表板,僅限本機 | $0 |
| **Starter** | 上述以外的其他所有 runtime、機隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 控制與評估：審批、工具風險策略、評測、異常偵測、成本最佳化器、OTel 匯出、防竄改稽核紀錄 | 每節點每月 $19 |

年繳方案、企業版與目前的價格請參閱
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架的授權金鑰
即使沒有雲端也能運作（`clawmetry license`）。確切的免費/付費劃分
請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你的機器上

ClawMetry 讀取本機的 session 檔案與日誌。**除非你執行
`clawmetry connect`,否則沒有任何 session 資料會離開你的機器**──
包括提示詞、回覆、工具參數、檔案內容或日誌行都不會外流。當你連線之後,
快照會以你機器上永不外流的金鑰進行端對端加密,並在你的瀏覽器中解密。
如果某節點沒有金鑰,上傳會被跳過,而不會以明文傳送,任何伺服器端
回應都無法把這個保護關閉。

在你連線之前,預設就會執行兩件事,皆可選擇退出且都不帶有 session
資料：一次匿名安裝 ping,以及一次針對 PyPI 的版本檢查。預設安裝
還會查詢一次你的公開 IP,用於啟動橫幅的一行文字。每個目的地、
它攜帶的內容,以及如何關閉,都列在
[docs/EGRESS.md](docs/EGRESS.md) 中;自架、重新指向或氣隙隔離的
安裝,完全不會有任何可選的對外呼叫。

解密發生在你的瀏覽器中,使用的是我們提供給你的程式碼。這在過去
只是一個承諾;現在則是你可以自行檢查的事。每一行會接觸到你金鑰的
程式碼都放在單一可讀的檔案
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js) 中,
它隨 wheel 一起發布,並以逐字方式提供,並以子資源完整性（Subresource
Integrity）雜湊值釘選。要確認瀏覽器執行的正是我們發布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這個做法無法證明的是：我們也負責提供載入該檔案的頁面,所以我們
理論上仍可以提供不同的頁面。完整性雜湊保護你免受 CDN 遭入侵的
影響,但無法防範供應商本身。你所獲得的保障是,任何替換都必須是
刻意為之、在頁面原始碼中可被看見,而且會與任何人都能從 PyPI
取得的產出物不同。自架或僅使用本機模式,則完全不需要依賴這一點。

## 安裝

```bash
pip install clawmetry     # 然後執行：clawmetry
```

或使用一行指令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台機器上
至少一個 agent runtime。Docker 使用說明：[docs/DOCKER.md](docs/DOCKER.md)。

或者讓 agent 幫你安裝。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能會教會 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode
安裝 ClawMetry、回報機器上的 agent 正在做什麼與花費多少、依要求
停止某個 session,並暫停高風險的工具呼叫以待審批：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文件

| | |
|---|---|
| [Runtime 相容性](docs/compatibility.md) | 每個轉接器讀取什麼,以及如何新增一個 runtime |
| [上下文爆量](docs/CONTEXT_BLOWOUT.md) | 各供應商的視窗大小、壓縮 vs. 溢出、各 runtime 的涵蓋範圍 |
| [開銷](docs/OVERHEAD.md) | 監測的實際成本、測量方式,以及可重現的測試框架 |
| [權益（Entitlements）](docs/ENTITLEMENTS.md) | 免費 vs. 付費、方案層級矩陣、授權 CLI |
| [審批與策略](docs/APPROVALS.md) | 執行前閘門控管、風險評分、手機審批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤資料匯出到任何地方,並從任何來源匯入 OTLP |
| [自帶你自己的 agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 端到端範例,附可執行程式碼 |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 你自行打造的 agent 的成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、卷掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理;從原始碼執行 |
| [遙測](docs/TELEMETRY.md) | 匿名安裝與開啟桌面應用的 ping,以及如何關閉它們 |

## 截圖

以下每個數字都來自一台真實機器,唯讀擷取,沒有任何預先安排的資料。

**它會告訴你何時出了問題,而不只是發生了什麼。**
頂部兩個異常橫幅：支出達到日均值的 7 倍,以及一次 4.2 倍的
成本激增。下方則列出最近 667 個 session 中,有 324 個帶有浪費訊號,
並依原因逐項列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它會告訴你錢花到哪裡去了,在每一個時間區間。**
今天 $252.47、本週 $513.15、本月 $1,312.92,每一項都附有背後的
token 數量,以及你的訂閱方案已涵蓋多少。下方則是約每月 $1,128
的可回收項目,以及快取重複使用已省下的每月 $17,256。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它會畫出一則訊息如何變成一個答案。**
即時流程圖：你本人、訊息抵達的頻道、閘道、目前正在回答的模型,
以及它呼叫過的每一個工具。節點會隨著工作流經而亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每一個 agent,都在同一張表格中。**
它執行什麼、過去 24 小時與整個生命週期的花費、最後一次被看到
的時間、擁有者是誰,以及是否有訂閱方案在支付費用。這裡有
14 個 agent,3 個 session 正在工作,13 個閒置中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它會逐一工具地顯示每一輪對話的時間與金錢花到哪裡。**
一次真實 session 的一輪對話：11 個工具、耗時 11.2 分鐘、花費 $1.16。
每一次 Bash 呼叫與模型呼叫都在時間軸上有自己的長條,因此耗時 4.1
分鐘的指令與耗時 226 毫秒的指令一眼就能分辨。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它會為工作品質評分,而不只是評估花費。**
本週得到 A 評等：54 個任務乾淨完成,2 個品質欠佳的花費 $48.57,
而活動量太少、不足以評判的執行則會被排除在評等之外,而不是
被計入為成功。每一個品質欠佳的執行都連結到它的追蹤紀錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它會顯示上下文視窗為何不斷被填滿。**
最新一輪對話用掉 1M-token 視窗中的 715K,峰值達 83.3%,4 次壓縮
全部是主動觸發,而非因溢出而觸發,並附上其之前每一輪對話的使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能不需要你做任何設定就能運作。**
內建偵測器從安裝那一刻起就已啟動：agent 沉寂、遙測資料流中斷、
成本激增、token 爆量、錯誤攀升、錯誤激增、預算門檻、威脅特徵符合、
安全工具發現問題、安全態勢改變。你自己的規則則是可選的額外項目。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**攔截高風險呼叫是選擇性開啟的,且預設就是關閉的。**
遞迴刪除、強制推送、sudo、機密資訊、套件安裝與對外呼叫,
各自都有一條可以開啟的規則。在你開啟之前,ClawMetry 只會觀察,
不會改變任何事。一旦開啟其中一條,符合的呼叫就會在這裡
（或你的手機上）等待核准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多截圖,依 runtime 分類：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 獲得的肯定

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
