<!-- i18n-src:c99ac0512cae -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**代理可以呼叫上百次工具卻毫無進展。** ClawMetry
讀取您的程式碼代理已經在寫入的 session 檔案，並將時間軸、
工具呼叫記錄，以及執行環境所公開的 token 與成本資料整合到一個
視圖中，讓您能分辨出正在正常運作的長時間執行與卡住的執行。

支援 **33 種 AI 代理執行環境** — Claude Code、OpenAI Codex、Hermes、OpenClaw 以及其他 29 種。一個儀表板管理您整個代理機群。([完整清單](SUPPORTED_RUNTIMES.txt)，由目錄自動產生。)

> 🌐 **閱讀其他語言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測所有東西。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟。零設定：它會找到您機器上已經安裝的
代理執行環境，以唯讀方式讀取它們，不會改變它們原有的運作方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安裝前須知

| | |
|---|---|
| **它做什麼** | 讀取您的代理已經在寫入的 session 檔案與日誌。沒有 SDK，不需要更改程式碼，不在您的應用程式中插入任何埋點。 |
| **您會看到什麼** | Session 時間軸、逐工具重播、token 與成本拆解，以及軌跡訊號（迴圈、重複失敗）— 依執行環境區分。 |
| **哪些是免費的** | `pip install clawmetry` 可讀取 **OpenClaw、NVIDIA NemoClaw、Goose 與 Qwen Code**，不需帳號、不需金鑰、也不會呼叫網路。另外 28 種 — Claude Code、Codex、Cursor 以及其他 — 由閉源的 `clawmetry-pro` 附屬套件讀取，該套件會隨 7 天試用或付費方案提供 — 確切的區分方式請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何開始** | `pip install clawmetry && clawmetry`，然後開啟 localhost:8900。這台機器上還沒有代理？`clawmetry --sample` 會開啟三個標記好的合成 session。 |
| **哪些資料會離開您的機器** | 不會有任何 session 資料離開，除非您執行 `clawmetry connect`。預設會執行兩項功能，兩者皆可停用，且都不會攜帶 session 內容：匿名安裝回報與 PyPI 版本檢查。所有目的地都列在 [docs/EGRESS.md](docs/EGRESS.md) 中，該文件是依據網路封包擷取重建，而非依據程式碼註解。 |

在您評斷輸出結果之前，有兩個限制值得了解：各執行環境公開的資料
差異很大（有些完全不公開成本資料 — [相容性矩陣](docs/compatibility.md)
會依執行環境說明細節），而且「觀察到一個動作」不等同於「能夠
阻止它」（[每個執行環境實際具備哪些控制能力](docs/APPROVALS.md)）。


## 支援 33 種代理執行環境

**開源版本中免費：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**付費方案：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每個執行環境都會取得相同的儀表板。同時執行多個時，頂部的
切換器會將每個分頁重新對應到其中一個。

自己用 SDK 打造的代理？攔截器 (interceptor) 也會追蹤它的 LLM 呼叫。
詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 您會獲得什麼

- **Sessions 與逐字稿**：每個代理逐輪做了什麼，並可重播
- **成本與 Token**：依執行環境、模型、session 與日期區分，並標記異常
- **流程 (Flow)**：訊息流經頻道、模型與工具的即時圖表
- **思考過程 (Brain)**：即時的推理與工具呼叫事件串流
- **情境爆量 (Context blowout)**：依供應商調整的視窗使用率、壓縮 (compaction) 與強制溢位的比較，以及每個執行環境「看不到什麼」的對照表（[原理](docs/CONTEXT_BLOWOUT.md)）
- **記憶與技能**：每個執行環境實際載入的檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、代理離線，可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **核准機制**：在高風險工具呼叫執行*之前*暫停，並可從手機核准（[原理](docs/APPROVALS.md)）

## 情境爆量，以及監控的成本

在您信任任何代理比較工具之前，值得先回答兩個問題。

**它如何跨執行環境處理情境視窗爆量？**

使用率百分比的可信度，取決於其分母是否誠實。ClawMetry
依供應商從[一份您可以閱讀並提交 PR 的表格](clawmetry/context_windows.py)
來決定視窗大小，涵蓋 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 與 GLM。它不會用單一廠商
的尺規去測量所有 33 個執行環境。這點很重要：一個 30 萬 token 的
GPT-5 輪次，若用 Anthropic 的 20 萬上限來評估，會顯示「>100%，已爆量」，
但實際上只是 GPT-5 的 40 萬上限的 75%。同一把尺規也會把一個
真正已溢位的 13 萬 token DeepSeek 輪次，誤判成舒適的 65%。

