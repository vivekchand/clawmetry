<!-- i18n-src:8252f6b1d31d -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的智能體如何思考。** 為 **14 種 AI 智能體執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex，以及其他 10 種。一個儀表板，掌握你整個智能體艦隊。

> 🌐 **閱讀其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟,就這麼簡單。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種智能體執行環境

ClawMetry 一開始是為 OpenClaw 打造的可觀測性工具,現在已能在同一個儀表板中計量你**整個智能體艦隊**,並自動偵測機器上的每一種執行環境:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw 和 NemoClaw 在開源版應用中免費使用;其他執行環境則需透過 ClawMetry Cloud 或自架的 Pro 授權才能啟用。從頁首切換執行環境後,每個分頁(成本、代幣、工具、追蹤軌跡)都會重新聚焦到該執行環境。確切的免費/付費劃分、方案矩陣、`/api/entitlement` 的資料結構,以及 `clawmetry license` CLI,請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow(流程)** — 即時動態圖表,顯示訊息如何流經頻道、大腦、工具再返回
- **Overview(總覽)** — 健康檢查、活動熱力圖、工作階段數量、模型資訊
- **Usage(用量)** — 依日/週/月分項的代幣與成本追蹤
- **Sessions(工作階段)** — 顯示模型、代幣數、最後活動時間的進行中智能體工作階段
- **Crons(排程任務)** — 顯示狀態、下次執行時間、耗時的排程工作
- **Logs(日誌)** — 彩色即時日誌串流
- **Memory(記憶)** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts(對話紀錄)** — 以聊天氣泡介面閱讀工作階段歷史
- **Alerts(警報)** — 預算上限、錯誤率觸發、智能體離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals(核准)** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫等操作攔截在一鍵簽核之後

## 螢幕截圖

