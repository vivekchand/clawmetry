<!-- i18n-src:bab48eec552f -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 Agent 在思考。** 針對 **14 種 AI Agent 執行環境**提供即時可觀測性:[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及其他 10 種。用一個儀表板管理你整個 agent 艦隊。

> 🌐 **其他語言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令,零設定,自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟後即完成設定。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種 Agent 執行環境

ClawMetry 一開始是為 OpenClaw 打造的可觀測性工具,現在已能在單一儀表板中計量你**整個 agent 艦隊**,並自動偵測機器上的每一種執行環境:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw 與 NemoClaw 在開源版本中免費使用;其他執行環境則需搭配 ClawMetry Cloud 或自架的 Pro 授權才會啟用。可從標頭切換執行環境,每個分頁(成本、token、工具、追蹤)都會重新對應到該執行環境。確切的免費/付費區分、方案矩陣、`/api/entitlement` 資料結構,以及 `clawmetry license` CLI,請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow** — 即時動態圖表,顯示訊息如何在頻道、大腦、工具之間流動並返回
- **Overview** — 健康檢查、活動熱力圖、session 數量、模型資訊
- **Usage** — Token 與成本追蹤,提供日/週/月分類
- **Sessions** — 使用中的 agent session,顯示模型、token、最後活動時間
- **Crons** — 排程工作,顯示狀態、下次執行時間、持續時間
- **Logs** — 彩色標示的即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 對話氣泡介面,方便閱讀 session 歷史紀錄
- **Alerts** — 預算上限、錯誤率觸發、agent 離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫等操作,阻擋在一鍵簽核之後

## 截圖

### 🧠 Brain — 即時 agent 事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 使用量與 session 摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與 session 分類的成本明細
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核日誌
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、Webhook 通知至 Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫阻擋在人工簽核之後;由政策支援的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前阻擋機制** — 一行指令即可安裝
PreToolUse hook,在符合條件的工具呼叫*執行前*先暫停,等候你的決定(啟用
[雲端推播通知](https://app.clawmetry.com/push)後,手機一點即可完成):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕只會阻擋那一次工具呼叫,agent 仍會保留其 session 並可嘗試其他做法。
在手機上核准會跳過 Claude Code 本身的權限提示(因為你已經回答過了)。
未符合條件的工具大約只會多花 40ms,並會回退到 Claude Code 一般的權限流程。
當 Claude Code 本身在等你回應時(`permission_prompt` /
`idle_prompt` 通知),你也會收到手機推播。

## 安裝

**一行指令(建議):**
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

v2 React 應用程式位於 `frontend/`,當 Flask
伺服器以啟用 v2 的方式啟動時,會在 `/v2` 提供服務。

開發時請使用兩個終端機:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理至
`http://localhost:8900`,因此 React 應用程式無需額外設定 CORS
即可與本地 Flask 伺服器通訊。

若要建置隨 Python 套件一併發布的打包檔:

```bash
cd frontend
npm run build
```

正式版打包檔會輸出至 `clawmetry/static/v2/dist/`。

## 執行環境 / Agent 相容性

ClawMetry 可觀測多種 AI agent 執行環境,不僅限於 OpenClaw。每個非 OpenClaw 的執行環境都配有專屬的讀取器轉接器(reader adapter),能將其原生 session 格式轉換為 ClawMetry 的統一資料結構;daemon 會將其匯入同一個 DuckDB 儲存區與雲端快照,並標記對應的執行環境,當偵測到一種以上的執行環境時,Session 重播分頁會顯示**執行環境切換器**。完整對照表與新增執行環境的指南請參閱 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族的入門介紹請參閱 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 執行環境 / Agent | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。支援對話紀錄、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個 session 一個 SQLite(`data/v2-sessions`)。支援對話紀錄與訊息計數。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。支援對話紀錄、模型、token/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。支援對話紀錄、模型、工具呼叫與思考過程、token 使用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。支援對話紀錄、模型、工具呼叫、token 使用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。支援聊天/composer 對話紀錄、模型。 |
| **Aider** | Beta 轉接器 | 每個專案一個 `.aider.chat.history.md`。支援對話紀錄、模型、token 計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。支援對話紀錄、模型、工具呼叫、token 總量。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。支援對話紀錄、模型、工具呼叫、token 與成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。支援對話紀錄、模型、工具呼叫、token 使用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。支援對話紀錄、模型、工具呼叫、token 與成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。支援對話紀錄、模型、工具呼叫、token 與成本。 |

「Beta 轉接器」代表 ClawMetry 為該執行環境的實際磁碟格式提供了讀取器,每一個都經過實機安裝的建置與驗證(參見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀,並且如實反映各執行環境實際儲存的內容(例如 PicoClaw/NanoClaw/Cursor 不會將 token 成本寫入磁碟)。當一個節點上運行多個執行環境時,執行環境切換器可將 session 檢視範圍限定在單一環境,方便深入查看。

## 追蹤任何 SDK Agent — 圈外成本歸因

上述執行環境都會將 session 寫入磁碟。而你自己的**正式環境 agent**——你用 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,或單純的 `httpx` 迴圈打造的那個——並不會這麼做。ClawMetry 的零設定攔截器仍可透過對 `httpx`/`requests` 進行 monkey-patch,擷取它的 LLM 呼叫(成本、token、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每次呼叫標記一個**具名來源**,因此你運行的每個產品都會在儀表板 Overview 的**🔌 圈外來源**卡片中,以獨立、可歸因成本的方式呈現——每個 agent 的呼叫次數、供應商、延遲、錯誤率一目了然。若未設定來源?呼叫仍會被追蹤,只是該卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所使用的是同一套資料層(DuckDB → 雲端快照),因此圈外來源會與其他所有資料一樣,以端對端加密的方式同步至雲端儀表板。

## OpenTelemetry — 廠商中立,將你的追蹤資料傳送至任何地方

ClawMetry 雙向支援 **OpenTelemetry**,採用 **GenAI 語意慣例**,因此你的 agent 追蹤資料永遠不會被鎖定在單一工具內。

**匯出**每個 session——LLM 呼叫、工具、子 agent、token、成本——以 OTLP/HTTP GenAI span 的形式傳送至任何 collector(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認證標頭與輪詢間隔為選用的環境變數:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**接收** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接收來自其他任何來源的追蹤與指標資料(`pip install clawmetry[otel]` 以啟用 protobuf 接收)。

你將同時擁有零設定、本地優先的 ClawMetry 儀表板,**以及**你的資料存放在你團隊已在使用的任何後端——沒有廠商鎖定,也不需要安裝第二個 agent。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、session 與排程工作。

若你確實需要自訂:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項:`clawmetry --help`

## 支援的頻道

ClawMetry 會為你設定的每個 OpenClaw 頻道顯示即時活動。只有在你的 `openclaw.json` 中實際設定的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點擊 Flow 中的任何頻道節點,即可看到即時聊天氣泡檢視,顯示收發訊息數量。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計數據、10 秒刷新 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 伺服器 + 頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 工作區 + 頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁 UI session |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只渲染你實際設定過的頻道,無需手動設定。

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

> **注意:** 在 Docker 中執行時,請掛載你 agent 的資料與日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能自動偵測你的設定。

## 系統需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上安裝的 AI agent 執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi 或 Deep Agents(或 Docker 用的掛載磁碟區)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA 為 OpenClaw 打造的企業級安全封裝器,可在沙盒化的 OpenShell 容器中運行 agent。

多數情況下不需要額外設定。無論 session 檔案位於主機的 `~/.openclaw/`,還是位於 OpenShell 容器內部,sync daemon 都會自動偵測。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw:

1. **二進位檔偵測** — 檢查是否存在 `nemoclaw` CLI,並執行 `nemoclaw status` 取得沙盒資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,接著透過磁碟區掛載或 `docker cp` 讀取 session

從 NemoClaw 容器同步的 session 檔案,會在雲端儀表板中標記 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你能一眼區分它們與標準 OpenClaw session。

### 建議設定:在主機上執行 sync daemon

為獲得最佳體驗,建議在**主機**(而非沙盒內部)執行 ClawMetry 的 sync daemon,以避免受 NemoClaw 網路政策限制影響。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon 會自動尋找任何執行中的 OpenShell 容器內的 session。

### 選用:明確指定沙盒名稱

若自動偵測失效,可指定 ClawMetry 使用正確的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒內執行(進階)

若你必須在 OpenShell 沙盒**內部**執行 sync daemon,請在 NemoClaw 網路政策中加入以下出站規則,讓它能連接到 ClawMetry 的匯入 API:

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

| 端點 | 連接埠 | 協定 | 是否必要 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是(sync daemon → 雲端) |
| `localhost:8900` | 8900 | HTTP | 是(本地儀表板 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器 session 偵測 |

sync daemon 僅會向 `ingest.clawmetry.com` 發出對外 HTTPS 呼叫,不需要任何入站連接埠。

---

## 雲端部署

請參閱 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**,內含 SSH 通道、反向代理與 Docker 相關說明。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會在你第一次於新機器上執行 `clawmetry`
CLI 時,傳送單一次匿名的「首次執行」ping 至
`https://app.clawmetry.com/api/install`。我們用這個來統計安裝次數
(這是我們作為開源專案唯一擁有的行銷指標),並瞭解使用者
安裝了哪些 agent 框架。

**每次安裝僅發送一次 POST**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;不會關聯到你的 email 或 api_key |
| `version` | `0.12.167` | 瞭解實際使用中的版本分佈 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 判斷我們接下來該整合哪些 agent |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真人安裝與 CI 雜訊 |

**我們不會傳送**:IP(雲端會在伺服器端從請求中推導國家代碼,之後即捨棄該 IP)、主機名稱、使用者名稱、工作區路徑、檔案內容、你的 api_key、你的 email,以及任何個資或工作區相關資訊。傳輸內容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式即可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

網路連線失敗絕不會阻擋 `clawmetry` 執行——這個 ping
是在背景執行緒上以「發送後不管」(fire-and-forget)方式進行,逾時時間為 3 秒。

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
  <strong>🦞 看見你的 agent 在思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · 屬於 <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系的一部分</sub>
</p>
