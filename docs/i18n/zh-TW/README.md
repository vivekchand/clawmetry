<!-- i18n-src:9a05336fbdc1 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的代理思考。** 為 **14 種 AI 代理執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及其他 10 種。一個儀表板管理你整個代理艦隊。

> 🌐 **其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

會在 **http://localhost:8900** 開啟,就這麼簡單。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種代理執行環境

ClawMetry 最初是為 OpenClaw 打造的可觀測性工具,如今能在一個儀表板中量測你**整個代理艦隊**,並自動偵測你機器上的每個執行環境:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw 與 NemoClaw 在開源應用中免費提供;其他執行環境需要透過 ClawMetry Cloud 或自架的 Pro 授權才能啟用。從頁首切換執行環境,每個分頁(成本、代幣、工具、追蹤)都會重新對應到該執行環境的範圍。確切的免費/付費劃分、方案矩陣、`/api/entitlement` 的資料結構,以及 `clawmetry license` CLI,請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow** — 即時動畫圖表,顯示訊息如何在頻道、大腦、工具之間流動並返回
- **Overview** — 健康檢查、活動熱力圖、工作階段計數、模型資訊
- **Usage** — 代幣與成本追蹤,含每日/每週/每月的細分統計
- **Sessions** — 顯示模型、代幣、最後活動時間的進行中代理工作階段
- **Crons** — 排程工作,含狀態、下次執行時間、耗時
- **Logs** — 彩色標示的即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 用於閱讀工作階段紀錄的聊天氣泡介面
- **Alerts** — 預算上限、錯誤率觸發、代理離線偵測;可轉發至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫等操作,封鎖在一鍵核准之後

## 螢幕截圖