每個視窗都附帶其來源資訊：`model_table`、`explicit_marker`、
`observed_floor`，或是在我們不知道模型時誠實標示的 `default`。
一個建立在猜測上的儀表，永遠不該以建立在查表上的儀表相同的
權威性呈現。

ClawMetry 只能在某些執行環境上看到壓縮 (compaction) 事件。所以
`GET /api/context-coverage` 會針對每個執行環境回報，「0」究竟代表
**「乾淨地跑完」還是「我們看不到」**。真正意味著「看不到」的 0 會
如實標示。[完整細節](docs/CONTEXT_BLOWOUT.md)

**埋點的成本是多少？**

| 路徑 | 加到您代理上的額外成本 | 預設啟用？ |
|---|---|---|
| Session 檔案追蹤（全部 33 個執行環境） | **0**。獨立行程，您的代理中不含任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 呼叫 **+0.44 毫秒**，相當於一次 5 秒呼叫的 0.009% | 關閉 |
| 工具前置鉤子閘門（暖快取） | 每次受管控的工具呼叫 **+44 毫秒**，在 36 毫秒的解譯器基準之上 | 關閉 |
| 強制執行代理 (Enforcement proxy) | 每次 LLM 呼叫 **+9.7 毫秒** | 關閉 |

Daemon 主機成本：擷取 (ingest) **每秒 2,762 個事件**，每個事件
磁碟上 **710 bytes**（每 10 萬個事件 67.7 MB），在繁忙的安裝環境
中持續佔用 **約 12% 的單核心**。最後一個數字超出了我們自訂的
5-10% 預算，因此公開列為待追蹤的 bug，而非隱藏不提。

在 Apple M2 Pro 上使用 `benchmarks/overhead.py` 測得。此測試
框架會在獨立行程中執行每種情況，交替其順序，並**在多輪結果
符號不一致時拒絕輸出數字**。您可以在自己的機器上一分鐘內
執行它：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過測量，包括鉤子閘門與強制執行代理，且此測試
框架在 CI 中於 Linux、macOS 與 Windows 上執行。有兩個結果值得
注意：在 Windows 上的代理成本大約是 Linux 的七倍，而 daemon
目前持續佔用約 12% 的單核心，超出我們自訂的 5-10% 預算。原始
JSON 資料、方法，以及仍未測量的部分都在
[docs/OVERHEAD.md](docs/OVERHEAD.md)。

## 定價

| 方案 | 涵蓋內容 | 價格 |
|---|---|---|
| **免費** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code，完整儀表板，僅限本機 | $0 |
| **Starter** | 上述以外的所有執行環境、機群視圖、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 控制與評估功能：核准機制、工具風險政策、評估 (evals)、異常偵測、成本優化器、OTel 匯出、防竄改稽核日誌 | 每節點每月 $19 |

年繳方案、企業版以及目前的價格資訊請見
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰
可在不使用雲端的情況下運作（`clawmetry license`）。確切的免費/
付費區分請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 您的資料留在您的機器上

ClawMetry 讀取本機的 session 檔案與日誌。**除非您執行
`clawmetry connect`，否則沒有任何 session 資料會離開您的機器** —
不含提示詞、回覆、工具參數、檔案內容或日誌內容。當您連接時，
快照會以端對端加密傳輸，金鑰永不離開您的機器，並在您的瀏覽器
中解密。如果某個節點沒有金鑰，上傳會被跳過而不會以未加密方式
傳送，且任何伺服器回應都無法關閉這項保護。

連接前預設會執行兩項功能，兩者皆可停用，且都不會攜帶 session
資料：匿名安裝回報與針對 PyPI 的版本檢查。預設安裝也會查詢一次
您的公開 IP，用於啟動時顯示的橫幅文字。所有目的地、其攜帶的內容
以及如何關閉，都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；自架、
重新指向或氣隙 (air-gapped) 的安裝完全不會發出任何選擇性的
對外呼叫。

解密是在您的瀏覽器中、以我們提供給您的程式碼完成的。這過去只是
一項承諾；現在您可以親自驗證。所有會接觸到您金鑰的程式碼都
放在一個可讀的檔案中，
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)，
它隨 wheel 套件一起發佈，並原封不動地提供服務，並以子資源完整性
(Subresource Integrity) 雜湊值固定。若要確認瀏覽器執行的是我們
發佈的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這無法證明的是：我們也提供載入這個檔案的頁面，所以我們理論上
可以提供不同的頁面。完整性雜湊值能保護您免受 CDN 遭入侵的風險，
但無法防範供應商本身。您所獲得的保障是：任何替換都必須是刻意
的、在頁面原始碼中可見的，且與任何人都能從 PyPI 取得的套件內容
不同。自架或完全保持在本機運作，可以徹底消除這種依賴。

