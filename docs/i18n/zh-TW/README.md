<!-- i18n-src:48548997be76 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 Agent 如何思考。** 支援 **12 種 AI Agent 執行環境**的即時可觀測性儀表板：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及其他 8 種。用一個儀表板管理你的整個 Agent 叢集。

> 🌐 **閱讀其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令，零配置，自動偵測所有環境。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟後即可使用。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 12 種 Agent 執行環境

ClawMetry 最初作為 OpenClaw 的可觀測性工具，現在可在一個儀表板中監測你的**整個 Agent 叢集**，並自動偵測機器上的每種執行環境：

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw 與 NemoClaw 在開源應用程式中免費使用；其他執行環境需搭配 ClawMetry Cloud 或自架 Pro 授權才可啟用。從頁首切換執行環境後，成本、Token、工具、追蹤等所有分頁都會重新套用至該執行環境的資料。

## 功能一覽

- **Flow（流程）** — 即時動態圖，呈現訊息在頻道、大腦、工具之間的流動過程
- **Overview（總覽）** — 健康檢查、活動熱力圖、工作階段數量、模型資訊
- **Usage（用量）** — Token 與費用追蹤，支援每日、每週、每月分解
- **Sessions（工作階段）** — 顯示活躍 Agent 工作階段的模型、Token 及最後活動時間
- **Crons（排程）** — 排程任務的狀態、下次執行時間及持續時間
- **Logs（日誌）** — 彩色即時日誌串流
- **Memory（記憶體）** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md 及每日筆記
- **Transcripts（對話記錄）** — 以聊天氣泡介面閱讀工作階段歷史
- **Alerts（警示）** — 預算上限、錯誤率觸發、Agent 離線偵測；可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals（審核）** — 對破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫設置一鍵確認關卡

## 截圖

### 🧠 Brain — 即時 Agent 事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 用量與工作階段摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與工作階段的費用細分
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核日誌
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、Webhook 整合 Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 對高風險工具呼叫設置手動確認關卡；以政策支援的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## 安裝

**一行指令（推薦）：**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip：**
```bash
pip install clawmetry
clawmetry
```

**從原始碼安裝：**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 前端開發

v2 React 應用程式位於 `frontend/` 目錄，啟用 v2 後可透過 Flask 伺服器的 `/v2` 路徑存取。

開發時請開啟兩個終端機：

```bash
# 終端機 1：Flask API/伺服器，監聽 :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 終端機 2：Vite 開發伺服器，監聽 :5173
cd frontend
nvm use
npm ci
npm run dev
```

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理至 `http://localhost:8900`，讓 React 應用程式無需額外的 CORS 設定即可與本地 Flask 伺服器通訊。

若要建置隨 Python 套件發布的產品包：

```bash
cd frontend
npm run build
```

產品包會輸出至 `clawmetry/static/v2/dist/`。

## 執行環境與 Agent 相容性

