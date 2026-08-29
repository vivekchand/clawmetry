<!-- i18n-src:d21bea5161e0 -->
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

**看見你的 agent 在想什麼。** 為 **30 種 AI agent 執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex,以及另外 26 種。一個儀表板,管理你整個 agent 機隊。

> 🌐 **其他語言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟。零設定:它會找到你機器上已經在執行的 agent 執行環境,以唯讀方式讀取,不會改變它們的任何運作方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 支援 30 種 agent 執行環境

**開源應用中免費支援:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案支援:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每種執行環境都使用同一個儀表板。同時執行多個時,頁首的切換器會把每個分頁重新對應到其中一個執行環境。

自己用 SDK 打造了 agent?攔截器(interceptor)也能追蹤它的 LLM 呼叫。詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能獲得什麼

- **Sessions 與逐字稿**:每個 agent 逐輪做了什麼,並可重播
- **成本與 token**:依執行環境、模型、session 與日期劃分,並附異常標記
- **Flow**:訊息在 channel、模型與工具之間流動的即時圖示
- **Brain**:即時的推理與工具呼叫事件串流
- **Context blowout(上下文爆量)**:依供應商調整大小的視窗使用率、compaction 與強制溢出的比較,以及每種執行環境「我們看不到什麼」的對照表([原理](docs/CONTEXT_BLOWOUT.md))
- **Memory 與技能**:每個執行環境實際載入的檔案與技能
- **健康狀態與日誌**:磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**:預算上限、錯誤暴增、agent 離線,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **核准(Approvals)**:在有風險的工具呼叫執行*之前*暫停,並可從手機核准([原理](docs/APPROVALS.md))

## Context blowout,以及觀測要付出什麼代價

在你信任任何 agent 比較工具之前,值得先問清楚這兩個問題。

**它如何處理跨執行環境的上下文視窗爆量?**

使用率百分比的可信度,取決於它的分母是否誠實。ClawMetry 依供應商從[一張你可以閱讀、也可以送 PR 的表格](clawmetry/context_windows.py)取得視窗大小,涵蓋 Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama 與 GLM。它不會用單一廠商的尺去量所有 26 種執行環境。這很重要:一個 300K 的 GPT-5 回合若拿 Anthropic 的 200K 去對照,會顯示「>100%,已爆量」,但實際上只是 GPT-5 400K 視窗的 75%。同一把尺也會把一個真正溢出的 130K DeepSeek 回合藏成看似安全的 65%。

每個視窗數字都附有來源標記:`model_table`、`explicit_marker`、`observed_floor`,或是在我們不認識該模型時誠實標記為 `default`。用猜測建立的量表,永遠不該和用查表建立的量表擁有同等的可信度。

ClawMetry 只能在部分執行環境上看到 compaction 事件。所以 `GET /api/context-coverage` 會針對每個執行環境回報:**顯示 0 究竟代表「乾淨跑完」還是「我們看不到」**。真正代表「看不到」的 `0`,會如實說明。[完整說明](docs/CONTEXT_BLOWOUT.md)

**這套監測工具本身的成本是多少?**

| 路徑 | 加到你的 agent 上的成本 | 預設開啟? |
|---|---|---|
| Session 檔案追蹤(全部 30 種執行環境) | **0**。獨立行程,agent 內不含任何 ClawMetry 程式碼 | 開啟 |
| HTTP 攔截器(`CLAWMETRY_INTERCEPT=1`) | 每次 LLM 呼叫 **+0.44 ms**,相當於 5 秒呼叫的 0.009% | 關閉 |
| 工具前置(pre-tool)hook gate(暖快取) | 每次受控工具呼叫 **+44 ms**,在 36 ms 直譯器基線之上 | 關閉 |
| Enforcement proxy | 每次 LLM 呼叫 **+9.7 ms** | 關閉 |

Daemon 主機成本:每秒可攝取 **2,762 個事件**,每個事件在磁碟上占 **710 bytes**(每 10 萬個事件 67.7 MB),在忙碌的安裝環境中持續占用 **約 12% 的單一核心**。最後這個數字超出了我們自己設定的 5-10% 預算,因此我們把它公開列為一個要追的 bug,而不是隱藏不提。

在 Apple M2 Pro 上以 `benchmarks/overhead.py` 測得。測試工具會在各自獨立的行程中執行每種情境、交替執行順序,並且**當多輪結果的正負號不一致時拒絕輸出數字**。你可以在一分鐘內於自己的機器上執行它:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每條路徑都經過量測,包括 hook gate 與 enforcement proxy,而且這套測試工具在 CI 中於 Linux、macOS 與 Windows 上執行。有兩個結果值得留意:proxy 在 Windows 上的成本大約是 Linux 的七倍,而 daemon 目前持續占用約 12% 的單一核心,超出我們自訂的 5-10% 預算。原始 JSON、測量方法,以及尚未量測的部分,都在 [docs/OVERHEAD.md](docs/OVERHEAD.md)。

## 定價

| 方案 | 涵蓋內容 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整儀表板,僅限本機 | $0 |
| **Starter** | 以上以外的所有執行環境、機隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 控制與評估:核准、工具風險政策、評估(evals)、異常偵測、成本優化器、OTel 匯出、防竄改稽核日誌 | 每節點每月 $19 |

年繳方案、Enterprise 以及最新價格請見
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰(license key)不需連線雲端即可使用(`clawmetry license`)。確切的免費/付費劃分請見 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你的機器上