### 🧠 Brain — 即時代理事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — 代幣使用量與工作階段摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態消息
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與工作階段劃分的成本明細
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核紀錄
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、發送至 Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫封鎖在人工核准之後;政策支援的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前攔截** — 一個指令即可安裝
PreToolUse 掛鉤,能在符合條件的工具呼叫*執行前*暫停它,並等待
你的決定(啟用[雲端推播通知](https://app.clawmetry.com/push)後,手機上一次點擊即可完成):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕只會封鎖那一次工具呼叫,代理仍會保留其工作階段,並可嘗試
其他做法。在手機上核准會跳過 Claude Code 自身的
權限提示(你已經回答過了)。未符合條件的工具大約只花費 40 毫秒,
就會轉入 Claude Code 正常的權限流程。當 Claude Code 本身正等待你的回應時
(`permission_prompt` / `idle_prompt` 通知),你也會收到手機推播。

## 安裝

**一行指令(建議做法):**
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
伺服器以啟用 v2 的方式啟動時,會提供於 `/v2` 路徑。

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
`http://localhost:8900`,因此 React 應用程式無需額外的 CORS 設定
即可與本機 Flask 伺服器溝通。

若要建置與 Python 套件一同發佈的組件包:

```bash
cd frontend
npm run build
```

正式版組件包會輸出至 `clawmetry/static/v2/dist/`。

## 執行環境 / 代理相容性

ClawMetry 觀察多種 AI 代理執行環境,不僅限於 OpenClaw。每個非 OpenClaw 的執行環境都配有專屬的讀取適配器,將其原生的工作階段格式轉換為 ClawMetry 的統一結構;daemon 會將這些資料匯入同一個 DuckDB 儲存區與雲端快照,並標記所屬執行環境,當偵測到一個以上的執行環境時,Session replay 分頁會顯示**執行環境切換器**。完整對照表與新增執行環境的指南請見 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族入門介紹請見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 執行環境 / 代理 | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 適配器 | 扁平的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。含逐字稿、模型、工具呼叫。 |
| **NanoClaw** | Beta 適配器 | 每個工作階段一個 SQLite 檔案(`data/v2-sessions`)。含逐字稿與訊息計數。 |
| **Hermes** | Beta 適配器 | SQLite `~/.hermes/state.db`。含逐字稿、模型、代幣/成本。 |
| **Claude Code** | Beta 適配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。含逐字稿、模型、工具呼叫與思考過程、代幣使用量。 |
| **Codex** | Beta 適配器 | Rollout JSONL `~/.codex/sessions/...`。含逐字稿、模型、工具呼叫、代幣使用量。 |
| **Cursor** | Beta 適配器 | SQLite `state.vscdb`。含聊天/合成器逐字稿、模型。 |
| **Aider** | Beta 適配器 | 每個專案一份 `.aider.chat.history.md`。含逐字稿、模型、代幣計數。 |
| **Goose** | Beta 適配器 | SQLite `~/.local/share/goose`。含逐字稿、模型、工具呼叫、代幣總計。 |
| **opencode** | Beta 適配器 | SQLite `~/.local/share/opencode`。含逐字稿、模型、工具呼叫、代幣與成本。 |
| **Qwen Code** | Beta 適配器 | JSONL `~/.qwen/projects/.../chats`。含逐字稿、模型、工具呼叫、代幣使用量。 |
| **Pi** | Beta 適配器 | JSONL `~/.pi/agent/sessions`。含逐字稿、模型、工具呼叫、代幣與成本。 |
| **Deep Agents** | Beta 適配器 | SQLite `~/.deepagents/.state/sessions.db`。含逐字稿、模型、工具呼叫、代幣與成本。 |
| **n8n** | Beta 適配器 | SQLite `~/.n8n/database.sqlite`。含工作流程執行紀錄、節點執行、AI Agent 提示,以及 n8n 有記錄時的模型與代幣資訊。 |

「Beta 適配器」代表 ClawMetry 為該執行環境的真實磁碟格式提供了讀取器,每一個都在真實機器上以真實安裝進行建置與驗證(參見 `tests/fixtures/runtimes/<rt>/`)。適配器均為唯讀,並且會誠實反映該執行環境實際儲存的內容(例如 PicoClaw/NanoClaw/Cursor 並不會將代幣成本寫入磁碟)。當同一節點上執行多個執行環境時,執行環境切換器可將工作階段檢視範圍鎖定在單一環境,方便深入查看。

## 追蹤任何 SDK 代理 — 環外(out-loop)成本歸因

上述的執行環境都會將工作階段寫入磁碟。而你自己的**正式環境代理**——不論是用 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 建置,還是一個普通的 `httpx` 迴圈——並不會這麼做。ClawMetry 的零設定攔截器仍能透過對 `httpx`/`requests` 進行猴子修補(monkey-patching),擷取其 LLM 呼叫(成本、代幣、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每次呼叫標記一個**命名來源**,因此你執行的每個產品都會在儀表板 Overview 分頁的**🔌 環外來源**卡片中,以獨立、可歸因成本的方式呈現——每個代理的呼叫數、供應商、延遲、錯誤率。若未設定來源,呼叫仍會被追蹤,只是該卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境適配器所使用的資料層相同(DuckDB → 雲端快照),因此環外來源會與其他資料一樣,以端對端加密方式同步至雲端儀表板。

## OpenTelemetry — 廠商中立,將你的追蹤資料送到任何地方

ClawMetry 使用 **GenAI 語意慣例**,在雙向都支援 **OpenTelemetry**,因此你的代理追蹤資料絕不會被鎖定在單一工具中。

**匯出**每個工作階段——LLM 呼叫、工具、子代理、代幣、成本——以 OTLP/HTTP GenAI span 格式,傳送至任何收集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

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

**擷取** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接受來自其他任何來源的追蹤與指標資料(protobuf 擷取需執行 `pip install clawmetry[otel]`)。

你將同時擁有零設定、本機優先的 ClawMetry 儀表板,**以及**你的資料在團隊已在使用的任何後端中——沒有鎖定,也不需要再安裝第二個代理。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、工作階段與排程工作。

若確實需要自訂:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項:`clawmetry --help`

## 支援的頻道

ClawMetry 會顯示你設定的每個 OpenClaw 頻道的即時活動。只有實際在 `openclaw.json` 中設定過的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點擊 Flow 中的任何頻道節點,即可看到即時聊天氣泡檢視,包含收發訊息計數。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計資料,每 10 秒刷新 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 支援伺服器與頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 支援工作區與頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁介面工作階段 |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格的氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 支援 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhooks |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架的團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援端對端加密 |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只呈現你實際設定過的頻道。無需手動設定。

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

> **注意:** 在 Docker 中執行時,請掛載你代理的資料與日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),以便 ClawMetry 自動偵測你的設定。

## 需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上的 AI 代理執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents 或 n8n(Docker 情況下則為已掛載的儲存卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw)——NVIDIA 為 OpenClaw 打造的企業級安全包裝層,可在受沙盒隔離的 OpenShell 容器中執行代理。

大多數情況下不需要額外設定。sync daemon 會自動探索工作階段檔案,無論它們位於主機上的 `~/.openclaw/`,還是 OpenShell 容器內部。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查是否存在 `nemoclaw` CLI,並執行 `nemoclaw status` 取得沙盒資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,再透過儲存卷掛載或 `docker cp` 讀取工作階段

從 NemoClaw 容器同步的工作階段檔案,在雲端儀表板中會被標記 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你能一眼將它們與標準 OpenClaw 工作階段區分開來。

### 建議設定:sync daemon 在主機上執行

為獲得最佳體驗,請在**主機**上(而非沙盒內)執行 ClawMetry 的 sync daemon。這樣可避免觸發 NemoClaw 的網路政策限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon 會自動在任何執行中的 OpenShell 容器內尋找工作階段。

### 選用:明確指定沙盒名稱

若自動偵測未能運作,可指定 ClawMetry 要使用的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒內執行(進階)

若你必須在 OpenShell 沙盒**內部**執行 sync daemon,請在 NemoClaw 網路政策中加入以下出站規則,使其能連線至 ClawMetry 的擷取 API:

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
| `ingest.clawmetry.com` | 443 | HTTPS | 是(sync daemon → 雲端) |
| `localhost:8900` | 8900 | HTTP | 是(本機儀表板介面) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器工作階段探索 |

sync daemon 只會向 `ingest.clawmetry.com` 發出出站 HTTPS 呼叫,不需要任何入站連接埠。

---

## 雲端部署

SSH 通道、反向代理與 Docker 相關內容,請參閱**[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會在你第一次於新機器上執行
`clawmetry` CLI 時,傳送一則匿名的「首次執行」訊號至
`https://app.clawmetry.com/api/install`。我們藉此統計安裝次數(這是我們作為開源專案唯一擁有的行銷指標),並瞭解使用者已安裝了哪些代理框架。

**每次安裝恰好一次 POST 請求**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;不會與你的電子郵件或 api_key 連結 |
| `version` | `0.12.167` | 瞭解目前流通中的版本分佈 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 決定我們下一步該整合哪些代理 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 將人為安裝與 CI 雜訊區分開來 |

**我們不會傳送的內容**:IP 位址(雲端會在伺服器端從請求中推導出國家代碼,之後即捨棄該 IP)、主機名稱、使用者名稱、工作區路徑、檔案內容、你的 api_key、你的電子郵件,以及任何個資或工作區相關資訊。傳輸的資料內容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式皆可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

若此處發生網路失敗,絕不會阻擋 `clawmetry` 正常執行——這則
訊號是在背景執行緒上以「盡力而為、逾時 3 秒」的方式傳送。

## Star 歷史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 授權

MIT

---

<p align="center">
  <strong>🦞 看見你的代理思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系的一部分</sub>
</p>