### 🧠 Brain — 即時智能體事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — 代幣用量與工作階段摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與工作階段拆分成本
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核日誌
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、透過 webhook 通知 Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫攔截在人工簽核之後;由政策驅動的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的預先執行攔截** — 一行指令即可安裝 PreToolUse
hook,在符合條件的工具呼叫**執行前**先暫停,並等待你的決定(開啟
[雲端推播通知](https://app.clawmetry.com/push)後,手機上點一下即可):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕(deny)只會擋下那一次工具呼叫,智能體仍保有工作階段,可以嘗試其他做法。在手機上核准會略過 Claude Code 自身的權限提示(你已經回答過了)。未符合規則的工具呼叫大約多耗費 40ms,並會回落至 Claude Code 原本的權限流程。當 Claude Code 本身在等你回應時(`permission_prompt` / `idle_prompt` 通知),你也會收到手機推播。

## 安裝

**一行指令安裝(推薦):**
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

v2 React 應用程式位於 `frontend/`,當 Flask 伺服器以啟用 v2 的方式
啟動時,會在 `/v2` 路徑提供服務。

開發時請開啟兩個終端機:

```bash
# 終端機 1:Flask API/伺服器,監聽 :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 終端機 2:Vite 開發伺服器,監聽 :5173
cd frontend
nvm use
npm ci
npm run dev
```

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理至
`http://localhost:8900`,讓 React 應用程式無需額外的 CORS 設定即可
與本機 Flask 伺服器通訊。

若要建置隨 Python 套件一併發佈的打包檔:

```bash
cd frontend
npm run build
```

正式版打包檔會輸出至 `clawmetry/static/v2/dist/`。

## 執行環境 / 智能體相容性

ClawMetry 觀察許多 AI 智能體執行環境,不只是 OpenClaw。每個非 OpenClaw 的執行環境都有專屬的讀取轉接器(reader adapter),負責將其原生的工作階段格式轉換成 ClawMetry 的統一資料結構;背景守護行程會將這些資料匯入同一個 DuckDB 儲存庫與雲端快照,並標記執行環境類型,當偵測到一種以上的執行環境時,Session replay 分頁會顯示**執行環境切換器**。完整的相容性矩陣與新增執行環境的指南請見 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族的入門介紹請見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 執行環境 / 智能體 | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化的 `providers.Message` JSONL 格式(`~/.picoclaw/workspace/sessions`)。含對話紀錄、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個工作階段一個 SQLite 檔(`data/v2-sessions`)。含對話紀錄與訊息數量。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。含對話紀錄、模型、代幣數/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。含對話紀錄、模型、工具呼叫與思考過程、代幣用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。含對話紀錄、模型、工具呼叫、代幣用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。含聊天/composer 對話紀錄、模型。 |
| **Aider** | Beta 轉接器 | 每個專案一份 `.aider.chat.history.md`。含對話紀錄、模型、代幣計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。含對話紀錄、模型、工具呼叫、代幣總計。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。含對話紀錄、模型、工具呼叫、代幣數與成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。含對話紀錄、模型、工具呼叫、代幣用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。含對話紀錄、模型、工具呼叫、代幣數與成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。含對話紀錄、模型、工具呼叫、代幣數與成本。 |
| **n8n** | Beta 轉接器 | SQLite `~/.n8n/database.sqlite`。含工作流程執行紀錄、節點執行、AI Agent 提示詞,以及 n8n 有記錄時的模型與代幣數。 |

「Beta 轉接器」代表 ClawMetry 針對該執行環境實際的磁碟格式提供了讀取器,每一個都是針對真實機器上的真實安裝進行建置與驗證的(參見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀,並且如實反映各執行環境實際儲存的內容(例如 PicoClaw/NanoClaw/Cursor 並不會把代幣成本寫入磁碟)。當同一節點上執行多種執行環境時,執行環境切換器可將工作階段檢視範圍限縮到單一環境,方便深入檢視。

## 追蹤任何 SDK 智能體 — 迴圈外成本歸因

上述執行環境都會將工作階段寫入磁碟。但你自己建置的**正式環境智能體**——不論是用 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,還是單純的 `httpx` 迴圈打造的——並不會這麼做。ClawMetry 的零設定攔截器仍可透過對 `httpx`/`requests` 進行 monkey-patch,擷取其 LLM 呼叫(成本、代幣數、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每次呼叫標記一個**命名來源**,讓你執行的每個產品都能在儀表板 Overview 頁的 **🔌 迴圈外來源** 卡片中,顯示為獨立、可歸因成本的項目——按智能體顯示呼叫數、供應商、延遲、錯誤率。若未設定來源?呼叫仍會被追蹤,只是該卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所使用的資料層相同(DuckDB → 雲端快照),因此迴圈外來源會與其他資料一樣同步至雲端儀表板,並採端對端加密。

## OpenTelemetry — 供應商中立,把追蹤軌跡送到任何地方

ClawMetry 在雙向都支援 **OpenTelemetry**,並使用 **GenAI 語意慣例**,因此你的智能體追蹤軌跡不會被鎖定在單一工具中。

**匯出**每個工作階段——LLM 呼叫、工具、子智能體、代幣、成本——以 OTLP/HTTP GenAI span 的形式送至任何收集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔為選填的環境變數:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**接收** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接收來自其他任何系統的追蹤軌跡與指標(protobuf 接收需 `pip install clawmetry[otel]`)。

你可以同時擁有零設定、本機優先的 ClawMetry 儀表板,**以及**團隊現有後端中的資料——沒有廠商鎖定,也不需要安裝第二個智能體。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、工作階段與排程任務。

若你確實需要自訂:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項:`clawmetry --help`

## 支援的頻道

ClawMetry 會顯示你已設定的每個 OpenClaw 頻道的即時活動。只有在你的 `openclaw.json` 中實際設定的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點擊 Flow 圖表中的任一頻道節點,即可查看即時聊天氣泡畫面,包含收到/送出的訊息數量。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計資料、10 秒重新整理 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 伺服器 + 頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 工作區 + 頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁介面的工作階段 |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格的氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 使用 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams 機器人外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天室 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只顯示你實際設定的頻道,無需手動設定。

## Docker 部署

想在容器中執行 ClawMetry?沒問題!🐳

**使用 Docker 快速開始:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
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

> **注意:** 在 Docker 中執行時,請掛載你智能體的資料與日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能自動偵測你的設定。

## 系統需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上的 AI 智能體執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents,或 n8n(或 Docker 掛載的資料卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw) —— NVIDIA 為 OpenClaw 打造的企業級安全封裝層,可在受沙盒隔離的 OpenShell 容器中執行智能體。

大多數情況下不需要額外設定。同步守護行程會自動找到工作階段檔案,無論它們位於主機的 `~/.openclaw/` 還是 OpenShell 容器內部。

### 運作方式

ClawMetry 以兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查 `nemoclaw` CLI 是否存在,並執行 `nemoclaw status` 取得沙盒資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,再透過資料卷掛載或 `docker cp` 讀取工作階段

從 NemoClaw 容器同步的工作階段檔案,在雲端儀表板中會標記 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你一眼就能與標準 OpenClaw 工作階段區分開來。

### 建議設定:在主機上執行同步守護行程

為獲得最佳體驗,請在**主機**(而非沙盒內部)執行 ClawMetry 的同步守護行程。這樣可以避免受到 NemoClaw 網路政策的限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守護行程會自動找到任何執行中 OpenShell 容器內的工作階段。

### 選用:明確指定沙盒名稱

若自動偵測未生效,可指定正確的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒內執行(進階用法)

若你必須在 OpenShell 沙盒**內部**執行同步守護行程,請在 NemoClaw 網路政策中加入以下對外連線規則,讓它能連線到 ClawMetry 的接收 API:

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
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步守護行程 → 雲端) |
| `localhost:8900` | 8900 | HTTP | 是(本機儀表板介面) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器工作階段偵測 |

同步守護行程只會對 `ingest.clawmetry.com` 發出對外 HTTPS 呼叫,不需要任何對內連接埠。

---

## 雲端部署

SSH 通道、反向代理與 Docker 相關內容請參閱 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會向
`https://app.clawmetry.com/api/install` 傳送匿名的安裝生命週期回報:第一次在新機器上執行 `clawmetry`
CLI 時會傳送一次 `install` 回報,升級到新版本後第一次執行會傳送一次
`update` 回報,完成儀表板內的引導選擇後會傳送一次 `onboarded`
回報。我們用這些資料統計真實安裝數(原始 PyPI 下載數字中約 98% 是鏡像站、CI 與自動更新造成的重複下載),並瞭解實際使用中的智能體框架與版本。

**每個生命週期事件、每個版本最多只會送出一次 POST 請求**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;在你明確連結雲端同步之前皆為匿名(之後,已驗證的守護行程心跳會攜帶此值,將此次安裝與你的帳號連結起來) |
| `event` | `install` / `update` / `onboarded` | 全新安裝或既有安裝的升級 |
| `version` | `0.12.167` | 瞭解實際使用中的版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援的優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 判斷接下來該整合哪些智能體 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真人安裝與 CI 雜訊 |

**我們不會傳送**:IP(雲端會在伺服器端從請求推導出國碼,隨後即捨棄該 IP)、主機名稱、使用者名稱、工作區路徑、檔案內容、你的 api_key、你的電子郵件,以及任何個資或工作區專屬資訊。傳輸的資料格式可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式即可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

若網路請求失敗,絕不會阻礙 `clawmetry` 正常運作——此回報是在背景執行緒上以
fire-and-forget 方式傳送,並設有 3 秒逾時。

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
  <strong>🦞 看見你的智能體如何思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系的一部分</sub>
</p>
