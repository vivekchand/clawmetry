<!-- i18n-src:c422fb7dd0da -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 agent 如何思考。** 為 **20 種 AI agent 執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex，以及另外 16 種。一個儀表板管理你整個 agent 艦隊。

> 🌐 **閱讀其他語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟，就這麼簡單。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 20 種 agent 執行環境

ClawMetry 最初是為 OpenClaw 打造的可觀測性工具，現在已經能在同一個儀表板中監測你**整個 agent 艦隊**，並自動偵測機器上的每種執行環境：

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw 和 NemoClaw 在開源應用程式中免費使用；其他執行環境需要 ClawMetry Cloud 或自架的 Pro 授權才能啟用。從頁首切換執行環境後,每個分頁(成本、tokens、工具、traces)都會重新聚焦到該執行環境。確切的免費/付費區分、方案比較表、`/api/entitlement` 格式,以及 `clawmetry license` CLI,請參閱 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能獲得什麼

- **Flow** — 動態圖表,即時顯示訊息如何流經頻道、大腦、工具再返回
- **Overview** — 健康檢查、活動熱力圖、session 數量、模型資訊
- **Usage** — token 與成本追蹤,提供每日/每週/每月的細分
- **Sessions** — 使用中的 agent session,顯示模型、tokens、最後活動時間
- **Crons** — 排程工作,顯示狀態、下次執行時間、耗時
- **Logs** — 彩色標示的即時日誌串流
- **Memory** — 瀏覽 SOUL.md、MEMORY.md、AGENTS.md、每日筆記
- **Transcripts** — 聊天氣泡介面,方便閱讀 session 歷史紀錄
- **Alerts** — 預算上限、錯誤率觸發、agent 離線偵測;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 將破壞性刪除、強制推送、資料庫變更、sudo、套件安裝、網路呼叫,擋在一鍵核准之前

## 螢幕截圖

