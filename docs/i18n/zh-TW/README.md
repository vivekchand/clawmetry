<!-- i18n-src:0e34918f8f2e -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 agent 如何思考。** 為 **14 種 AI agent 執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex，以及另外 10 種。一個儀表板,管理你整個 agent 機隊。

> 🌐 **閱讀其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令,零設定,自動偵測所有東西。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟後即可完成。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種 agent 執行環境

ClawMetry 最初是為 OpenClaw 打造的可觀測性工具,現在已能在單一儀表板中為你**整個 agent 機隊**進行計量,並自動偵測你機器上的每一種執行環境:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw 與 NemoClaw 在開源版本中免費使用;其他執行環境則需要 ClawMetry Cloud 或自架的 Pro 授權才能啟用。從頁首切換執行環境後,每個分頁(成本、token、工具、追蹤)都會重新聚焦到該執行環境。確切的免費/付費劃分、方案比較表、`/api/entitlement` 的資料結構,以及 `clawmetry license` CLI,請見 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow** — 即時動畫圖表,顯示訊息在頻道、brain、工具之間流動並返回的過程
- **Overview** — 健康檢查、活動熱力圖、session 數量、模型資訊
- **Usage** — 依日/週/月分類的 token 與成本追蹤
- **Sessions** — 顯示模型、token、最後活動時間的進行中 agent session
- **Crons** — 排程工作及其狀態、下次執行時間、耗時
- **Logs** — 彩色即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 用於閱讀 session 歷史紀錄的聊天氣泡介面
- **Alerts** — 預算上限、錯誤率觸發、agent 離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、force push、資料庫變更、sudo、套件安裝、網路呼叫攔截在一鍵核可之前

## 螢幕截圖

