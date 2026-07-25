<!-- i18n-src:8f42d460a973 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 agent 如何思考。** 為 **14 種 AI agent 執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及其他 10 種。一個儀表板，掌握你整個 agent 艦隊。

> 🌐 **閱讀其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

開啟 **http://localhost:8900** 即可完成。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種 agent 執行環境

ClawMetry 一開始是為 OpenClaw 打造的可觀測性工具，如今已能在單一儀表板中計量你的**整個 agent 艦隊**，並自動偵測你機器上的每個執行環境：

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw 與 NemoClaw 在開源應用中免費使用；其他執行環境則需要 ClawMetry Cloud 或自架的 Pro 授權才會啟用。從頁首切換執行環境後，每個分頁（成本、token、工具、追蹤軌跡）都會重新聚焦到該執行環境上。確切的免費／付費區分、方案矩陣、`/api/entitlement` 資料結構，以及 `clawmetry license` CLI，請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能得到什麼

- **Flow** — 即時動畫圖表，顯示訊息如何在頻道、大腦、工具之間流動並返回
- **Overview** — 健康檢查、活動熱力圖、session 數量、模型資訊
- **Usage** — token 與成本追蹤，提供日／週／月分項統計
- **Sessions** — 顯示模型、token、最後活動時間的進行中 agent session
- **Crons** — 排程任務，顯示狀態、下次執行時間、耗時
- **Logs** — 彩色即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 以聊天氣泡介面閱讀 session 歷史紀錄
- **Alerts** — 預算上限、錯誤率觸發、agent 離線偵測；可轉發至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫攔截在單鍵核准之後

## 螢幕截圖

### 🧠 Brain — 即時 agent 事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 用量與 session 摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 按模型與 session 分項的成本明細
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核紀錄
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、Slack／Discord／PagerDuty／Email webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫攔截在手動核准之後；由政策驅動的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## 安裝

**一行指令（建議）：**
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

v2 React 應用程式位於 `frontend/`，在 Flask 伺服器以啟用 v2 的方式啟動時，會於 `/v2` 提供服務。

開發時請使用兩個終端機：

```bash
# 終端機 1：Flask API／伺服器，於 :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 終端機 2：Vite 開發伺服器，於 :5173
cd frontend
nvm use
npm ci
npm run dev
```

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理到 `http://localhost:8900`，因此 React 應用程式無需額外的 CORS 設定即可與本機 Flask 伺服器溝通。

若要建置隨 Python 套件一同發佈的組建：

```bash
cd frontend
npm run build
```

正式版組建會輸出至 `clawmetry/static/v2/dist/`。

## 執行環境／Agent 相容性

ClawMetry 觀測許多 AI agent 執行環境，不僅止於 OpenClaw。每個非 OpenClaw 的執行環境都配有專屬的讀取轉接器，將其原生 session 格式轉譯為 ClawMetry 的統一資料結構；daemon 會將這些資料匯入同一個 DuckDB 儲存庫與雲端快照中，並標記所屬執行環境，當偵測到一個以上的執行環境時，Session 回放分頁會顯示**執行環境切換器**。完整矩陣與新增執行環境的指南請參見 [`docs/compatibility.md`](docs/compatibility.md)，OpenClaw 家族入門介紹請參見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 執行環境／Agent | 狀態 | 說明 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境，自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化的 `providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。支援 Transcripts、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個 session 一份 SQLite（`data/v2-sessions`）。支援 Transcripts 與訊息計數。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。支援 Transcripts、模型、token／成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。支援 Transcripts、模型、工具呼叫與思考過程、token 用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。支援 Transcripts、模型、工具呼叫、token 用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。支援 Chat／Composer Transcripts、模型。 |
| **Aider** | Beta 轉接器 | 每個專案一份 `.aider.chat.history.md`。支援 Transcripts、模型、token 計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。支援 Transcripts、模型、工具呼叫、token 總計。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。支援 Transcripts、模型、工具呼叫、token 與成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。支援 Transcripts、模型、工具呼叫、token 用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。支援 Transcripts、模型、工具呼叫、token 與成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。支援 Transcripts、模型、工具呼叫、token 與成本。 |

「Beta 轉接器」代表 ClawMetry 為該執行環境的實際磁碟格式提供了讀取器，每一款都是根據真實機器上的真實安裝所建置並驗證（見 `tests/fixtures/runtimes/<rt>/`）。轉接器皆為唯讀，並且如實反映該執行環境實際儲存的內容（例如 PicoClaw／NanoClaw／Cursor 並不會將 token 成本寫入磁碟）。當單一節點上運行多個執行環境時，執行環境切換器可將 session 檢視範圍限定在其中一個，方便深入查看。

## 追蹤任何 SDK agent — 迴圈外成本歸因

上述執行環境都會將 session 寫入磁碟。而你自行打造的**正式環境 agent**，也就是那個建構在 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B，或是單純 `httpx` 迴圈上的 agent，並不會這麼做。ClawMetry 的零設定攔截器仍可透過修補（monkey-patch）`httpx`／`requests` 來擷取其 LLM 呼叫（成本、token、延遲、錯誤）：

```python
import clawmetry.track            # 啟用攔截器
clawmetry.track.set_source("support-agent")   # 為此產品命名