ClawMetry 可觀測多種 AI Agent 執行環境，不僅限於 OpenClaw。每個非 OpenClaw 執行環境都有專屬的讀取器轉接器，將其原生工作階段格式轉換為 ClawMetry 的統一資料結構；Daemon 會將其以執行環境標記一起匯入相同的 DuckDB 儲存區及雲端快照，並在存在多個執行環境時，於「工作階段回放」分頁顯示**執行環境切換器**。完整相容性矩陣及新增執行環境的指南請見 [`docs/compatibility.md`](docs/compatibility.md)，OpenClaw 家族入門說明請見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 執行環境 / Agent | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境，自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平式 `providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。支援對話記錄、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個工作階段的 SQLite（`data/v2-sessions`）。支援對話記錄及訊息數量。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。支援對話記錄、模型、Token 與費用。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。支援對話記錄、模型、工具呼叫與思考過程、Token 用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。支援對話記錄、模型、工具呼叫、Token 用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。支援聊天與撰寫器對話記錄、模型。 |
| **Aider** | Beta 轉接器 | 每個專案的 `.aider.chat.history.md`。支援對話記錄、模型、Token 數量。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。支援對話記錄、模型、工具呼叫、Token 總量。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。支援對話記錄、模型、工具呼叫、Token 與費用。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。支援對話記錄、模型、工具呼叫、Token 用量。 |

「Beta 轉接器」表示 ClawMetry 為該執行環境的真實磁碟格式提供了讀取器，每個讀取器均在真實機器的真實安裝環境中建置並驗證（詳見 `tests/fixtures/runtimes/<rt>/`）。轉接器為唯讀；每個轉接器都如實反映其執行環境實際儲存的資料（例如 PicoClaw、NanoClaw、Cursor 不會將 Token 費用寫入磁碟）。當一個節點上同時運行多個執行環境時，執行環境切換器可將工作階段視圖限定在單一執行環境，便於深入分析。

## 追蹤任意 SDK Agent — 迴圈外費用歸因

上述執行環境均會將工作階段寫入磁碟。你自行建置的**生產 Agent**，無論是基於 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 或純粹的 `httpx` 迴圈，都不會這樣做。ClawMetry 的零配置攔截器透過對 `httpx`、`requests` 進行 monkey-patching，仍可捕捉其 LLM 呼叫（費用、Token、延遲、錯誤）：

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`（或環境變數 `CLAWMETRY_SOURCE=support-agent`）會為每次呼叫標記一個**命名來源**，讓你運行的每個產品在儀表板總覽的**🔌 迴圈外來源**卡片中顯示為獨立的費用歸因項目，包含呼叫次數、提供者、延遲及每個 Agent 的錯誤率。若未設定來源，呼叫仍會被追蹤，但該卡片不會顯示。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器使用的是同一個資料層（DuckDB 雲端快照），因此迴圈外來源與其他資料同樣會以端對端加密的方式同步至雲端儀表板。

## OpenTelemetry — 廠商中立，資料傳送至任何地方

ClawMetry 雙向支援 **OpenTelemetry**，並使用 **GenAI 語意慣例**，確保你的 Agent 追蹤資料不受限於單一工具。

**匯出**每個工作階段的資料（LLM 呼叫、工具、子 Agent、Token、費用）為 OTLP/HTTP GenAI Span，傳送至任何收集器（Datadog、Grafana、Honeycomb 或你自己的 OTel Collector）：

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔為選用環境變數：

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**匯入** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接受來自任何來源的追蹤與指標（Protobuf 匯入需 `pip install clawmetry[otel]`）。

你可同時擁有零配置、本地優先的 ClawMetry 儀表板，**並且**將資料送往你的團隊已在使用的後端，無廠商鎖定，無需安裝第二個 Agent。

## 設定

大多數使用者不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、工作階段及 cron 排程。

如需自訂設定：

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項：`clawmetry --help`

## 支援的頻道

ClawMetry 會顯示你在 OpenClaw 中已設定的每個頻道的即時活動。只有在你的 `openclaw.json` 中實際設定的頻道才會出現在 Flow 圖中，未設定的頻道會自動隱藏。

點擊 Flow 中的任意頻道節點，即可查看即時的聊天氣泡視圖，顯示傳入及傳出的訊息數量。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整 | ✅ | 訊息、統計資料，每 10 秒重新整理 |
| 💬 **iMessage** | ✅ 完整 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整 | ✅ | 透過 WhatsApp Web（Baileys） |
| 🔵 **Signal** | ✅ 完整 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整 | ✅ | 群組與頻道自動偵測 |
| 🟪 **Slack** | ✅ 完整 | ✅ | 工作區與頻道自動偵測 |
| 🌐 **Webchat** | ✅ 完整 | ✅ | 內建網頁 UI 工作階段 |
| 📡 **IRC** | ✅ 完整 | ✅ | 終端機風格氣泡 UI |
| 🍏 **BlueBubbles** | ✅ 完整 | ✅ | 透過 BlueBubbles REST API 使用 iMessage |
| 🔵 **Google Chat** | ✅ 完整 | ✅ | 透過 Chat API Webhook |
| 🟣 **MS Teams** | ✅ 完整 | ✅ | 透過 Teams Bot 外掛程式 |
| 🔷 **Mattermost** | ✅ 完整 | ✅ | 自架團隊聊天 |
| 🟩 **Matrix** | ✅ 完整 | ✅ | 去中心化，支援端對端加密 |
| 🟢 **LINE** | ✅ 完整 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整 | ✅ | 透過 IRC 連線的聊天室 |
| 🔷 **Feishu/Lark** | ✅ 完整 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整 | ✅ | Zalo Bot API |

