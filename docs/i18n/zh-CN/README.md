<!-- i18n-src:c422fb7dd0da -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看清你的智能体在想什么。** 面向 **20 种 AI 智能体运行时**的实时可观测性工具：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 16 种。一个仪表盘,管理你的整个智能体舰队。

> 🌐 **多语言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令,零配置,自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开,即可完成。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 20 种智能体运行时

ClawMetry 最初是为 OpenClaw 打造的可观测性工具,如今已能在同一个仪表盘中计量你的**整个智能体舰队**,自动检测你机器上的每一种运行时:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw 和 NemoClaw 在开源应用中免费提供;其他运行时则需要通过 ClawMetry Cloud 或自托管的 Pro 许可证解锁。可以从页头切换运行时,每个标签页(成本、Token、工具、追踪)都会重新聚焦到该运行时。具体的免费/付费划分、层级对照表、`/api/entitlement` 的数据结构以及 `clawmetry license` CLI,详见 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能获得什么

- **Flow** —— 动态流程图,实时展示消息在渠道、大脑、工具之间往返流转
- **Overview** —— 健康检查、活动热力图、会话计数、模型信息
- **Usage** —— 按日/周/月分解的 Token 与成本追踪
- **Sessions** —— 活跃的智能体会话,包含模型、Token、最后活动时间
- **Crons** —— 定时任务,包含状态、下次运行时间、耗时
- **Logs** —— 彩色标注的实时日志流
- **Memory** —— 浏览 SOUL.md、MEMORY.md、AGENTS.md、每日笔记
- **Transcripts** —— 用聊天气泡界面阅读会话历史
- **Alerts** —— 预算上限、错误率触发、智能体离线检测;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** —— 将危险的删除操作、强制推送、数据库变更、sudo、包安装、网络调用挡在一键签核之后

## 截图

