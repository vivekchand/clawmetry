<!-- i18n-src:88be2deff5d5 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的代理在想什麼。** 針對 **30 種 AI 代理執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex，還有另外 26 種。一個儀表板，掌控你整個代理艦隊。

> 🌐 **以下語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟。零設定：它會找出你機器上已有的代理執行環境，以唯讀方式讀取，且完全不改變它們的運作方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 支援 30 種代理執行環境

**開源應用中免費提供：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案提供：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每種執行環境都能使用相同的儀表板。同時執行多種也沒問題，頂部的切換器會把每個分頁重新聚焦到其中一種上。

自己用 SDK 打造的代理呢？攔截器一樣能追蹤它的 LLM 呼叫。詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能獲得什麼

- **工作階段與逐字稿**：每個代理逐輪做了什麼，並可重播
- **成本與 token**：依執行環境、模型、工作階段與日期呈現，附帶異常標記
- **流程圖**：訊息在頻道、模型與工具間流動的即時圖示
- **Brain**：即時的推理與工具呼叫事件串流
- **上下文爆量**：依供應商換算的視窗使用率、壓縮 vs 強制溢位，加上每個執行環境「看不到什麼」的對照表（[原理](docs/CONTEXT_BLOWOUT.md)）
- **記憶與技能**：每個執行環境實際載入了哪些檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、代理離線，可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **審核**：在有風險的工具呼叫*執行前*先暫停，並可從手機核准（[原理](docs/APPROVALS.md)）

## 上下文爆量，以及觀測本身的代價

在你信任任何代理比較工具之前，有兩個問題值得先問清楚。

**它如何處理跨執行環境的上下文視窗爆量？**

使用率百分比的可信度，取決於分母算得夠不夠誠實。ClawMetry 依供應商從[一張你可以閱讀也可以送 PR 的表格](clawmetry/context_windows.py)推算視窗大小，涵蓋 Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama 與 GLM。它不會用單一廠商的尺去衡量全部 30 種執行環境。這很重要：一個 300K 的 GPT-5 回合若拿 Anthropic 的 200K 當基準衡量，會被讀成「>100%，已爆量」,但實際上只是 GPT-5 400K 視窗的 75%。同一把尺也會把一個真正溢位的 130K DeepSeek 回合，粉飾成看似安全的 65%。

每個視窗數字都附帶其來源:`model_table`、`explicit_marker`、`observed_floor`,或在我們不知道模型時老實顯示 `default`。建立在猜測之上的量表,絕不該和建立在查表之上的量表擁有同等的權威性。

ClawMetry 只能在部分執行環境上看到壓縮事件。因此 `GET /api/context-coverage` 會針對每種執行環境回報:**0 代表「乾淨運行」還是「我們看不見」**。真正代表看不見的 `0`,就會誠實地這樣標示。[完整說明](docs/CONTEXT_BLOWOUT.md)

**這套監測工具本身要花多少代價？**

| 路徑 | 加諸於你的代理 | 預設啟用？ |
|---|---|---|
| 工作階段檔案追蹤（全部 30 種執行環境） | **0**。獨立處理程序，你的代理裡沒有任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 呼叫 **+0.44 毫秒**，相當於一次 5 秒呼叫的 0.009% | 關閉 |
| 工具前置掛鉤閘門（熱快取） | 每次受管控的工具呼叫 **+44 毫秒**，疊加在 36 毫秒的直譯器基底之上 | 關閉 |
| 執行代理（enforcement proxy） | 每次 LLM 呼叫 **+9.7 毫秒** | 關閉 |

守護行程主機成本:攝入 **每秒 2,762 個事件**、磁碟上**每個事件 710 位元組**（每 10 萬個事件 67.7 MB）,在忙碌的安裝環境上持續佔用**約 12% 的單一核心**。最後這個數字超出我們自訂的 5-10% 預算,因此我們選擇把它當成一個要追查的 bug 公開,而不是隱而不宣。

在 Apple M2 Pro 上以 `benchmarks/overhead.py` 測得。此測試工具會在獨立處理程序中執行每種情境、交替其順序,並且**在多輪結果正負號不一致時拒絕印出數字**。你可以在自己的機器上花一分鐘跑跑看:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過量測,包括掛鉤閘門與執行代理,而且這套測試工具在 CI 中會於 Linux、macOS 與 Windows 上運行。值得留意的兩個結果:代理在 Windows 上的成本約為 Linux 的七倍;而守護行程目前持續佔用約 12% 的單一核心,超出我們自訂的 5-10% 預算。原始 JSON、方法說明,以及尚未量測的部分,都在 [docs/OVERHEAD.md](docs/OVERHEAD.md)。

## 價格

| 方案 | 涵蓋範圍 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整儀表板,僅限本機 | $0 |
| **Starter** | 上述以外的所有執行環境、艦隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter 加上控制與評估功能:審核、工具風險政策、評估、異常偵測、成本優化器、OTel 匯出、防竄改稽核日誌 | 每節點每月 $19 |