ClawMetry 讀取本機的 session 檔案與日誌。**除非你執行 `clawmetry connect`,否則不會有任何 session 資料離開你的機器** —— 不會傳送提示詞、回覆、工具參數、檔案內容或日誌內容。當你連線之後,快照會以端對端加密方式傳送,金鑰永遠不會離開你的機器,並在你的瀏覽器中解密。如果節點沒有金鑰,上傳會被跳過,而不是以明文傳送,而且沒有任何伺服器端回應能夠關閉這項保護。

在你連線之前,預設就會執行兩件事,兩者皆可選擇退出(opt-out),且都不含 session 資料:匿名安裝回報 ping,以及對 PyPI 的版本檢查。預設安裝也會查詢一次你的公開 IP,用於啟動橫幅顯示。每個外送目的地、它攜帶的內容,以及如何關閉它,都列在 [docs/EGRESS.md](docs/EGRESS.md);自架、重新導向或氣隙(air-gapped)安裝完全不會有任何可選的外送呼叫。

解密發生在你的瀏覽器中,使用我們提供給你的程式碼。這件事過去只是一句承諾,現在你可以自行驗證。所有會碰觸到你金鑰的程式碼都在同一個可讀檔案裡,[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),它隨 wheel 一起發佈,原封不動地提供,並以 Subresource Integrity 雜湊值固定。要確認瀏覽器執行的就是我們發佈的版本:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

這個方法無法證明的是:我們提供載入此檔案的網頁,所以我們仍然可以提供不同的網頁。完整性雜湊值能保護你免受 CDN 遭入侵的影響,但無法保護你免受供應商本身的行為影響。你所獲得的保障是:任何替換都必須是刻意為之、在網頁原始碼中可見,且與任何人都能從 PyPI 取得的產物不同。若採用自架或僅限本機的方式,則完全不需要依賴這項保障。

## 安裝

```bash
pip install clawmetry     # 然後執行:clawmetry
```

或使用一行指令:`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台機器上至少一種 agent 執行環境。Docker 安裝說明見 [docs/DOCKER.md](docs/DOCKER.md)。

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個轉接器讀取哪些內容,以及如何新增一種執行環境 |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | 各供應商的視窗大小、compaction 與溢出的比較、各執行環境的涵蓋範圍 |
| [開銷(Overhead)](docs/OVERHEAD.md) | 監測工具的實際成本,附可重現的測試工具 |
| [權益(Entitlements)](docs/ENTITLEMENTS.md) | 免費與付費差異、方案矩陣、license CLI |
| [核准與政策](docs/APPROVALS.md) | 執行前把關、風險評分、手機核准 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤資料匯出到任何地方,並從任何來源接收 OTLP |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為你自行打造的 agent 進行成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、volume 掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理;如何從原始碼執行 |
| [遙測(Telemetry)](docs/TELEMETRY.md) | 匿名安裝與開啟桌面應用的 ping,以及如何關閉它們 |

## 截圖

以下每個數字都來自一台真實機器,唯讀取得,沒有任何預先安排的資料。

**它會告訴你哪裡出問題,而不只是發生了什麼事。**
頂部有兩個異常橫幅:支出達到日均的 7 倍,以及一次 4.2 倍的成本暴增。橫幅下方,最近 667 個 session 中有 324 個帶有浪費訊號,並依原因逐項列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它顯示錢花到哪去了,涵蓋每個時間窗。**
今天 $252.47、本週 $513.15、本月 $1,312.92,各自附上背後的 token 數,以及你的訂閱方案已涵蓋的比例。下方則列出約 $1,128/月的可回收支出,以及快取重用已省下的約 $17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它畫出一則訊息如何變成一個答案。**
即時 flow 圖:你、訊息抵達的 channel、gateway、正在作答的模型,以及它呼叫的每個工具。節點會隨著工作流經而亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**機器上的每個 agent,都在同一張表格裡。**
它執行什麼、過去 24 小時與生命週期內的成本、最後一次上線時間、負責人是誰,以及是否有訂閱方案涵蓋這筆費用。這裡有 14 個 agent、3 個 session 正在運作、13 個閒置中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它逐一顯示一個回合的時間與花費都花在哪個工具上。**
一個真實 session 的一個回合:11 個工具、花了 11.2 分鐘、成本 $1.16。每個 Bash 呼叫與模型呼叫都在時間軸上有自己的長條,因此那個跑了 4.1 分鐘的指令,與那個只花 226 毫秒的指令,一眼就能區分。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它評的是工作品質,而不只是花費。**
本週得到 A 級:54 個任務乾淨完成,2 個品質不佳的任務花了 $48.57,而活動量太少、不足以評判的執行則不列入評分,而不是被算作成功。每個品質不佳的執行都連結到它的追蹤紀錄。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它顯示為什麼上下文視窗一直被填滿。**
最新回合使用了 1M token 視窗中的 715K,峰值達 83.3%,4 次 compaction 全都是主動觸發,而非因溢出而觸發,並附上背後每一回合的使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**偵測功能不需要你做任何設定就能運作。**
內建偵測器從安裝時就已啟用:agent 無回應、遙測資料饋送中斷、成本暴增、token 用量激增、錯誤率上升、錯誤暴增、預算門檻、符合威脅特徵、安全工具發現、安全態勢改變。你也可以在此之上額外新增自己的規則。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**攔截高風險呼叫是選擇性加入(opt-in),且預設關閉。**
遞迴刪除、強制推送(force push)、sudo、機密資訊、套件安裝與對外呼叫,各自都有一條可開啟的規則。在你開啟之前,ClawMetry 只會觀察,不會改變任何事。一旦開啟某條規則,符合條件的呼叫就會在此處(或你的手機上)等待核准或拒絕。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多依執行環境分類的截圖:[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
