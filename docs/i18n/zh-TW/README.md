<!-- i18n-src:191e9094d7fa -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的代理在想什麼。** 針對 **14 種 AI 代理執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex，以及其他 10 種。一個儀表板,涵蓋你整個代理艦隊。

> 🌐 **語言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令,零設定,自動偵測所有東西。

```bash
pip install clawmetry && clawmetry
```

會在 **http://localhost:8900** 開啟,就這樣完成了。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種代理執行環境

ClawMetry 最初是為 OpenClaw 打造的可觀測性工具,現在則能在同一個儀表板上為你**整個代理艦隊**進行計量,並自動偵測你機器上的每種執行環境:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw 與 NemoClaw 在開源應用程式中免費使用;其他執行環境則需要透過 ClawMetry Cloud 或自架的 Pro 授權才能啟用。從頁首切換執行環境,每個分頁(成本、代幣、工具、追蹤)都會重新聚焦到該執行環境。確切的免費/付費分界、方案矩陣、`/api/entitlement` 的資料結構,以及 `clawmetry license` CLI,請參見 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow** — 即時動畫圖表,顯示訊息如何流經頻道、大腦、工具再返回
- **Overview** — 健康檢查、活動熱力圖、工作階段數量、模型資訊
- **Usage** — 代幣與成本追蹤,提供日/週/月分佈
- **Sessions** — 使用中的代理工作階段,顯示模型、代幣、最後活動時間
- **Crons** — 排程任務,顯示狀態、下次執行時間、耗時
- **Logs** — 彩色即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 對話氣泡介面,用於閱讀工作階段歷史紀錄
- **Alerts** — 預算上限、錯誤率觸發、代理離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫,擋在一鍵核准之後

## 螢幕截圖