> **自動偵測：** ClawMetry 讀取你的 `~/.openclaw/openclaw.json`，只顯示你實際設定的頻道，無需手動設定。

## Docker 部署

想在容器中執行 ClawMetry？沒問題！🐳

**Docker 快速開始：**

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

**Docker Compose 範例：**

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

> **注意：** 在 Docker 中執行時，請掛載你的 Agent 資料與日誌目錄（例如 `~/.openclaw`、`~/.claude`、`~/.codex`），讓 ClawMetry 能自動偵測你的環境設定。

## 系統需求

- Python 3.8 以上
- Flask（透過 pip 自動安裝）
- 同一台機器上需有至少一種 AI Agent 執行環境：OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw 或 PicoClaw（或 Docker 的掛載磁碟區）
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 可自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw)，即 NVIDIA 為 OpenClaw 設計的企業安全包裝器，讓 Agent 在沙箱化的 OpenShell 容器內執行。

大多數情況下無需額外設定。Sync Daemon 無論工作階段檔案存在於主機的 `~/.openclaw/` 或 OpenShell 容器內，均可自動探索。

### 運作原理

ClawMetry 透過兩種方式偵測 NemoClaw：

1. **二進位檔偵測** — 檢查 `nemoclaw` CLI 是否存在，並執行 `nemoclaw status` 取得沙箱資訊
2. **容器偵測** — 掃描執行中的 Docker 容器，尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像，然後透過磁碟區掛載或 `docker cp` 讀取工作階段

從 NemoClaw 容器同步的工作階段檔案會在雲端儀表板中標記 `runtime=nemoclaw` 及 `container_id` 元資料，讓你一眼就能與標準 OpenClaw 工作階段區分。

### 建議設定：在主機上執行 Sync Daemon

為獲得最佳體驗，請在**主機**（而非沙箱內）執行 ClawMetry 的 Sync Daemon，以避免受到 NemoClaw 網路政策限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync Daemon 會自動找到任何執行中的 OpenShell 容器內的工作階段。

### 選用：指定沙箱名稱

若自動偵測無法正常運作，可手動指定正確的沙箱：

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱內執行（進階）

若必須在 OpenShell 沙箱**內部**執行 Sync Daemon，請在你的 NemoClaw 網路政策中新增以下出站規則，讓其能連線至 ClawMetry 的 ingest API：

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

套用方式：

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 連接埠與端點

| 端點 | 連接埠 | 通訊協定 | 是否必要 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是（Sync Daemon 至雲端） |
| `localhost:8900` | 8900 | HTTP | 是（本地儀表板 UI） |
| Docker Socket（`/var/run/docker.sock`） | — | Unix Socket | 用於容器工作階段探索 |

Sync Daemon 僅對 `ingest.clawmetry.com` 發出對外的 HTTPS 呼叫，不需要開放任何對內連接埠。

---

## 雲端部署

SSH 通道、反向代理及 Docker 的相關說明請見 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 在新機器上首次執行 `clawmetry` CLI 時，會向 `https://app.clawmetry.com/api/install` 發送一次匿名的「首次執行」Ping。我們用此統計安裝次數（這是開源專案唯一的行銷指標），並了解使用者安裝了哪些 Agent 框架。

**每次安裝僅發送一次 POST**，內容包含：

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 隨機 UUID，儲存於 `~/.clawmetry/install_id` | 去重；不與你的電子郵件或 api_key 關聯 |
| `version` | `0.12.167` | 了解線上版本分佈 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 了解下一步應整合哪些 Agent |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分人工安裝與 CI 雜訊 |

**我們不會發送**：IP（雲端伺服器端從請求中衍生國碼後即丟棄 IP）、主機名稱、使用者名稱、工作區路徑、檔案內容、你的 api_key、你的電子郵件，以及任何個人識別資訊或工作區相關資料。傳輸的原始內容可在 [`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**退出方式**（以下任一方式均可永久停用）：

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

此處的網路失敗永遠不會阻擋 `clawmetry` 執行，Ping 以「發後不管」的方式在 Daemon 執行緒上執行，逾時為 3 秒。

## 星標歷史

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
  <strong>🦞 看見你的 Agent 如何思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系的一部分</sub>
</p>
