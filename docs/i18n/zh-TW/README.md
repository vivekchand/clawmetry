<!-- i18n-src:7cfb63716507 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 agent 如何思考。** 為 **14 種 AI agent 運行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及其他 10 種。一個儀表板，掌握你整個 agent 艦隊。

> 🌐 **以下語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟，就這麼簡單。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 14 種 agent 運行環境

ClawMetry 一開始是為 OpenClaw 打造的可觀測性工具，現在則能在單一儀表板中計量你**整個 agent 艦隊**,並自動偵測你機器上的每個運行環境：

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw 和 NemoClaw 在開源應用程式中免費提供；其他運行環境則需要透過 ClawMetry Cloud 或自架的 Pro 授權來啟用。從頁首切換運行環境,每個分頁(成本、tokens、工具、追蹤紀錄)都會重新對應到該運行環境。確切的免費/付費劃分、方案矩陣、`/api/entitlement` 格式,以及 `clawmetry license` CLI,請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你將獲得什麼

- **Flow** — 即時動畫圖表,顯示訊息如何流經 channels、brain、工具,再流回來
- **Overview** — 健康檢查、活動熱度圖、session 數量、模型資訊
- **Usage** — Token 與成本追蹤,提供日/週/月的分項統計
- **Sessions** — 使用中的 agent sessions,包含模型、tokens、最後活動時間
- **Crons** — 排程工作,包含狀態、下次執行時間、執行時長
- **Logs** — 顏色標示的即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 聊天氣泡介面,用於閱讀 session 歷史紀錄
- **Alerts** — 預算上限、錯誤率觸發、agent 離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫,統一放在一鍵核准的關卡後面

## 螢幕截圖