### 🧠 Brain — 即時 agent 事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 使用量與 session 摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與 session 分類的成本明細
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作空間檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核紀錄
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫攔截在人工核可之前;有政策支援的防護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前攔截** — 一行指令即可安裝一個
PreToolUse hook,在符合條件的工具呼叫*執行前*先暫停,並等待
你的決定(啟用[雲端推播通知](https://app.clawmetry.com/push)後,
只需在手機上點一下):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕(deny)只會封鎖那一次工具呼叫,agent 仍保有其 session,可以
嘗試其他做法。在手機上核准會跳過 Claude Code 自身的
權限提示(因為你已經回答過了)。未符合條件的工具只會多花約 40 毫秒,
並會正常進入 Claude Code 原本的權限流程。當 Claude Code 本身在等你回應時
(`permission_prompt` / `idle_prompt` 通知),你也會收到手機推播。

## 安裝

**一行安裝(建議):**
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
伺服器啟動時啟用 v2,就會在 `/v2` 提供服務。

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

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理到
`http://localhost:8900`,因此 React 應用程式可以與本機 Flask 伺服器
溝通,無需額外設定 CORS。

若要建置隨 Python 套件一起發佈的 bundle:

```bash
cd frontend
npm run build
```

正式版 bundle 會輸出到 `clawmetry/static/v2/dist/`。

## 執行環境 / Agent 相容性

ClawMetry 觀測多種 AI agent 執行環境,不只是 OpenClaw。每個非 OpenClaw 的執行環境都配有專屬的讀取轉接器(reader adapter),將其原生的 session 格式轉換為 ClawMetry 統一的資料結構;daemon 會將這些資料匯入同一個 DuckDB 儲存區與雲端快照,並標註對應的執行環境,而 Session replay 分頁在偵測到多於一種執行環境時,會顯示**執行環境切換器**。完整比較表與新增執行環境的指南請見 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族的入門介紹請見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

正在使用 [Perplexity 的 numbat](https://github.com/perplexityai/numbat) agent 安全工具嗎?ClawMetry 開箱即用地擷取其偵測結果與強制執行決策,詳見 [`docs/NUMBAT.md`](docs/NUMBAT.md)。

| 執行環境 / Agent | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。含 Transcript、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個 session 各一個 SQLite(`data/v2-sessions`)。含 Transcript 與訊息計數。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。含 Transcript、模型、token/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。含 Transcript、模型、工具呼叫 + 思考過程、token 使用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。含 Transcript、模型、工具呼叫、token 使用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。含 Chat/composer Transcript、模型。 |
| **Aider** | Beta 轉接器 | 每個專案各一個 `.aider.chat.history.md`。含 Transcript、模型、token 計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。含 Transcript、模型、工具呼叫、token 總計。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。含 Transcript、模型、工具呼叫、token + 成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。含 Transcript、模型、工具呼叫、token 使用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。含 Transcript、模型、工具呼叫、token + 成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。含 Transcript、模型、工具呼叫、token + 成本。 |
| **n8n** | Beta 轉接器 | SQLite `~/.n8n/database.sqlite`。含工作流程執行紀錄、節點執行、AI Agent 提示詞,以及 n8n 有記錄時的模型 + token。 |
| **Antigravity** | Beta 轉接器 | `~/.gemini/<flavor>/brain/` 下的 Brain JSONL。含對話、工具步驟、思考過程、每次生成的 Gemini token 分拆與成本、背景生成的耗用量。 |
| **GitHub Copilot** | Beta 轉接器 | Copilot CLI 的 `~/.copilot/session-state/` 下 `events.jsonl`,加上每次呼叫用量帳本 `session-store.db`。含對話、工具呼叫、模型路由、快取感知的 token 分拆、由供應商計費的 AI 額度成本。 |

「Beta 轉接器」代表 ClawMetry 提供了針對該執行環境真實磁碟格式的讀取器,且每一個都經過在真實機器上實際安裝驗證(見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀,並且如實反映該執行環境實際儲存的內容(例如 PicoClaw/NanoClaw/Cursor 不會將 token 成本寫入磁碟)。當一個節點上執行多種執行環境時,執行環境切換器會將 session 檢視聚焦到單一環境,以便深入查看。

## 追蹤任何 SDK agent — 迴圈外成本歸屬

以上執行環境都會把 session 寫入磁碟。但你自己的**正式環境 agent**——那個用 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,或單純的 `httpx` 迴圈打造的 agent——不會這麼做。ClawMetry 的零設定攔截器仍能透過對 `httpx`/`requests` 進行 monkey-patch,捕捉它的 LLM 呼叫(成本、token、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或環境變數 `CLAWMETRY_SOURCE=support-agent`)會為每次呼叫標註一個**命名來源**,因此你執行的每個產品都會在儀表板 Overview 的 **🔌 迴圈外來源** 卡片中,以獨立、可歸屬成本的項目呈現——每個 agent 的呼叫數、供應商、延遲、錯誤率一目瞭然。若未設定來源?呼叫仍會被追蹤,只是卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所使用的資料層相同(DuckDB → 雲端快照),因此迴圈外來源會與其他所有資料一樣同步到雲端儀表板,並採端對端加密。

## OpenTelemetry — 廠商中立,把追蹤資料送去任何地方

ClawMetry 支援雙向的 **OpenTelemetry**,並使用 **GenAI 語意慣例(semantic conventions)**,因此你的 agent 追蹤資料絕不會被鎖在單一工具中。

**匯出**每個 session 的資料——LLM 呼叫、工具、子 agent、token、成本——以 OTLP/HTTP GenAI span 的形式送往任何 collector(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔為選用的環境變數:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**匯入** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接收來自其他系統的追蹤與指標資料(protobuf 匯入需執行 `pip install clawmetry[otel]`)。

你可以同時擁有零設定、本機優先的 ClawMetry 儀表板,**以及**把資料送到團隊本來就在用的任何後端——沒有鎖定,也不需要再裝第二個 agent。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作空間、日誌、session 與排程工作。

若你確實需要自訂:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項:`clawmetry --help`

## 支援的頻道

只要你在 OpenClaw 中設定好,ClawMetry 就會顯示每個頻道的即時活動。只有在你的 `openclaw.json` 中實際設定的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點擊 Flow 圖表中的任一頻道節點,即可看到即時聊天氣泡檢視,包含進出訊息計數。

| 頻道 | 狀態 | 即時彈窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計數據,每 10 秒更新 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 伺服器 + 頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 工作空間 + 頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁 UI session |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格的氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天室 |
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

> **注意:** 在 Docker 中執行時,請掛載你的 agent 資料與日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能自動偵測你的設定。

## 系統需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上有一個 AI agent 執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity,或 GitHub Copilot(Docker 環境則需掛載對應資料卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw)——NVIDIA 為 OpenClaw 打造的企業級安全包裝器,可在沙箱化的 OpenShell 容器中執行 agent。

大多數情況下不需要額外設定。同步 daemon 會自動探索 session 檔案,無論它們位於主機上的 `~/.openclaw/`,還是在 OpenShell 容器內。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查是否存在 `nemoclaw` CLI,並執行 `nemoclaw status` 取得沙箱資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw`,或 `ghcr.io/nvidia/` 映像檔,再透過卷掛載或 `docker cp` 讀取 session

從 NemoClaw 容器同步的 session 檔案,在雲端儀表板中會被標註 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你一眼就能與標準 OpenClaw session 區分開來。

### 建議設定:在主機上執行同步 daemon

為了獲得最佳體驗,請在**主機**(而非沙箱內)執行 ClawMetry 的同步 daemon。這樣可以避免 NemoClaw 網路政策的限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步 daemon 會自動在任何執行中的 OpenShell 容器內找到 session。

### 選用:明確指定沙箱名稱

若自動偵測未能運作,可指定 ClawMetry 使用正確的沙箱:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱內執行(進階)

若你必須在 OpenShell 沙箱**內部**執行同步 daemon,請在你的 NemoClaw 網路政策中加入以下出站規則,使其能連線至 ClawMetry 的 ingest API:

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
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步 daemon → 雲端) |
| `localhost:8900` | 8900 | HTTP | 是(本機儀表板 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器 session 探索 |

同步 daemon 只會向 `ingest.clawmetry.com` 發出出站的 HTTPS 呼叫,不需要任何入站連接埠。

---

## 雲端部署

SSH 通道、反向代理與 Docker 相關內容請見 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會向
`https://app.clawmetry.com/api/install` 傳送匿名的安裝生命週期回報:第一次在
新機器上執行 `clawmetry` CLI 時傳送一次 `install` 回報,升級到新版本後
第一次執行時傳送一次 `update` 回報,完成儀表板內的引導選項時傳送一次
`onboarded` 回報。我們用這些資料來統計實際安裝數量
(原始的 PyPI 下載數字約有 98% 來自鏡像站、CI 與自動更新的重複下載),
並了解實際被使用的 agent 框架與版本。

**每個生命週期事件、每個版本最多傳送一次 POST**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去除重複;在你明確連接 Cloud 同步之前保持匿名(之後經過驗證的 daemon 心跳會帶上此值,將此次安裝與你的帳號連結) |
| `event` | `install` / `update` / `onboarded` | 全新安裝 vs. 既有安裝的升級 |
| `version` | `0.12.167` | 了解實際流通的版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我們接下來該整合哪些 agent |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真實使用者安裝與 CI 雜訊 |

**我們不會傳送**: IP(雲端會在伺服器端從請求中推導出國家代碼,
之後即捨棄該 IP)、主機名稱、使用者名稱、工作空間路徑、檔案內容、
你的 api_key、你的電子郵件,或任何個人識別資訊 (PII) 或
工作空間專屬資料。傳輸內容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式即可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

即使網路連線失敗,也絕不會阻擋 `clawmetry` 執行——這個
回報是在 daemon 執行緒上以「發送後不理會(fire-and-forget)」方式進行,逾時時間為 3 秒。

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
