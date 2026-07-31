<!-- i18n-src:02b789586c7d -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的代理思考。** 為 **14 種 AI 代理執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及其他 10 種。一個儀表板掌握你整個代理艦隊。

> 🌐 **閱讀其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多語言 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟,就這麼簡單。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種代理執行環境

ClawMetry 最初是為 OpenClaw 打造的可觀測性工具,現在能在同一個儀表板中計量你**整個代理艦隊**,並自動偵測你機器上的每種執行環境:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw 和 NemoClaw 在開源應用中免費使用;其他執行環境則需要 ClawMetry Cloud 或自架的 Pro 授權才能啟用。從標題列切換執行環境,每個分頁(成本、代幣、工具、追蹤)都會重新聚焦到該執行環境。確切的免費/付費區分、方案矩陣、`/api/entitlement` 結構,以及 `clawmetry license` CLI,請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow** — 即時動畫圖表,顯示訊息如何流經頻道、大腦、工具並返回
- **Overview** — 健康檢查、活動熱力圖、工作階段計數、模型資訊
- **Usage** — 代幣與成本追蹤,包含每日/每週/每月的細項分析
- **Sessions** — 使用中的代理工作階段,顯示模型、代幣、最後活動時間
- **Crons** — 排程工作,包含狀態、下次執行時間、持續時間
- **Logs** — 彩色即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 聊天泡泡介面,用於閱讀工作階段歷史紀錄
- **Alerts** — 預算上限、錯誤率觸發、代理離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫攔截在一鍵核准之前

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

