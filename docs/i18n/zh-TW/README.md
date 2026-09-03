<!-- i18n-src:9767c8001c9c -->
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

**看見你的代理在思考。** 針對 **30 種 AI 代理執行環境**的即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 26 種。一個儀表板掌控你整個代理艦隊。

> 🌐 **本文件其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

會在 **http://localhost:8900** 開啟。零設定：它會找出你機器上已有的代理執行環境，以唯讀方式讀取它們,不會改變它們的任何運作方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 支援 30 種代理執行環境

**開源應用中免費提供：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每個執行環境都使用相同的儀表板。同時執行多個時，頁首的切換器可以將每個分頁重新指向其中任一個。

自己用某個 SDK 打造了代理？攔截器同樣會追蹤它的 LLM 呼叫。詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能獲得什麼

- **工作階段與逐字稿**：每個代理逐輪做了什麼,可重播
- **成本與 token**：依執行環境、模型、工作階段與日期分類,附帶異常標記
- **流程（Flow）**：訊息在頻道、模型與工具間流動的即時圖表
- **大腦（Brain）**：推理與工具呼叫事件的即時串流
- **情境爆量（Context blowout）**：依供應商調整大小的視窗使用率,壓縮 vs 強制溢位,以及每個執行環境「我們看不到什麼」的地圖（[原理](docs/CONTEXT_BLOWOUT.md)）
- **記憶與技能**：每個執行環境實際載入的檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、代理離線,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **審批**：在風險工具呼叫執行*之前*暫停,並可從手機核准（[原理](docs/APPROVALS.md)）

## 情境爆量,以及觀測的成本

在你信任任何代理比較工具之前,值得先弄清楚兩個問題。

**它如何處理跨執行環境的情境視窗爆量？**

使用率百分比的可信度,取決於它拿什麼當分母。ClawMetry 依供應商從[一份你可以閱讀並提交 PR 的表格](clawmetry/context_windows.py)決定視窗大小,涵蓋 Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不會用同一家廠商的尺去衡量全部 26 種執行環境。這很重要：用 Anthropic 的 200K 去衡量一個 300K 的 GPT-5 回合,會讀成「>100%,爆了」,但實際上只是 GPT-5 自家 400K 視窗的 75%。同一把尺也會把一個真正溢位的 130K DeepSeek 回合隱藏成看似舒適的 65%。

每個視窗都附帶其來源：`model_table`、`explicit_marker`、`observed_floor`,或是在我們不認識該模型時誠實標示為 `default`。建立在猜測上的量表,永遠不該和建立在查表上的量表具有同等權威性。

ClawMetry 只能在部分執行環境上看到壓縮事件。因此 `GET /api/context-coverage` 會依執行環境回報,一個 **0 到底代表「乾淨執行完」還是「我們看不見」**。真正代表看不見的 `0`,會如實說明。[完整說明](docs/CONTEXT_BLOWOUT.md)

**這套儀器化本身要花多少代價？**

| 路徑 | 對你代理增加的負擔 | 預設值？ |
|---|---|---|
| 工作階段檔案追蹤（全部 30 種執行環境） | **0**。獨立行程,你的代理內沒有任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 呼叫 **+0.44 毫秒**,相當於一次 5 秒呼叫的 0.009% | 關閉 |
| 前置工具掛鉤閘門（暖快取） | 每次受管控的工具呼叫 **+44 毫秒**,高於 36 毫秒的直譯器基準 | 關閉 |
| 執行防護代理（proxy） | 每次 LLM 呼叫 **+9.7 毫秒** | 關閉 |

守護行程（daemon）主機成本：擷取速率 **每秒 2,762 個事件**、磁碟上**每事件 710 位元組**（每 10 萬個事件 67.7 MB）,在繁忙安裝環境下持續佔用**約一個核心的 12%**。最後這個數字超出了我們自訂的 5-10% 預算,因此我們把它當成一個要追蹤的 bug 公開出來,而不是隱藏不提。

在 Apple M2 Pro 上以 `benchmarks/overhead.py` 測得。該測試工具會將每種情境放在獨立行程中執行,交替其順序,並在**多輪結果正負號不一致時拒絕印出數字**。你可以在自己的機器上花一分鐘跑一次：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過測量,包含掛鉤閘門與防護代理,而這套測試工具在 CI 中會於 Linux、macOS 與 Windows 上執行。有兩個值得留意的結果：防護代理在 Windows 上的成本大約是 Linux 的七倍,而守護行程目前持續佔用約一個核心的 12%,超出我們自訂的 5-10% 預算。原始 JSON、方法論,以及尚未測量的部分都在 [docs/OVERHEAD.md](docs/OVERHEAD.md)。

## 定價

| 方案 | 涵蓋範圍 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整儀表板,僅限本機 | $0 |
| **Starter** | 以上其他所有執行環境、艦隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 控制與評估：審批、工具風險政策、評估（evals）、異常偵測、成本優化器、OTel 匯出、防竄改稽核日誌 | 每節點每月 $19 |

年繳方案、企業版與最新價格請見
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰無需雲端即可運作
（`clawmetry license`）。確切的免費/付費分界請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你的機器上

ClawMetry 讀取本機的工作階段檔案與日誌。**除非你執行 `clawmetry connect`,否則沒有任何工作階段資料會離開你的機器**——不含提示詞、回覆、工具參數、檔案內容或日誌行。當你真的連線時,快照會以你機器上永不外流的金鑰進行端對端加密,並在你的瀏覽器中解密。若某個節點沒有金鑰,上傳會被跳過,而不是以明文傳送,且沒有任何伺服器回應能關閉這項保護。