# ...你的 agent 照常運行；每一次 LLM 呼叫現在都會被追蹤並歸因。
```

`set_source()`（或 `CLAWMETRY_SOURCE=support-agent` 環境變數）會為每次呼叫標記一個**命名來源**，因此你運行的每個產品都會在儀表板 Overview 的 **🔌 迴圈外來源** 卡片中，以獨立、可歸因成本的項目呈現——每個 agent 的呼叫次數、供應商、延遲、錯誤率一目瞭然。若未設定來源？呼叫依然會被追蹤，只是卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所使用的資料層相同（DuckDB → 雲端快照），因此迴圈外來源會與其他所有資料一樣同步至雲端儀表板，並採端對端加密。

## OpenTelemetry — 供應商中立，將你的追蹤軌跡傳送至任何地方

ClawMetry 使用 **GenAI 語意慣例**，雙向支援 **OpenTelemetry**，因此你的 agent 追蹤軌跡永遠不會被鎖定在單一工具上。

**匯出**每個 session 的資料——LLM 呼叫、工具、子 agent、token、成本——以 OTLP/HTTP GenAI span 的形式傳送至任何收集器（Datadog、Grafana、Honeycomb，或你自己的 OTel Collector）：

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 等效寫法：
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔為選填的環境變數：

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 額外的 HTTP 標頭
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒數（預設 60）
```

**接收**——內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接受來自其他系統的追蹤軌跡與指標（`pip install clawmetry[otel]` 以啟用 protobuf 接收）。

你能同時擁有零設定、本機優先的 ClawMetry 儀表板，**以及**將資料保留在你團隊既有的任何後端——不被鎖定，也不需要再安裝第二個 agent。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、session 與排程任務。

若你確實需要自訂：

```bash
clawmetry --port 9000              # 自訂連接埠（預設：8900）
clawmetry --host 127.0.0.1         # 僅綁定於 localhost
clawmetry --workspace ~/mybot      # 自訂工作區路徑
clawmetry --name "Alice"           # 你在 Flow 視覺化中的名稱
```

所有選項：`clawmetry --help`

## 支援的頻道

ClawMetry 會顯示你所設定的每個 OpenClaw 頻道的即時活動。只有在你的 `openclaw.json` 中實際設定過的頻道，才會顯示在 Flow 圖表中，未設定的頻道會自動隱藏。

點擊 Flow 中的任何頻道節點，即可看到即時聊天氣泡檢視，含收發訊息計數。

| 頻道 | 狀態 | 即時彈出視窗 | 說明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計，每 10 秒更新 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web（Baileys） |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 伺服器與頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 工作區與頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁 UI session |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化，支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天室 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測：** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`，只顯示你實際設定過的頻道，無需手動設定。

## Docker 部署

想在容器中執行 ClawMetry？沒問題！🐳

**使用 Docker 快速上手：**

```bash
# 建置映像檔
docker build -t clawmetry .

# 以預設設定執行
docker run -p 8900:8900 clawmetry

# 或掛載你的 agent 資料目錄（此處以 OpenClaw 的 ~/.openclaw 為例）
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