### 🔐 Security — 安全態勢與稽核日誌
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、通往 Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 在手動核准前攔截高風險工具呼叫;由政策支援的防護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前攔截** — 一行指令安裝一個
PreToolUse hook,它會在符合條件的工具呼叫*執行前*暫停並等待
你的決定(啟用[雲端推播通知](https://app.clawmetry.com/push)後,手機輕點一下即可):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕只會阻擋那一次工具呼叫,代理仍保有其工作階段並可以嘗試
其他方法。在手機上核准會跳過 Claude Code 自身的
權限提示(你已經回答過了)。未匹配的工具僅耗費約 40ms,
並會回落到 Claude Code 的一般權限流程。當 Claude Code 本身正在
等待你回應時,你也會收到手機推播(`permission_prompt` /
`idle_prompt` 通知)。

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

開啟 `http://localhost:5173/v2/`。Vite 會將 `/api` 請求代理到
`http://localhost:8900`,因此 React 應用程式無需額外的 CORS 設定
即可與本機 Flask 伺服器通訊。

若要建置隨 Python 套件一起發佈的組合包:

```bash
cd frontend
npm run build
```

正式版組合包會寫入 `clawmetry/static/v2/dist/`。

## 執行環境/代理相容性

ClawMetry 觀察許多 AI 代理執行環境,不只是 OpenClaw。每個非 OpenClaw 的執行環境都配有專屬的讀取器轉接器,將其原生工作階段格式轉換為 ClawMetry 的統一結構;守護程式將它們攝入同一個 DuckDB 儲存庫 + 雲端快照,並標記執行環境,而 Session replay 分頁在存在多個執行環境時會顯示**執行環境切換器**。完整矩陣及新增執行環境的指南請見 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 系列的入門介紹請見 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 執行環境/代理 | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。工作階段紀錄、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個工作階段各自的 SQLite(`data/v2-sessions`)。工作階段紀錄 + 訊息計數。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。工作階段紀錄、模型、代幣/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。工作階段紀錄、模型、工具呼叫 + 思考過程、代幣使用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。工作階段紀錄、模型、工具呼叫、代幣使用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。聊天/編輯器工作階段紀錄、模型。 |
| **Aider** | Beta 轉接器 | 每個專案的 `.aider.chat.history.md`。工作階段紀錄、模型、代幣計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。工作階段紀錄、模型、工具呼叫、代幣總量。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。工作階段紀錄、模型、工具呼叫、代幣 + 成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。工作階段紀錄、模型、工具呼叫、代幣使用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。工作階段紀錄、模型、工具呼叫、代幣 + 成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。工作階段紀錄、模型、工具呼叫、代幣 + 成本。 |
| **n8n** | Beta 轉接器 | SQLite `~/.n8n/database.sqlite`。工作流程執行、節點執行、AI Agent 提示,以及 n8n 有記錄時的模型 + 代幣。 |
| **Antigravity** | Beta 轉接器 | 位於 `~/.gemini/<flavor>/brain/` 下的 Brain JSONL。對話、工具步驟、思考過程、每次生成的 Gemini 代幣拆分 + 成本、背景生成耗用量。 |

「Beta 轉接器」代表 ClawMetry 提供該執行環境真實磁碟格式的讀取器,每一個都是根據真實機器上的真實安裝建置並驗證的(見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀;每一個都如實反映其執行環境實際儲存的內容(例如 PicoClaw/NanoClaw/Cursor 不會將代幣成本寫入磁碟)。當一個節點上執行多個執行環境時,執行環境切換器可將工作階段檢視範圍限定在單一環境,方便深入探究。

## 追蹤任何 SDK 代理 — 環外(out-loop)成本歸因

以上這些執行環境都會將工作階段寫入磁碟。而你自己的**生產環境代理**——不論是你用 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 建構的,或是純粹的 `httpx` 迴圈——並不會這麼做。ClawMetry 的零設定攔截器仍可透過修補 `httpx`/`requests` 來擷取其 LLM 呼叫(成本、代幣、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每個呼叫標記一個**命名來源**,因此你執行的每個產品都會在儀表板 Overview 頁面的**🔌 環外來源**卡片中,以獨立、可歸因成本的項目呈現——每個代理的呼叫數、供應商、延遲、錯誤率。若未設定來源?呼叫仍會被追蹤,只是卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所提供的資料層相同(DuckDB → 雲端快照),因此環外來源會與其他所有資料一樣同步至雲端儀表板,並採端到端加密。

## OpenTelemetry — 廠商中立,將你的追蹤資料送往任何地方

ClawMetry 使用 **GenAI 語意慣例**,在雙向都支援 **OpenTelemetry**,因此你的代理追蹤資料永遠不會被鎖定在單一工具中。

**匯出**每個工作階段——LLM 呼叫、工具、子代理、代幣、成本——以 OTLP/HTTP GenAI span 格式匯出至任何收集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

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

**攝入** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接受來自其他任何來源的追蹤與指標資料(需 protobuf 攝入時請 `pip install clawmetry[otel]`)。

你既能擁有零設定、本地優先的 ClawMetry 儀表板,**又**能將資料送往你的團隊已經在使用的任何後端——沒有鎖定,不需要安裝第二個代理。

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

ClawMetry 會顯示你所設定的每個 OpenClaw 頻道的即時活動。只有實際在你的 `openclaw.json` 中設定的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點擊 Flow 中的任何頻道節點,即可查看即時聊天泡泡檢視,包含收發訊息計數。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計資料,10 秒重新整理一次 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | 伺服器 + 頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | 工作區 + 頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁介面工作階段 |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格泡泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhooks |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛程式 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援端到端加密 |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只呈現你實際設定過的頻道。無需手動設定。

## Docker 部署

想在容器中執行 ClawMetry?沒問題!🐳

**使用 Docker 快速上手:**

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

> **注意:** 在 Docker 中執行時,請掛載你的代理資料 + 日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能夠自動偵測你的設定。

## 需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上的 AI 代理執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n 或 Antigravity(Docker 則需掛載的磁碟區)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA 為 OpenClaw 打造的企業級安全封裝器,可在沙盒化的 OpenShell 容器中執行代理。

大多數情況下不需要額外設定。同步守護程式會自動探索工作階段檔案,不論其位於主機的 `~/.openclaw/` 還是 OpenShell 容器內部。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查 `nemoclaw` CLI 是否存在,並執行 `nemoclaw status` 取得沙盒資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,然後透過磁碟區掛載或 `docker cp` 讀取工作階段

從 NemoClaw 容器同步的工作階段檔案,在雲端儀表板中會標記 `runtime=nemoclaw` 及 `container_id` 中繼資料,讓你能一眼分辨它們與標準 OpenClaw 工作階段的差異。

### 建議設定:在主機上執行同步守護程式

為獲得最佳體驗,請在**主機**(而非沙盒內部)執行 ClawMetry 的同步守護程式。這樣可以避開 NemoClaw 的網路政策限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守護程式會自動在任何執行中的 OpenShell 容器內找到工作階段。

### 選用:明確指定沙盒名稱

若自動偵測無法運作,可指定 ClawMetry 使用正確的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒內部執行(進階)

若你必須在 OpenShell 沙盒**內部**執行同步守護程式,請在 NemoClaw 網路政策中新增以下出站規則,讓它能夠連線至 ClawMetry 攝入 API:

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
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步守護程式 → 雲端) |
| `localhost:8900` | 8900 | HTTP | 是(本機儀表板介面) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器工作階段探索 |

同步守護程式只會對 `ingest.clawmetry.com` 發出出站 HTTPS 呼叫。不需要任何入站連接埠。

---

## 雲端部署

SSH 通道、反向代理與 Docker 相關內容,請參閱 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會向 `https://app.clawmetry.com/api/install` 傳送匿名的
安裝生命週期回報:在新機器上首次執行 `clawmetry` CLI 時傳送一次
`install` 回報,升級到新版本後首次執行時傳送一次
`update` 回報,完成儀表板內的引導選擇時傳送一次
`onboarded` 回報。我們藉此統計實際安裝數(原始 PyPI 下載數字約
98% 來自鏡像站、CI 及自動更新的重複下載),並了解實際使用中的
代理框架與版本。

**每個版本、每種生命週期事件最多傳送一次 POST**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;在你明確連接 Cloud 同步之前保持匿名(之後已驗證的守護程式心跳會攜帶它,將此安裝連結到你的帳號) |
| `event` | `install` / `update` / `onboarded` | 全新安裝 vs. 既有安裝的升級 |
| `version` | `0.12.167` | 實際使用中的版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我們接下來應該整合哪些代理 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真人安裝與 CI 雜訊 |

**我們不會傳送**:IP(雲端會在伺服器端從請求推導出國家代碼,
然後捨棄 IP)、主機名稱、使用者名稱、工作區路徑、檔案內容、
你的 api_key、你的電子郵件,以及任何個人識別資訊或工作區
相關資料。傳輸內容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式即可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

此處的網路失敗永遠不會阻擋 `clawmetry` 執行——
回報是在守護程式執行緒上以「送出即忘」方式進行,逾時為 3 秒。

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