有兩件事會在你連線之前預設執行,兩者皆可選擇退出、也都不攜帶任何工作階段資料：一個匿名安裝回報 ping,以及對 PyPI 的版本檢查。預設安裝也會查詢一次你的公開 IP,用於啟動橫幅顯示。每個目的地、它攜帶什麼資訊,以及如何關閉,都列在
[docs/EGRESS.md](docs/EGRESS.md) 中；自架、重新指向或氣隙（air-gapped）安裝完全不會有任何可選的對外呼叫。

解密發生在你的瀏覽器中,使用我們提供給你的程式碼。這曾經只是一句承諾;現在你可以親自檢查。每一行碰觸到你金鑰的程式碼都在同一個可讀檔案中,[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),它隨 wheel 一起發布,以原樣提供服務,並以次資源完整性（Subresource Integrity）雜湊值釘選。若要確認瀏覽器執行的正是我們發布的內容：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這無法證明的是：我們也提供載入這個檔案的頁面,所以我們理論上可以提供一個不同的頁面。完整性雜湊能保護你免受 CDN 遭入侵的影響,但無法防範供應商本身。你能確保的是,任何替換行為都必須是刻意的、在頁面原始碼中可見的,且與任何人都能從 PyPI 下載到的產物不同。自架或僅使用本機模式,則完全不需要依賴這份信任。

## 安裝

```bash
pip install clawmetry     # 然後執行: clawmetry
```

或使用一行安裝指令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台機器上至少一個代理執行環境。Docker 說明請見 [docs/DOCKER.md](docs/DOCKER.md)。

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個轉接器（adapter）會讀取什麼,以及如何新增一個執行環境 |
| [情境爆量](docs/CONTEXT_BLOWOUT.md) | 各供應商的視窗大小、壓縮 vs 溢位、各執行環境的涵蓋範圍 |
| [效能開銷](docs/OVERHEAD.md) | 儀器化的實測成本,附可重現的測試工具 |
| [權益（Entitlements）](docs/ENTITLEMENTS.md) | 免費 vs 付費、方案矩陣、授權 CLI |
| [審批與政策](docs/APPROVALS.md) | 執行前把關、風險評分、手機審批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 匯出追蹤到任何地方,從任何來源攝取 OTLP |
| [自帶代理（Bring your own agent）](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 的完整流程,附可執行範例 |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為你自行打造的代理進行成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、磁碟區掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理;從原始碼執行 |
| [遙測](docs/TELEMETRY.md) | 匿名安裝與開啟桌面版的 ping,以及如何關閉它們 |

## 截圖

以下每個數字都來自一台真實機器,唯讀取得,未經任何刻意安排。

**它會告訴你哪裡出了問題,而不只是發生了什麼事。**
頂部兩則異常橫幅：花費達到每日平均的 7 倍,以及一次 4.2 倍的成本激增。下方顯示最近 667 個工作階段中有 324 個帶有浪費訊號,並依原因逐項列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它會告訴你錢花到哪裡去了,涵蓋每個時間窗口。**
今日 $252.47,本週 $513.15,本月 $1,312.92,各自附帶背後的 token 數,以及你的訂閱方案已涵蓋多少。下方是約每月 $1,128 可回收的項目清單,以及快取重用已節省的每月 $17,256。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它會畫出一則訊息如何變成一個答案。**
即時流程圖：你、訊息抵達的頻道、閘道（gateway）、目前正在回答的模型,以及它呼叫的每個工具。節點會隨著工作流動而亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每個代理,全部列在一張表中。**
它執行什麼、過去 24 小時與整個生命週期的花費、最後一次出現的時間、負責人是誰,以及是否有訂閱方案涵蓋這筆費用。這裡有 14 個代理,3 個工作階段正在運作,13 個閒置中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它會逐一顯示一個回合的時間與金錢花在哪個工具上。**
一個真實工作階段的一個回合：11 個工具,耗時 11.2 分鐘,花費 $1.16。每次 Bash 呼叫與每次模型呼叫在時間軸上都有自己的長條,因此那個跑了 4.1 分鐘的指令,和那個只跑了 226 毫秒的指令,一眼就能分辨出來。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它評的是工作品質,而不只是花費。**
本週評級 A：54 個任務乾淨完成,2 個粗糙的任務花費了 $48.57,而活動量太少、無法判斷的執行紀錄則被排除在評級之外,而不是被計算為成功案例。每個粗糙的執行紀錄都連結到它的追蹤記錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它會告訴你情境視窗為何一直被填滿。**
最新回合使用了 1M token 視窗中的 715K,峰值 83.3%,4 次壓縮全部都是主動觸發,而非因溢位而觸發,並附上其背後每個回合的使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能無需你做任何設定即可運作。**
內建偵測器從安裝那一刻起就已啟用：代理無回應、遙測資料流中斷、成本激增、token 爆量、錯誤攀升、錯誤激增、預算門檻、威脅特徵比對、安全工具發現、安全態勢變化。你自己的規則則是可選的額外項目。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**攔截風險呼叫是選擇性加入的功能,且預設關閉。**
遞迴刪除、強制推送、sudo、機密資料、套件安裝與對外呼叫,各自都有可自行開啟的規則。在你開啟之前,ClawMetry 只會觀察,不會改變任何事。一旦開啟其中一項,符合條件的呼叫就會在此處（或你的手機上）等待核准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多依執行環境分類的截圖：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