## 安裝

```bash
pip install clawmetry     # 然後執行: clawmetry
```

或使用一行指令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+，以及同一台機器上
至少一個代理執行環境。Docker 安裝說明請見 [docs/DOCKER.md](docs/DOCKER.md)。

或者讓代理替您安裝。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能可以教導 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或
OpenCode 安裝 ClawMetry、回報機器上的代理正在做什麼與花費多少、
依要求停止某個 session，並保留高風險的工具呼叫等待核准：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個 adapter 讀取的內容，以及如何新增執行環境 |
| [情境爆量](docs/CONTEXT_BLOWOUT.md) | 依供應商區分的視窗、壓縮與溢位的比較、各執行環境的覆蓋範圍 |
| [額外負擔 (Overhead)](docs/OVERHEAD.md) | 埋點的實際測量成本，以及重現測試用的框架 |
| [授權等級 (Entitlements)](docs/ENTITLEMENTS.md) | 免費與付費比較、方案矩陣、授權 CLI |
| [核准機制與政策](docs/APPROVALS.md) | 執行前閘門、風險評分、手機核准 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 匯出追蹤記錄至任何地方，從任何來源接收 OTLP |
| [自帶代理 (Bring your own agent)](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 端到端說明，附可執行範例 |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 您自行建置代理的成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天 adapter |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、volume 掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理；從原始碼執行 |
| [遙測 (Telemetry)](docs/TELEMETRY.md) | 匿名安裝與桌面開啟回報，以及如何關閉它們 |

## 截圖

以下每個數字都來自一台真實機器，以唯讀方式讀取，沒有任何
預先植入的資料。

**它會告訴您哪裡出問題，而不只是發生了什麼事。**
頂部有兩個異常橫幅：花費達到每日平均的 7 倍，以及一次 4.2 倍
的成本激增。下方則是最近 667 個 session 中有 324 個帶有浪費
訊號，並依原因逐項列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它會顯示每個時間區間的花費去向。**
今日 $252.47、本週 $513.15、本月 $1,312.92，各自附上背後的
token 數量，以及您的訂閱方案已涵蓋的比例。下方則列出約每月
$1,128 可回收的項目，以及快取重複使用已經節省的每月 $17,256。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它會繪製出一則訊息如何變成一個答案。**
即時流程圖：您、訊息抵達的頻道、閘道、目前正在回答的模型，
以及它呼叫的每一個工具。隨著工作流經各個節點，節點會逐一
亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每個代理，整合在一個表格中。**
它執行什麼、過去 24 小時與整個生命週期的花費、最後出現的
時間、擁有者，以及是否有訂閱方案涵蓋費用。此處顯示 14 個
代理，3 個 session 正在工作，13 個閒置。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它會逐工具顯示一輪對話的時間與金錢花在哪裡。**
一次真實 session 的其中一輪：11 個工具在 11.2 分鐘內花費 $1.16。
每一次 Bash 呼叫與模型呼叫都在時間軸上有自己的橫條，因此一眼
就能分辨出執行了 4.1 分鐘的指令與只跑了 226 毫秒的指令。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它評估的是工作品質，而不只是花費。**
本週評等為 A：54 個任務乾淨完成，2 個品質較差的任務花費
$48.57，而活動量太少不足以評估的執行則被排除在評等之外，
而非被計入為成功案例。每個品質較差的執行都連結到其追蹤記錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它會顯示情境視窗為何持續被填滿。**
最新一輪使用了 100 萬 token 視窗中的 71.5 萬，峰值 83.3%，
4 次壓縮全都是主動觸發而非因溢位觸發，並顯示其背後每一輪的
使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能無需任何設定即可運作。**
內建偵測器從安裝時就已啟用：代理靜默無回應、遙測資料流中斷、
成本激增、token 爆量、錯誤率上升、錯誤激增、預算門檻、威脅
特徵比對、安全工具發現、安全態勢變化。您自己的規則是額外的
選用項目。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**攔截高風險呼叫是選用功能，且預設關閉。**
遞迴刪除、強制推送、sudo、機密資料、套件安裝與對外呼叫，
每一項都有可開啟的規則。在您開啟之前，ClawMetry 只會觀察，
不會改變任何事。一旦開啟，符合條件的呼叫就會在此處（或您的
手機上）等待核准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多依執行環境分類的截圖：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 獲得的認可

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