### 🧠 Brain — 即時代理事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — 代幣使用量與工作階段摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態消息
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 按模型與工作階段劃分的成本
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核紀錄
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、Slack / Discord / PagerDuty / Email 的 Webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫擋在人工核准之後;由政策驅動的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前攔截** — 一行指令即可安裝
PreToolUse 掛勾,在符合條件的工具呼叫*執行前*暫停,並等待
你的決定(啟用[雲端推播通知](https://app.clawmetry.com/push)後,手機一觸即可完成):

```bash
clawmetry hooks install     # 寫入 ~/.claude/settings.json(可重複執行)
clawmetry hooks status      # 目前已接上什麼,啟用了多少政策
clawmetry hooks uninstall   # 只移除 ClawMetry 加入的項目
```

拒絕只會阻擋那一次工具呼叫,代理仍保有其工作階段,並可嘗試其他做法。在手機上核准會略過 Claude Code 自身的權限提示(你已經回答過了)。未匹配到的工具大約只花費約 40ms,並會回落到 Claude Code 原本的權限流程。當 Claude Code 本身在等你回應時(`permission_prompt` / `idle_prompt` 通知),你也會收到手機推播。

## 安裝

**一行指令(推薦):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**從原始碼安裝:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 前端開發

v2 React 應用程式位於 `frontend/`,當 Flask 伺服器以啟用 v2 的方式啟動時,會在 `/v2` 提供服務。

開發時請使用兩個終端機:

```bash
# 終端機 1:於 :8900 執行 Flask API/伺服器
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 終端機 2:於 :5173 執行 Vite 開發伺服器
cd frontend
nvm use
npm ci
npm run dev
```

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理至
`http://localhost:8900`,因此 React 應用程式無需額外的 CORS 設定即可與本地 Flask 伺服器通訊。

若要建置隨 Python 套件發佈的產出包:

```bash
cd frontend
npm run build
```

正式產出包會寫入 `clawmetry/static/v2/dist/`。

## 執行環境/代理相容性

ClawMetry 觀察許多 AI 代理執行環境,不只是 OpenClaw。每個非 OpenClaw 的執行環境都會搭配一個專屬的讀取器轉接器,將其原生的工作階段格式轉換為 ClawMetry 的統一資料結構;背景守護程序會將它們一併寫入同一個 DuckDB 儲存庫 + 雲端快照,並標記其執行環境,當同時存在多種執行環境時,Session replay 分頁會顯示**執行環境切換器**。完整對照表與新增執行環境的指南請見 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族的入門介紹請見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

你正在使用 [Perplexity 的 numbat](https://github.com/perplexityai/numbat) 代理安全工具嗎?ClawMetry 開箱即用地擷取它的發現與執行決策,詳見 [`docs/NUMBAT.md`](docs/NUMBAT.md)。

| 執行環境/代理 | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。含逐字稿、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個工作階段一個 SQLite(`data/v2-sessions`)。含逐字稿 + 訊息計數。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。含逐字稿、模型、代幣/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。含逐字稿、模型、工具呼叫 + 思考過程、代幣使用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。含逐字稿、模型、工具呼叫、代幣使用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。含聊天/composer 逐字稿、模型。 |
| **Aider** | Beta 轉接器 | 每個專案一個 `.aider.chat.history.md`。含逐字稿、模型、代幣計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。含逐字稿、模型、工具呼叫、代幣總數。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。含逐字稿、模型、工具呼叫、代幣 + 成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。含逐字稿、模型、工具呼叫、代幣使用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。含逐字稿、模型、工具呼叫、代幣 + 成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。含逐字稿、模型、工具呼叫、代幣 + 成本。 |
| **n8n** | Beta 轉接器 | SQLite `~/.n8n/database.sqlite`。含工作流程執行、節點運作、AI Agent 提示,以及 n8n 有記錄的模型 + 代幣。 |
| **Antigravity** | Beta 轉接器 | 位於 `~/.gemini/<flavor>/brain/` 下的 Brain JSONL。含對話、工具步驟、思考過程、每次生成的 Gemini 代幣拆分 + 成本、背景生成消耗量。 |

「Beta 轉接器」代表 ClawMetry 為該執行環境的實際磁碟格式提供讀取器,每個都是根據真實機器上的真實安裝建置並驗證的(見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀,且對其執行環境實際儲存的內容誠實呈現(例如 PicoClaw/NanoClaw/Cursor 不會把代幣成本寫入磁碟)。當一個節點上同時執行多種執行環境時,執行環境切換器可將 sessions 檢視聚焦於單一環境,方便深入檢視。

## 追蹤任何 SDK 代理 — 迴圈外的成本歸屬

上述執行環境都會把工作階段寫入磁碟。但你自己的**正式環境代理**——基於 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 或單純的 `httpx` 迴圈打造的那個——並不會。ClawMetry 的零設定攔截器仍可透過對 `httpx`/`requests` 進行猴子補丁(monkey-patching),擷取它的 LLM 呼叫(成本、代幣、延遲、錯誤):

```python
import clawmetry.track            # 啟用攔截器
clawmetry.track.set_source("support-agent")   # 為此產品命名

# ...你的代理照常執行;每次 LLM 呼叫現在都會被追蹤 + 歸屬。
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每次呼叫標記一個**具名來源**,因此你執行的每個產品都會在儀表板 Overview 頁的**🔌 迴圈外來源**卡片中,以獨立、可歸屬成本的項目呈現——每個代理的呼叫數、供應商、延遲、錯誤率一目了然。若未設定來源?呼叫仍會被追蹤,只是該卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所使用的是同一個資料層(DuckDB → 雲端快照),因此迴圈外來源會與其他一切一樣同步到雲端儀表板,並採端對端加密。

## OpenTelemetry — 廠商中立,將你的追蹤資料送到任何地方

ClawMetry 使用 **GenAI 語意慣例**,雙向支援 **OpenTelemetry**,因此你的代理追蹤資料永遠不會被鎖定在單一工具中。

**匯出**每個工作階段——LLM 呼叫、工具、子代理、代幣、成本——以 OTLP/HTTP GenAI span 的形式,送往任何收集器(Datadog、Grafana、Honeycomb 或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 等效寫法:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔皆為可選環境變數:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 額外的 HTTP 標頭
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒數(預設 60)
```

**擷取** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接收來自其他任何來源的追蹤與指標資料(如需 protobuf 擷取,請執行 `pip install clawmetry[otel]`)。

你可以同時擁有零設定、本地優先的 ClawMetry 儀表板,**以及**將資料送進團隊已在使用的任何後端,無綁定,也不必額外安裝第二個代理。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、工作階段與排程任務。

若你確實需要自訂:

```bash
clawmetry --port 9000              # 自訂連接埠(預設:8900)
clawmetry --host 127.0.0.1         # 僅綁定至 localhost
clawmetry --workspace ~/mybot      # 自訂工作區路徑
clawmetry --name "Alice"           # Flow 視覺化中顯示你的名稱
```

所有選項:`clawmetry --help`

## 支援的頻道

ClawMetry 會為你設定的每個 OpenClaw 頻道顯示即時活動。只有在你的 `openclaw.json` 中實際設定過的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點擊 Flow 中的任何頻道節點,即可看到即時聊天氣泡檢視,顯示進出訊息的計數。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計資料、10 秒重新整理 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 伺服器 + 頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 工作區 + 頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁介面工作階段 |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只呈現你實際設定過的頻道,無需手動設定。

## Docker 部署

想在容器中執行 ClawMetry?沒問題!🐳

**使用 Docker 快速開始:**

```bash
# 建置映像檔
docker build -t clawmetry .

# 以預設設定執行
docker run -p 8900:8900 clawmetry

# 或掛載你代理的資料目錄(範例:OpenClaw 的 ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose 範例:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **注意:** 在 Docker 中執行時,請掛載你代理的資料 + 日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能自動偵測你的設定。

## 需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上的 AI 代理執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n 或 Antigravity(Docker 則需掛載對應目錄)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw)——NVIDIA 為 OpenClaw 打造的企業級安全包裝層,可在沙盒化的 OpenShell 容器中執行代理。

多數情況下不需要額外設定。同步守護程序會自動探索工作階段檔案,無論它們位於主機上的 `~/.openclaw/`,還是在 OpenShell 容器內部。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查是否存在 `nemoclaw` CLI,並執行 `nemoclaw status` 取得沙盒資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,再透過磁碟區掛載或 `docker cp` 讀取工作階段

從 NemoClaw 容器同步而來的工作階段檔案,會在雲端儀表板中標記 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你能一眼分辨它們與標準 OpenClaw 工作階段的差異。

### 建議設定:在主機上執行同步守護程序

為獲得最佳體驗,請在**主機**上執行 ClawMetry 的同步守護程序(而非在沙盒內)。這樣可避免 NemoClaw 網路政策的限制。

```bash
# 在主機上(沙盒外)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守護程序會自動在任何執行中的 OpenShell 容器內找到工作階段。

### 選用:明確指定沙盒名稱

若自動偵測未成功,可指定正確的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒內執行(進階)

若你必須在 OpenShell 沙盒**內部**執行同步守護程序,請在你的 NemoClaw 網路政策中加入以下出站規則,使其能連線至 ClawMetry 擷取 API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

套用方式:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 連接埠與端點

| 端點 | 連接埠 | 通訊協定 | 是否必要 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步守護程序 → 雲端) |
| `localhost:8900` | 8900 | HTTP | 是(本地儀表板介面) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器工作階段探索 |

同步守護程序只會對 `ingest.clawmetry.com` 發出出站 HTTPS 呼叫,不需要任何入站連接埠。

---

## 雲端部署

請參見 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**,了解 SSH 通道、反向代理與 Docker 相關內容。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會將匿名的安裝生命週期回報,傳送至
`https://app.clawmetry.com/api/install`:第一次在新機器上執行
`clawmetry` CLI 時傳送一次 `install` 回報,升級到新版本後首次執行時傳送一次
`update` 回報,完成儀表板內的引導選擇時傳送一次 `onboarded`
回報。我們用這些資料統計真實安裝數(原始 PyPI 下載數字約有 98% 來自鏡像站、CI
與自動更新的重複下載),並了解實際使用中的代理框架與版本。

**每個生命週期事件、每個版本最多發送一次 POST**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;在你明確連接 Cloud 同步之前保持匿名(之後已驗證的守護程序心跳會攜帶此 ID,將此次安裝與你的帳號連結) |
| `event` | `install` / `update` / `onboarded` | 全新安裝 vs 既有安裝的升級 |
| `version` | `0.12.167` | 掌握實際使用中的版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我們接下來該整合哪些代理 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真人安裝與 CI 雜訊 |

**我們不會傳送的內容**:IP(雲端會從請求中於伺服器端推導出國碼,之後即捨棄該
IP)、主機名稱、使用者名稱、工作區路徑、檔案內容、你的 api_key、你的電子郵件,
以及任何個人身分資訊或工作區相關資訊。傳輸內容可於
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式即可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # 僅限當前 shell
export DO_NOT_TRACK=1                          # W3C 跨工具標準
touch ~/.clawmetry/notelemetry                 # 持久性檔案標記
```

網路故障不會阻擋 `clawmetry` 的執行——該回報是在背景執行緒上以「發送後不管」的
方式進行,逾時時間為 3 秒。

## Star 歷史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 授權條款

MIT

---

<p align="center">
  <strong>🦞 看見你的代理在想什麼</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系的一部分</sub>
</p>