### 🧠 Brain —— 智能体事件实时流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview —— Token 使用与会话汇总
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow —— 实时工具调用信息流
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens —— 按模型和会话拆分成本
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory —— 工作区文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security —— 安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts —— 预算上限、错误率触发,以及到 Slack / Discord / PagerDuty / Email 的 Webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals —— 将高风险工具调用挡在人工签核之后;基于策略的保护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**面向 Claude Code 的预执行拦截** —— 一条命令即可安装
PreToolUse 钩子,在匹配的工具调用*实际执行前*将其暂停,并等待你的决定(启用
[云端推送通知](https://app.clawmetry.com/push) 后,手机一点即可完成):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒绝只会拦截那一次工具调用,智能体会保留其会话并可以尝试其他方案。在手机上批准会跳过 Claude Code 自身的
权限提示(你已经回答过了)。未匹配的工具大约耗费 40ms,随后回落到 Claude Code
正常的权限流程。当 Claude Code 本身在等待你处理时,你也会收到手机推送
(`permission_prompt` / `idle_prompt` 通知)。

## 安装

**一行命令(推荐):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**从源码安装:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 前端开发

v2 版 React 应用位于 `frontend/`,当 Flask 服务器以启用 v2 的方式启动时,
会在 `/v2` 路径下提供服务。

开发时请使用两个终端:

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

打开 `http://localhost:5173/v2/`。Vite 会将 `/api` 请求代理到
`http://localhost:8900`,因此 React 应用无需额外的 CORS 配置即可与本地
Flask 服务器通信。

构建随 Python 包一起发布的产物包:

```bash
cd frontend
npm run build
```

生产环境的构建产物会写入 `clawmetry/static/v2/dist/`。

## 运行时 / 智能体兼容性

ClawMetry 观测的不仅是 OpenClaw,还有许多 AI 智能体运行时。每个非 OpenClaw 的运行时都配有专用的读取适配器,负责将其原生的会话格式转换为 ClawMetry 的统一数据结构;守护进程会将它们摄入同一个 DuckDB 存储和云端快照中,并打上运行时标签,Session replay 标签页在检测到多种运行时同时存在时会显示**运行时切换器**。完整对照表和运行时接入指南见 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族的入门介绍见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

正在使用 [Perplexity 的 numbat](https://github.com/perplexityai/numbat) 智能体安全工具?ClawMetry 开箱即可摄入它的检测结果和执行决策,详见 [`docs/NUMBAT.md`](docs/NUMBAT.md)。

| 运行时 / 智能体 | 状态 | 说明 |
|---|---|---|
| **OpenClaw** | 原生支持 | 参考运行时,自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。会话记录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 按会话存储的 SQLite(`data/v2-sessions`)。会话记录 + 消息计数。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。会话记录、模型、Token/成本。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。会话记录、模型、工具调用 + 思考过程、Token 用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。会话记录、模型、工具调用、Token 用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。聊天/composer 会话记录、模型。 |
| **Aider** | Beta 适配器 | 每个项目一个 `.aider.chat.history.md`。会话记录、模型、Token 计数。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。会话记录、模型、工具调用、Token 总量。 |
| **opencode** | Beta 适配器 | SQLite `~/.local/share/opencode`。会话记录、模型、工具调用、Token + 成本。 |
| **Qwen Code** | Beta 适配器 | JSONL `~/.qwen/projects/.../chats`。会话记录、模型、工具调用、Token 用量。 |
| **Pi** | Beta 适配器 | JSONL `~/.pi/agent/sessions`。会话记录、模型、工具调用、Token + 成本。 |
| **Deep Agents** | Beta 适配器 | SQLite `~/.deepagents/.state/sessions.db`。会话记录、模型、工具调用、Token + 成本。 |
| **n8n** | Beta 适配器 | SQLite `~/.n8n/database.sqlite`。工作流执行、节点运行、AI Agent 提示词,以及 n8n 有记录时的模型 + Token。 |
| **Antigravity** | Beta 适配器 | `~/.gemini/<flavor>/brain/` 下的 Brain JSONL。对话、工具步骤、思考过程、按每次生成拆分的 Gemini Token 及成本、后台生成消耗。 |
| **GitHub Copilot** | Beta 适配器 | Copilot CLI 的 `events.jsonl`(位于 `~/.copilot/session-state/`)+ `session-store.db` 中按调用记录的用量台账。对话、工具调用、模型路由、区分缓存的 Token 拆分、按供应商计费的 AI 额度成本。 |
| **Grok** | Beta 适配器 | xAI Grok Build CLI(`~/.grok/bin/grok` 下的 Rust 二进制文件):全局事件日志 `~/.grok/logs/unified.jsonl` + 按会话的 `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`。对话、按轮次拆分的 Token、模型路由,以及暂存在 `~/.grok/upload_queue/` 下的 CLI 出站仓库负载,方便你查看有哪些内容离开了你的机器。 |

"Beta 适配器"意味着 ClawMetry 为该运行时真实的磁盘存储格式提供了读取器,每一个都基于真实机器上的真实安装构建并验证过(参见 `tests/fixtures/runtimes/<rt>/`)。适配器均为只读;每个适配器都如实反映其运行时实际存储了什么(例如 PicoClaw/NanoClaw/Cursor 并不会把 Token 成本写入磁盘)。当一个节点上运行多个运行时时,运行时切换器会将会话视图聚焦到某一个,便于专注排查。

## 追踪任意 SDK 智能体 —— loop 外的成本归因

以上这些运行时都会将会话写入磁盘。而你自己的**生产级智能体**——无论是基于 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 构建的,还是一个纯粹的 `httpx` 循环——却不会。ClawMetry 的零配置拦截器依然能够捕获它的 LLM 调用(成本、Token、延迟、错误),方式是对 `httpx`/`requests` 进行猴子补丁:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或环境变量 `CLAWMETRY_SOURCE=support-agent`)会给每次调用打上一个**命名来源**标签,这样你运行的每个产品都会作为独立的、可归因成本的条目出现在仪表盘 Overview 页面的 **🔌 Out-loop sources** 卡片中——每个智能体的调用数、供应商、延迟、错误率一目了然。没有设置来源?调用依然会被追踪,只是卡片会保持隐藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

这与运行时适配器所使用的数据层完全相同(DuckDB → 云端快照),因此 out-loop 来源会像其他数据一样端到端加密同步到云端仪表盘。

## OpenTelemetry —— 厂商中立,追踪数据可发送到任意地方

ClawMetry 在收发两个方向都支持 **OpenTelemetry**,并使用 **GenAI 语义约定**,因此你的智能体追踪数据永远不会被锁定在单一工具中。

**导出**每个会话——LLM 调用、工具、子智能体、Token、成本——以 OTLP/HTTP GenAI span 的形式导出到任意采集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证请求头和轮询间隔为可选的环境变量:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**摄入** —— 内置的 OTLP 接收器可以在 `/v1/traces`、`/v1/logs`、`/v1/metrics` 上接收来自任何其他系统的追踪、日志和指标数据。将任何具备 OpenTelemetry 埋点的应用指向它即可:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON 格式的追踪和日志在普通 `pip install clawmetry` 下即可使用,无需额外依赖。Protobuf 摄入(以及 OTLP/JSON 格式的指标)则需要 `pip install clawmetry[otel]`。设置了自己 `service.name` 的应用会在运行时切换器中作为独立的智能体出现,拥有自己的成本和 Token 数据。

你既能获得零配置、本地优先的 ClawMetry 仪表盘,**又**能将数据同步到你团队已经在用的任何后端,没有锁定,也不需要安装第二个智能体。

## 配置

大多数人不需要任何配置。ClawMetry 会自动检测你的工作区、日志、会话和定时任务。

如果确实需要自定义:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有选项:`clawmetry --help`

## 支持的渠道

ClawMetry 会为你已配置的每个 OpenClaw 渠道显示实时活动。只有在你的 `openclaw.json` 中实际配置过的渠道才会出现在 Flow 图中,未配置的渠道会自动隐藏。

点击 Flow 图中的任意渠道节点即可查看实时聊天气泡视图,包含收发消息计数。

| 渠道 | 状态 | 实时弹窗 | 说明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支持 | ✅ | 消息、统计数据,10 秒刷新一次 |
| 💬 **iMessage** | ✅ 完整支持 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支持 | ✅ | 通过 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支持 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完整支持 | ✅ | 服务器 + 频道检测 |
| 🟪 **Slack** | ✅ 完整支持 | ✅ | 工作区 + 频道检测 |
| 🌐 **Webchat** | ✅ 完整支持 | ✅ | 内置网页 UI 会话 |
| 📡 **IRC** | ✅ 完整支持 | ✅ | 终端风格的气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完整支持 | ✅ | 通过 BlueBubbles REST API 实现 iMessage |
| 🔵 **Google Chat** | ✅ 完整支持 | ✅ | 通过 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支持 | ✅ | 通过 Teams 机器人插件 |
| 🔷 **Mattermost** | ✅ 完整支持 | ✅ | 自托管团队聊天工具 |
| 🟩 **Matrix** | ✅ 完整支持 | ✅ | 去中心化,支持端到端加密 |
| 🟢 **LINE** | ✅ 完整支持 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支持 | ✅ | 去中心化 NIP-04 私信 |
| 🟣 **Twitch** | ✅ 完整支持 | ✅ | 通过 IRC 连接实现聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整支持 | ✅ | WebSocket 事件订阅 |
| 🔵 **Zalo** | ✅ 完整支持 | ✅ | Zalo Bot API |

> **自动检测:** ClawMetry 会读取你的 `~/.openclaw/openclaw.json`,只渲染你实际配置过的渠道,无需手动设置。

## Docker 部署

想在容器中运行 ClawMetry?没问题!🐳

**使用 Docker 快速开始:**

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

**Docker Compose 示例:**

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

> **注意:** 在 Docker 中运行时,请挂载你的智能体的数据和日志目录(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),以便 ClawMetry 能自动检测你的配置。

## 环境要求

- Python 3.8+
- Flask(通过 pip 自动安装)
- 同一台机器上运行的 AI 智能体运行时:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity、GitHub Copilot、Grok 或 QM(在 Docker 中则为挂载的数据卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 会自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw) —— NVIDIA 为 OpenClaw 打造的企业级安全封装层,在沙盒化的 OpenShell 容器中运行智能体。

大多数情况下无需额外配置。无论会话文件位于宿主机的 `~/.openclaw/` 还是 OpenShell 容器内部,同步守护进程都会自动发现它们。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw:

1. **二进制检测** —— 检查是否存在 `nemoclaw` CLI,并运行 `nemoclaw status` 获取沙盒信息
2. **容器检测** —— 扫描运行中的 Docker 容器,查找包含 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 的镜像,然后通过卷挂载或 `docker cp` 读取会话数据

从 NemoClaw 容器同步的会话文件,在云端仪表盘中会被打上 `runtime=nemoclaw` 和 `container_id` 元数据标签,让你一眼就能将它们与标准的 OpenClaw 会话区分开来。

### 推荐配置:在宿主机上运行同步守护进程

为获得最佳体验,请在**宿主机**(而非沙盒内部)运行 ClawMetry 的同步守护进程。这样可以避开 NemoClaw 的网络策略限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程会自动查找任何运行中的 OpenShell 容器内的会话数据。

### 可选:显式指定沙盒名称

如果自动检测未生效,可以指定 ClawMetry 应使用的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒内部运行(进阶用法)

如果你必须在 OpenShell 沙盒**内部**运行同步守护进程,请在你的 NemoClaw 网络策略中添加以下出站规则,使其能够访问 ClawMetry 的接收 API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

使用以下命令应用配置:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 端口与端点

| 端点 | 端口 | 协议 | 是否必需 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步守护进程 → 云端) |
| `localhost:8900` | 8900 | HTTP | 是(本地仪表盘 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用于容器会话发现 |

同步守护进程只会向 `ingest.clawmetry.com` 发起出站 HTTPS 调用,不需要任何入站端口。

---

## 云端部署

有关 SSH 隧道、反向代理和 Docker 的说明,请参见 **[云端测试指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目使用 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测

ClawMetry 会向 `https://app.clawmetry.com/api/install` 发送匿名的安装生命周期
数据:首次在新机器上运行 `clawmetry` CLI 时发送一次 `install` 数据,
升级到新版本后首次运行时发送一次 `update` 数据,完成仪表盘内的引导选择时
发送一次 `onboarded` 数据。我们借此统计真实的安装量(原始的 PyPI 下载
数字约 98% 来自镜像、CI 和自动更新的重复下载),并了解实际使用中有哪些
智能体框架和版本。

**每个生命周期事件、每个版本最多发送一次 POST**,内容包括:

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储在 `~/.clawmetry/install_id` 的随机 UUID | 去重;在你显式连接 Cloud 同步之前保持匿名(此后经过身份验证的守护进程心跳会携带它,将此次安装与你的账户关联) |
| `event` | `install` / `update` / `onboarded` | 区分全新安装与现有安装的升级 |
| `version` | `0.12.167` | 了解实际使用中的版本分布 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支持优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我们接下来应该集成哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 将人工安装与 CI 噪音区分开 |

**我们不会发送的内容**:IP(云端会在服务端根据请求推导国家代码,随后
丢弃该 IP)、主机名、用户名、工作区路径、文件内容、你的 api_key、你的
邮箱,以及任何 PII 或与工作区相关的信息。完整的传输负载可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审查。

**退出遥测**(以下任意一种方式即可永久禁用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

网络故障不会阻塞 `clawmetry` 的运行,遥测请求在守护线程上以“发送后不等待
结果”的方式执行,超时时间为 3 秒。

## Star 历史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 许可证

MIT

---

<p align="center">
  <strong>🦞 看清你的智能体在想什么</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 构建 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生态系统的一部分</sub>
</p>