### 🧠 Brain — 即時 agent 事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 用量與 session 摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與 session 分類的成本明細
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核紀錄
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發、Webhook 通知至 Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將高風險工具呼叫放在人工核准後面;採用政策驅動的保護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前攔截** — 一行指令即可安裝
PreToolUse hook,能在符合條件的工具呼叫*執行前*暫停,並等待
你的決定(開啟[雲端推播通知](https://app.clawmetry.com/push)後,手機上點一下即可完成):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕只會擋下那一次工具呼叫,agent 仍會保留其 session,並可以
嘗試其他做法。在手機上核准會略過 Claude Code 本身的
權限提示(你已經回答過了)。未符合規則的工具呼叫大約多花 ~40ms,
並會回落到 Claude Code 原本的權限流程。當 Claude Code 本身正在等你回應時
(`permission_prompt` / `idle_prompt` 通知),你也會收到手機推播。

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
伺服器以啟用 v2 的方式啟動時,會提供於 `/v2`。

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
即可與本機 Flask 伺服器通訊。

若要建置隨 Python 套件一起發行的 bundle:

```bash
cd frontend
npm run build
```

正式版 bundle 會寫入 `clawmetry/static/v2/dist/`。

## 運行環境 / Agent 相容性

ClawMetry 觀測許多 AI agent 運行環境,不僅限於 OpenClaw。每個非 OpenClaw 的運行環境都配有一個專用的讀取轉接器,將其原生的 session 格式轉譯為 ClawMetry 的統一格式;daemon 會將這些資料匯入同一個 DuckDB 儲存區 + 雲端快照,並標記其運行環境,而 Session replay 分頁在偵測到一種以上的運行環境時,會顯示**運行環境切換器**。完整矩陣以及新增運行環境的指南,請參閱 [`docs/compatibility.md`](docs/compatibility.md);OpenClaw 家族的入門介紹請參閱 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

正在使用 [Perplexity 的 numbat](https://github.com/perplexityai/numbat) agent 安全工具嗎?ClawMetry 開箱即可擷取其偵測結果與執行決策 — 詳見 [`docs/NUMBAT.md`](docs/NUMBAT.md)。

| 運行環境 / Agent | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考運行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。Transcripts、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個 session 一個 SQLite(`data/v2-sessions`)。Transcripts + 訊息計數。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。Transcripts、模型、tokens/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。Transcripts、模型、工具呼叫 + 思考過程、token 用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。Transcripts、模型、工具呼叫、token 用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。Chat/composer transcripts、模型。 |
| **Aider** | Beta 轉接器 | 每個專案一個 `.aider.chat.history.md`。Transcripts、模型、token 計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。Transcripts、模型、工具呼叫、token 總計。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。Transcripts、模型、工具呼叫、tokens + 成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。Transcripts、模型、工具呼叫、token 用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。Transcripts、模型、工具呼叫、tokens + 成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。Transcripts、模型、工具呼叫、tokens + 成本。 |
| **n8n** | Beta 轉接器 | SQLite `~/.n8n/database.sqlite`。工作流程執行、節點執行、AI Agent 提示詞,以及 n8n 有記錄時的模型 + tokens。 |
| **Antigravity** | Beta 轉接器 | 位於 `~/.gemini/<flavor>/brain/` 下的 Brain JSONL。對話、工具步驟、思考過程、每次生成的 Gemini token 分項 + 成本、背景生成的耗用量。 |
| **GitHub Copilot** | Beta 轉接器 | Copilot CLI 的 `events.jsonl`(位於 `~/.copilot/session-state/`)+ `session-store.db` 每次呼叫的用量帳本。對話、工具呼叫、模型路由、快取感知的 token 分項、供應商計費的 AI credit 成本。 |
| **Grok** | Beta 轉接器 | xAI Grok Build CLI(位於 `~/.grok/bin/grok` 的 Rust 執行檔):全域事件日誌 `~/.grok/logs/unified.jsonl` + 每個 session 的 `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`。對話、每輪 token 分項、模型路由,以及暫存於 `~/.grok/upload_queue/` 的 CLI 對外儲存庫傳送內容,讓你能看到有哪些資料離開你的機器。 |

「Beta 轉接器」意指 ClawMetry 為該運行環境的實際磁碟格式提供讀取器,每一個都在真實機器上針對真實安裝進行建置與驗證(見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀;每個轉接器都誠實反映其運行環境實際儲存的內容(例如 PicoClaw/NanoClaw/Cursor 並不會將 token 成本寫入磁碟)。當一個節點上執行多種運行環境時,運行環境切換器會將 sessions 檢視範圍限定在其中一個,方便進行深入研究。

## 追蹤任何 SDK agent — 圈外成本歸因

以上這些運行環境都會將 sessions 寫入磁碟。而你自己的**正式環境 agent** — 也就是你用 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,或是純 `httpx` 迴圈打造的那個 — 並不會這麼做。ClawMetry 的零設定攔截器仍能透過對 `httpx`/`requests` 進行 monkey-patching 來擷取其 LLM 呼叫(成本、tokens、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每次呼叫標記一個**命名來源**,因此你執行的每個產品都會在儀表板 Overview 頁面的 **🔌 圈外來源** 卡片中,以獨立的、可歸因成本的項目呈現 — 顯示每個 agent 的呼叫次數、供應商、延遲、錯誤率。若未設定來源?呼叫仍會被追蹤,只是該卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與運行環境轉接器所使用的資料層相同(DuckDB → 雲端快照),因此圈外來源會與其他所有資料一樣同步至雲端儀表板,並採用端對端加密。

## OpenTelemetry — 供應商中立,將你的追蹤資料送往任何地方

ClawMetry 使用 **GenAI 語意慣例**,在雙向都支援 **OpenTelemetry**,因此你的 agent 追蹤資料絕不會被鎖在單一工具中。

**匯出**每個 session — LLM 呼叫、工具、sub-agents、tokens、成本 — 以 OTLP/HTTP GenAI span 的形式,送往任何收集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔為選擇性的環境變數:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**匯入** — 內建的 OTLP 接收器可在 `/v1/traces` 與 `/v1/metrics` 接收來自任何其他來源的 traces 與 metrics(需要 protobuf 匯入時,執行 `pip install clawmetry[otel]`)。

你將同時擁有零設定、本機優先的 ClawMetry 儀表板,**以及**你的資料在你的團隊已在使用的任何後端中 — 沒有鎖定,也不需要安裝第二個 agent。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、sessions 與 crons。

若你確實需要自訂:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項:`clawmetry --help`

## 支援的 Channels

ClawMetry 會顯示你設定的每個 OpenClaw channel 的即時活動。只有實際在你的 `openclaw.json` 中設定過的 channels 才會出現在 Flow 圖表中 — 未設定的會自動隱藏。

點擊 Flow 中的任一 channel 節點,即可看到即時聊天氣泡檢視,包含收發訊息計數。

| Channel | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計資料,10 秒刷新一次 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | Guild + channel 偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | Workspace + channel 偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁 UI sessions |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格的氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhooks |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天工具 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天室 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只顯示你實際設定過的 channels。無需手動設定。

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

> **注意:** 在 Docker 中執行時,請掛載你 agent 的資料 + 日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能自動偵測你的設定。

## 需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上的 AI agent 運行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity、GitHub Copilot、Grok,或 QM(Docker 情況下則為掛載的資料卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA 為 OpenClaw 打造的企業級安全包裝層,在沙箱化的 OpenShell 容器中執行 agents。

大多數情況下不需要額外設定。無論 session 檔案位於主機上的 `~/.openclaw/`,或在 OpenShell 容器內,sync daemon 都會自動探索它們。

### 運作方式

ClawMetry 透過兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查 `nemoclaw` CLI 是否存在,並執行 `nemoclaw status` 取得沙箱資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,再透過磁碟區掛載或 `docker cp` 讀取 sessions

從 NemoClaw 容器同步的 session 檔案,會在雲端儀表板中標記 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你能一眼區分它們與標準 OpenClaw sessions。

### 建議設定:在主機上執行 sync daemon

為獲得最佳體驗,請在**主機**(而非沙箱內部)執行 ClawMetry 的 sync daemon。這樣可避免 NemoClaw 網路政策的限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon 會自動在任何執行中的 OpenShell 容器內尋找 sessions。

### 選用:指定明確的沙箱名稱

若自動偵測無法運作,可將 ClawMetry 指向正確的沙箱:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱內執行(進階)

若你必須在 OpenShell 沙箱**內部**執行 sync daemon,請在你的 NemoClaw 網路政策中加入以下對外規則,讓它能連上 ClawMetry ingest API:

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
| `localhost:8900` | 8900 | HTTP | 是(本機儀表板 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器 session 探索 |

sync daemon 只會對 `ingest.clawmetry.com` 發出對外 HTTPS 呼叫。不需要任何對內連接埠。

---

## 雲端部署

關於 SSH 通道、反向代理與 Docker,請參閱 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會傳送匿名的安裝生命週期回報至
`https://app.clawmetry.com/api/install`:第一次在新機器上執行
`clawmetry` CLI 時傳送一次 `install` 回報,升級到新版本後第一次
執行時傳送一次 `update` 回報,完成儀表板內的引導選擇時傳送一次
`onboarded` 回報。我們用這些資料來統計真實安裝數(原始 PyPI 下載
數字約有 98% 來自鏡像站、CI 與自動更新的重複下載),並了解實際
使用中的 agent 框架與版本。

**每個生命週期事件、每個版本最多傳送一次 POST 請求**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;在你明確連接 Cloud sync 之前皆為匿名(之後經過驗證的 daemon 心跳會攜帶此資訊,將此安裝與你的帳號連結) |
| `event` | `install` / `update` / `onboarded` | 全新安裝或既有安裝的升級 |
| `version` | `0.12.167` | 了解實際使用中的版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我們接下來該整合哪些 agents |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 區分真實使用者安裝與 CI 雜訊 |

**我們不會傳送的資料**:IP(雲端會在伺服器端從請求推導出國家代碼,
然後捨棄 IP)、主機名稱、使用者名稱、工作區路徑、檔案內容、你的
api_key、你的電子郵件,以及任何 PII 或工作區相關資訊。傳輸的資料
內容可在 [`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式皆可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

網路失敗絕不會阻擋 `clawmetry` 的執行 — 這個回報是在
daemon 執行緒上以「發送後不管」的方式進行,逾時為 3 秒。

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
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生態系的一部分</sub>
</p>