年繳方案、企業方案與最新價格請見 **[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰不需雲端即可使用（`clawmetry license`）。免費/付費的確切分界，詳見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你自己的機器上

ClawMetry 讀取本機的工作階段檔案與日誌。**除非你執行 `clawmetry connect`，否則沒有任何工作階段資料會離開你的機器**——不會傳送提示詞、回覆、工具參數、檔案內容或日誌內容。當你真的連線時，快照會以你機器上永不外流的金鑰進行端對端加密，並在你的瀏覽器中解密。若某個節點沒有金鑰，上傳會被跳過而不是以明文傳送，且沒有任何伺服器回應能關閉這個保護。

在你連線之前，預設就會執行兩件事，兩者都可選擇退出，且都不攜帶工作階段資料：一個匿名的安裝回報，以及對 PyPI 的版本檢查。預設安裝也會查詢一次你的公開 IP，用於啟動橫幅的一行資訊。每個目的地、其攜帶的內容、以及如何關閉它，都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；自架、改指向自訂端點與氣隙（air-gapped）安裝完全不會有任何非必要的對外呼叫。

解密發生在你的瀏覽器中，執行的是我們提供給你的程式碼。過去這只是一句承諾；現在你可以自行查證。每一行接觸到你金鑰的程式碼，都在同一個可讀的檔案 [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js) 裡，它隨 wheel 一起發布，並以逐字方式提供，並用子資源完整性（Subresource Integrity）雜湊值釘選。若要確認瀏覽器執行的正是我們發布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這無法證明的是：我們也提供載入該檔案的頁面，因此理論上我們也可能提供另一個不同的頁面。完整性雜湊值能保護你免受被入侵的 CDN 所害，但無法防範供應商本身。你獲得的是：任何替換行為都必須是刻意的、在頁面原始碼中可見的，且會與任何人都能從 PyPI 取得的版本不同。若選擇自架或只在本機使用，則完全不需要依賴這件事。

## 安裝

```bash
pip install clawmetry     # 接著執行: clawmetry
```

或使用一行指令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+，以及同一台機器上至少一種代理執行環境。Docker 安裝說明：[docs/DOCKER.md](docs/DOCKER.md)。

或者讓代理幫你設定。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) 技能可以教會 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode 安裝 ClawMetry、回報機器上代理正在做什麼與花費多少、依要求停止某個工作階段、並暫留有風險的工具呼叫以待核准：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個轉接器讀取哪些資料，以及如何新增一種執行環境 |
| [上下文爆量](docs/CONTEXT_BLOWOUT.md) | 依供應商劃分的視窗、壓縮 vs 溢位、每個執行環境的涵蓋範圍 |
| [額外負擔](docs/OVERHEAD.md) | 監測工具實際量測到的成本，以及可重現此量測的測試工具 |
| [授權額度](docs/ENTITLEMENTS.md) | 免費 vs 付費、方案等級表、授權金鑰 CLI |
| [審核與政策](docs/APPROVALS.md) | 執行前把關、風險評分、手機審核 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤資料匯出到任何地方，並從任何來源攝入 OTLP |
| [自帶代理](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 端到端範例，附可執行程式碼 |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為你自行打造的代理進行成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、掛載卷設定 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理；從原始碼執行 |
| [遙測](docs/TELEMETRY.md) | 匿名安裝與桌面啟動回報，以及如何關閉它們 |

## 螢幕截圖

以下每個數字都來自一台真實機器，唯讀取得，沒有任何預先安排的資料。

**它會告訴你哪裡出問題了，而不只是發生了什麼事。**
頂部有兩則異常橫幅：支出達到日均值的 7 倍，以及一次 4.2 倍的成本激增。橫幅下方，最近 667 個工作階段中有 324 個帶有浪費訊號，並依原因逐一列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它會告訴你錢花到哪裡去了，在每一個時間窗口。**
今日 $252.47、本週 $513.15、本月 $1,312.92，各自附帶背後的 token 用量，以及你的訂閱方案已涵蓋多少。下方是約 $1,128/月被列為可回收的支出，以及快取重複使用已省下的 $17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它會畫出一則訊息如何變成一個答案。**
即時流程圖：你、訊息抵達的頻道、閘道、正在回應的模型，以及它用到的每一項工具。隨著工作推進，節點會依序亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每個代理，都在同一張表格裡。**
它在跑什麼、過去 24 小時與整個生命週期各花了多少、最後一次出現的時間、屬於誰、以及是否有訂閱方案涵蓋這筆費用。這裡有 14 個代理，3 個工作階段正在運作，13 個閒置中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它會逐一顯示一個回合的時間與金錢花在哪個工具上。**
一次真實工作階段中的一個回合：11.2 分鐘內用了 11 個工具，花費 $1.16。每一次 Bash 呼叫與模型呼叫都有自己的時間軸長條，讓耗時 4.1 分鐘的指令和只花 226 毫秒的指令，一眼就能分辨出來。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它評的是工作成果，而不只是花費。**
本週得到 A 評級：54 個任務乾淨完成，2 個不理想的任務花費 $48.57，而活動量太少、無法判斷的執行紀錄則被排除在評級之外，而不是被算作成功。每個不理想的執行紀錄都連結到它的追蹤記錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它會顯示為什麼上下文視窗一直被填滿。**
在最新一個回合中，1M token 視窗用掉了 715K，峰值達 83.3%，4 次壓縮全都是主動觸發、而非因溢位而觸發，並附上其背後每個回合的使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能不需要你做任何設定就能運作。**
內建偵測器從安裝起就已啟用：代理無回應、遙測資料流中斷、成本激增、token 用量暴衝、錯誤率上升、錯誤激增、預算門檻、符合威脅特徵、安全工具發現異常、安全態勢改變。你也可以在此之上額外加上自己的規則。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**暫留有風險的呼叫是選擇性啟用的，且預設關閉出貨。**
遞迴刪除、強制推送、sudo、機密資訊、套件安裝與對外呼叫，各自都有一個你可以自行開啟的規則。在你開啟之前，ClawMetry 只會觀察而不改變任何事。一旦開啟某項規則，符合條件的呼叫就會在這裡（或你的手機上）等待核准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多依執行環境分類的內容：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