### 🧠 Brain — 即時 agent 事件串流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 使用量與 session 摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 即時工具呼叫動態
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 依模型與 session 細分成本
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作區檔案瀏覽器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全態勢與稽核日誌
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 預算上限、錯誤率觸發,並將 webhook 傳送至 Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 將風險工具呼叫擋在人工簽核之前;由政策支援的防護規則
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code 的執行前攔截** — 一行指令即可安裝
PreToolUse hook,在符合條件的工具呼叫*執行前*暫停,並等待你的決定
(啟用[雲端推播通知](https://app.clawmetry.com/push)後,用手機點一下即可):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒絕只會擋下那一次工具呼叫,agent 仍保有其 session,可以嘗試其他做法。用手機核准會略過 Claude Code 自身的
權限提示(因為你已經回答過了)。未匹配的工具只會多花約 40ms,並會回退到 Claude Code
的一般權限流程。當 Claude Code 本身在等你回應時(`permission_prompt` /
`idle_prompt` 通知),你也會收到手機推播。

## 安裝

**一行指令(建議使用):**
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

v2 React 應用程式位於 `frontend/`,啟用 v2 後,Flask
伺服器會將其服務於 `/v2`。

開發時請開啟兩個終端機:

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

若要建置隨 Python 套件一起發佈的 bundle:

```bash
cd frontend
npm run build
```

正式環境的 bundle 會輸出到 `clawmetry/static/v2/dist/`。

## 執行環境 / Agent 相容性

ClawMetry 觀測許多 AI agent 執行環境,不只是 OpenClaw。每個非 OpenClaw 的執行環境都有專屬的讀取轉接器(reader adapter),將其原生的 session 格式轉換成 ClawMetry 的統一格式;daemon 會將這些資料匯入同一個 DuckDB 儲存庫與雲端快照,並標記所屬執行環境,當偵測到一個以上的執行環境時,Session replay 分頁會顯示**執行環境切換器**。完整比較表與新增執行環境的指南請參閱 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族入門介紹請參閱 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

正在使用 [Perplexity 的 numbat](https://github.com/perplexityai/numbat) agent 安全工具嗎?ClawMetry 開箱即可擷取其偵測結果與強制執行決策——詳見 [`docs/NUMBAT.md`](docs/NUMBAT.md)。

| 執行環境 / Agent | 狀態 | 備註 |
|---|---|---|
| **OpenClaw** | 原生支援 | 參考執行環境,自動偵測 |
| **PicoClaw** | Beta 轉接器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。Transcripts、模型、工具呼叫。 |
| **NanoClaw** | Beta 轉接器 | 每個 session 一份 SQLite(`data/v2-sessions`)。Transcripts + 訊息數量。 |
| **Hermes** | Beta 轉接器 | SQLite `~/.hermes/state.db`。Transcripts、模型、tokens/成本。 |
| **Claude Code** | Beta 轉接器 | JSONL `~/.claude/projects/.../<id>.jsonl`。Transcripts、模型、工具呼叫 + thinking、token 使用量。 |
| **Codex** | Beta 轉接器 | Rollout JSONL `~/.codex/sessions/...`。Transcripts、模型、工具呼叫、token 使用量。 |
| **Cursor** | Beta 轉接器 | SQLite `state.vscdb`。Chat/composer transcripts、模型。 |
| **Aider** | Beta 轉接器 | 每個專案一份 `.aider.chat.history.md`。Transcripts、模型、token 計數。 |
| **Goose** | Beta 轉接器 | SQLite `~/.local/share/goose`。Transcripts、模型、工具呼叫、token 總量。 |
| **opencode** | Beta 轉接器 | SQLite `~/.local/share/opencode`。Transcripts、模型、工具呼叫、tokens + 成本。 |
| **Qwen Code** | Beta 轉接器 | JSONL `~/.qwen/projects/.../chats`。Transcripts、模型、工具呼叫、token 使用量。 |
| **Pi** | Beta 轉接器 | JSONL `~/.pi/agent/sessions`。Transcripts、模型、工具呼叫、tokens + 成本。 |
| **Deep Agents** | Beta 轉接器 | SQLite `~/.deepagents/.state/sessions.db`。Transcripts、模型、工具呼叫、tokens + 成本。 |
| **n8n** | Beta 轉接器 | SQLite `~/.n8n/database.sqlite`。工作流程執行、節點執行、AI Agent 提示,以及 n8n 有紀錄時的模型 + tokens。 |
| **Antigravity** | Beta 轉接器 | Brain JSONL,位於 `~/.gemini/<flavor>/brain/`。對話、工具步驟、thinking、每次生成的 Gemini token 細分 + 成本、背景生成耗用量。 |
| **GitHub Copilot** | Beta 轉接器 | Copilot CLI `events.jsonl`,位於 `~/.copilot/session-state/`,加上 `session-store.db` 每次呼叫的使用量帳本。對話、工具呼叫、模型路由、快取感知的 token 細分、由供應商計費的 AI-credit 成本。 |
| **Grok** | Beta 轉接器 | xAI Grok Build CLI(位於 `~/.grok/bin/grok` 的 Rust 執行檔):全域事件日誌 `~/.grok/logs/unified.jsonl` + 每個 session 的 `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`。對話、每輪 token 細分、模型路由,以及暫存於 `~/.grok/upload_queue/` 的 CLI 外送 repo payload,讓你看見離開你機器的資料。 |

「Beta 轉接器」代表 ClawMetry 提供該執行環境真實磁碟格式的讀取器,且每個都是根據真實機器上的真實安裝建置並驗證的(見 `tests/fixtures/runtimes/<rt>/`)。轉接器皆為唯讀,並且對其執行環境實際儲存的內容如實呈現(例如 PicoClaw/NanoClaw/Cursor 並不會將 token 成本寫入磁碟)。當一個節點上執行多個執行環境時,執行環境切換器可以將 sessions 檢視聚焦到單一環境,方便深入研究。

## 追蹤任何 SDK agent — 迴圈外成本歸因

上述執行環境都會將 session 寫入磁碟。但你自己的**正式環境 agent**——你基於 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,或單純用 `httpx` 寫的迴圈打造的那個——並不會。ClawMetry 的零設定攔截器仍能透過 monkey-patch `httpx`/`requests`,擷取它的 LLM 呼叫(成本、tokens、延遲、錯誤):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 環境變數)會為每次呼叫標記一個**具名來源**,因此你執行的每個產品都會在儀表板 Overview 的 **🔌 迴圈外來源**卡片中,以獨立、可歸因成本的形式顯示——每個 agent 的呼叫數、供應商、延遲、錯誤率。沒有設定來源?呼叫依然會被追蹤,只是卡片會保持隱藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

這與執行環境轉接器所使用的資料層相同(DuckDB → 雲端快照),因此迴圈外來源會與其他一切一樣同步到雲端儀表板,並採端對端加密。

## OpenTelemetry — 供應商中立,將你的 traces 傳送到任何地方

ClawMetry 使用 **GenAI 語意慣例**,雙向支援 **OpenTelemetry**,因此你的 agent traces 永遠不會被鎖在單一工具中。

**匯出**每個 session——LLM 呼叫、工具、子 agent、tokens、成本——以 OTLP/HTTP GenAI spans 的形式送往任何 collector(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

驗證標頭與輪詢間隔為可選的環境變數:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**匯入** — 內建的 OTLP 接收器可在 `/v1/traces`、`/v1/logs`、`/v1/metrics` 接收來自其他任何來源的 traces、logs 與 metrics。將任何已套用 OpenTelemetry 檢測的應用程式指向這裡:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON traces 與 logs 在單純 `pip install clawmetry` 的情況下就能運作,不需要額外套件。Protobuf 匯入(以及 OTLP/JSON metrics)則需要 `pip install clawmetry[otel]`。設定了自己的 `service.name` 的應用程式,會在執行環境切換器中以獨立 agent 的身分出現,並顯示其成本與 tokens。

你可以同時擁有零設定、本機優先的 ClawMetry 儀表板,**以及**你的資料存放在團隊已在使用的任何後端——沒有鎖定,也不需要安裝第二個 agent。

## 設定

大多數人不需要任何設定。ClawMetry 會自動偵測你的工作區、日誌、sessions 與 crons。

如果你確實需要自訂:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有選項:`clawmetry --help`

## 支援的頻道

ClawMetry 會為你設定的每個 OpenClaw 頻道顯示即時活動。只有實際在你的 `openclaw.json` 中設定過的頻道才會出現在 Flow 圖表中,未設定的頻道會自動隱藏。

點選 Flow 中的任一頻道節點,即可看到即時聊天氣泡檢視,顯示收發訊息的數量。

| 頻道 | 狀態 | 即時彈出視窗 | 備註 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支援 | ✅ | 訊息、統計資料,10 秒更新一次 |
| 💬 **iMessage** | ✅ 完整支援 | ✅ | 直接讀取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支援 | ✅ | 透過 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支援 | ✅ | 透過 signal-cli |
| 🟣 **Discord** | ✅ 完整支援 | ✅ | Guild + 頻道偵測 |
| 🟪 **Slack** | ✅ 完整支援 | ✅ | Workspace + 頻道偵測 |
| 🌐 **Webchat** | ✅ 完整支援 | ✅ | 內建網頁介面 session |
| 📡 **IRC** | ✅ 完整支援 | ✅ | 終端機風格的氣泡介面 |
| 🍏 **BlueBubbles** | ✅ 完整支援 | ✅ | 透過 BlueBubbles REST API 支援 iMessage |
| 🔵 **Google Chat** | ✅ 完整支援 | ✅ | 透過 Chat API webhooks |
| 🟣 **MS Teams** | ✅ 完整支援 | ✅ | 透過 Teams bot 外掛 |
| 🔷 **Mattermost** | ✅ 完整支援 | ✅ | 自架團隊聊天 |
| 🟩 **Matrix** | ✅ 完整支援 | ✅ | 去中心化,支援 E2EE |
| 🟢 **LINE** | ✅ 完整支援 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支援 | ✅ | 去中心化 NIP-04 私訊 |
| 🟣 **Twitch** | ✅ 完整支援 | ✅ | 透過 IRC 連線的聊天室 |
| 🔷 **Feishu/Lark** | ✅ 完整支援 | ✅ | WebSocket 事件訂閱 |
| 🔵 **Zalo** | ✅ 完整支援 | ✅ | Zalo Bot API |

> **自動偵測:** ClawMetry 會讀取你的 `~/.openclaw/openclaw.json`,只渲染你實際設定過的頻道。不需要手動設定。

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

> **注意:** 在 Docker 中執行時,請掛載你的 agent 資料 + 日誌目錄(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),讓 ClawMetry 能自動偵測你的設定。

## 系統需求

- Python 3.8+
- Flask(透過 pip 自動安裝)
- 同一台機器上的 AI agent 執行環境:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity、GitHub Copilot、Grok 或 QM(Docker 則需掛載對應的資料卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支援

ClawMetry 會自動偵測 [NemoClaw](https://github.com/NVIDIA/NemoClaw)——NVIDIA 為 OpenClaw 打造的企業級安全包裝器,在受沙箱隔離的 OpenShell 容器中執行 agent。

大多數情況下不需要額外設定。無論 session 檔案位於主機的 `~/.openclaw/` 還是 OpenShell 容器內部,sync daemon 都會自動發現它們。

### 運作方式

ClawMetry 以兩種方式偵測 NemoClaw:

1. **執行檔偵測** — 檢查是否有 `nemoclaw` CLI,並執行 `nemoclaw status` 取得沙箱資訊
2. **容器偵測** — 掃描執行中的 Docker 容器,尋找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 映像檔,再透過卷掛載或 `docker cp` 讀取 session

從 NemoClaw 容器同步的 session 檔案,會在雲端儀表板中標記 `runtime=nemoclaw` 與 `container_id` 中繼資料,讓你能一眼分辨它們與標準 OpenClaw session 的差異。

### 建議設定:在主機上執行 sync daemon

為了獲得最佳體驗,請在**主機**(而非沙箱內部)執行 ClawMetry 的 sync daemon。這樣可以避免 NemoClaw 網路政策的限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon 會自動在任何執行中的 OpenShell 容器內尋找 session。

### 選用:明確指定沙箱名稱

如果自動偵測無法運作,可以指定 ClawMetry 應使用的沙箱:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱內執行(進階)

如果你必須在 OpenShell 沙箱**內部**執行 sync daemon,請在你的 NemoClaw 網路政策中新增以下出站規則,讓它能連上 ClawMetry 的匯入 API:

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
| `localhost:8900` | 8900 | HTTP | 是(本機儀表板 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用於容器 session 探索 |

sync daemon 僅會發出對 `ingest.clawmetry.com` 的出站 HTTPS 呼叫,不需要任何入站連接埠。

---

## 雲端部署

請參閱 **[雲端測試指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**,了解 SSH 通道、反向代理與 Docker 的相關內容。

## 測試

本專案使用 BrowserStack 進行測試。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遙測

ClawMetry 會向
`https://app.clawmetry.com/api/install` 傳送匿名的安裝生命週期 ping:在新機器上第一次
執行 `clawmetry` CLI 時傳送一次 `install` ping,升級到新版本後第一次
執行時傳送一次 `update` ping,以及完成儀表板內的引導選擇時
傳送一次 `onboarded` ping。我們用這個機制來統計真實安裝數
(原始 PyPI 下載數字約有 98% 來自鏡像、CI 與自動更新的重複下載),
並了解實際使用中的 agent 框架與版本。

**每個生命週期事件、每個版本最多只會傳送一次 POST**,內容包含:

| 欄位 | 範例 | 用途 |
|---|---|---|
| `install_id` | 儲存於 `~/.clawmetry/install_id` 的隨機 UUID | 去重複;在你明確連結 Cloud sync 前皆為匿名(之後已驗證的 daemon heartbeat 會攜帶它,將此安裝與你的帳號連結) |
| `event` | `install` / `update` / `onboarded` | 全新安裝或既有安裝的升級 |
| `version` | `0.12.167` | 了解實際使用中的版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支援優先順序 |
| `python` | `3.11.15` | Python 版本支援矩陣 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我們接下來應該整合哪些 agent |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 將人工安裝與 CI 雜訊區分開來 |

**我們不會傳送**:IP(雲端會在伺服器端從請求中推算國碼,
之後即捨棄該 IP)、主機名稱、使用者名稱、工作區
路徑、檔案內容、你的 api_key、你的電子郵件,以及任何個資或
工作區相關資訊。傳輸的 payload 可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中稽核。

**選擇退出**(以下任一方式即可永久停用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

這裡的網路失敗永遠不會阻擋 `clawmetry` 執行——這個
ping 是在 daemon 執行緒上以「發送後不理會」(fire-and-forget)方式進行,逾時為 3 秒。

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