> **注意：** 在 Docker 中執行時，請掛載你的 agent 資料與日誌目錄（例如 `~/.openclaw`、`~/.claude`、`~/.codex`），讓 ClawMetry 能自動偵測你的設定。

## 系統需求

- Python 3.8+
- Flask（透過 pip 自動安裝）
- 同一台機器上需有一個 AI agent 執行環境：OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi 或 Deep Agents（若使用 Docker，可改為掛載對應磁碟區）
- Linux 或 macOS

## NemoClaw／OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw)，也就是 NVIDIA 為 OpenClaw 打造的企業級安全封裝層，讓 agent 在沙箱化的 OpenShell 容器中執行。

多數情況下無需額外設定。無論 session 檔案位於主機的 `~/.openclaw/` 或是 OpenShell 容器內部，同步 daemon 都能自動發現。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw：

1. **執行檔偵測** — 檢查是否存在 `nemoclaw` CLI，並執行 `nemoclaw status` 取得沙箱資訊
2. **容器偵測** — 掃描執行中的 Docker 容器，尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔，接著透過磁碟區掛載或 `docker cp` 讀取 session

從 NemoClaw 容器同步的 session 檔案，會在雲端儀表板中標記 `runtime=nemoclaw` 及 `container_id` 中繼資料，讓你能一眼分辨出它們與標準 OpenClaw session 的差異。

### 建議設定：在主機上執行同步 daemon

為獲得最佳體驗，請在**主機**（而非沙箱內部）執行 ClawMetry 的同步 daemon，以避免受 NemoClaw 網路政策限制影響。

```bash
# 在主機上（沙箱外部）
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步 daemon 會自動在任何執行中的 OpenShell 容器內尋找 session。

### 選用：明確指定沙箱名稱

若自動偵測未能運作，可指定正確的沙箱給 ClawMetry：

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱內執行（進階）

若你必須在 OpenShell 沙箱**內部**執行同步 daemon，請在你的 NemoClaw 網路政策中加入以下出站規則，讓它能連線至 ClawMetry 的接收 API：

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
| `ingest.clawmetry.com` | 443 | HTTPS | 是（同步 daemon → 雲端） |
| `localhost:8900` | 8900 | HTTP | 是（本機儀表板 UI） |
| Docker socket（`/var/run/docker.sock`） | — | Unix socket | 用於容器 session 發現 |

同步 daemon 只會對 `ingest.clawmetry.com` 發出出站 HTTPS 呼叫，不需要任何入站連接埠。

---

## 雲端部署

請參閱 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**，內含 SSH 通道、反向代理與 Docker 相關說明。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會在你第一次於新機器上執行 `clawmetry` CLI 時，向
`https://app.clawmetry.com/api/install` 傳送單一次匿名的「首次執行」訊號。我們用這個數據來統計安裝次數（這是我們身為開源專案唯一擁有的行銷指標），並了解使用者安裝了哪些 agent 框架。

**每次安裝僅傳送一次 POST**，內容包含：

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複；不會與你的電子郵件或 api_key 產生關聯 |
| `version` | `0.12.167` | 了解實際使用中的版本分佈 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我們接下來應該整合哪些 agent |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真人安裝與 CI 產生的雜訊 |

**我們不會傳送**：IP（雲端會在伺服器端從請求中推算國碼，之後即捨棄該 IP）、主機名稱、使用者名稱、工作區路徑、檔案內容、你的 api_key、你的電子郵件，或任何個資／工作區專屬資訊。傳輸內容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**退出方式**（以下任一種即可永久停用）：

```bash
export CLAWMETRY_NO_TELEMETRY=1                # 僅限當前 shell
export DO_NOT_TRACK=1                          # W3C 跨工具標準
touch ~/.clawmetry/notelemetry                 # 永久性檔案標記
```

網路失敗時絕不會阻擋 `clawmetry` 的執行，此訊號是在背景執行緒中以 3 秒逾時、發送後即忽略結果（fire-and-forget）的方式運作。

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
  <strong>🦞 看見你的 agent 如何思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · 隸屬於 <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系</sub>
</p>
