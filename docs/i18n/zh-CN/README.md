<!-- i18n-src:9a05336fbdc1 -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体如何思考。** 为 **14 种 AI 智能体运行时**提供实时可观测性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 10 种。一个仪表盘,统揽你的整个智能体舰队。

> 🌐 **阅读其他语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令,零配置,自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开,就这么简单。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 14 种智能体运行时

ClawMetry 最初是为 OpenClaw 打造的可观测性工具,如今已能在一个仪表盘中计量你的**整个智能体舰队**,自动检测你机器上的每一种运行时:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw 和 NemoClaw 在开源应用中免费提供;其余运行时需要通过 ClawMetry Cloud 或自托管的 Pro 许可证解锁。可在页面顶部切换运行时,每个标签页(成本、令牌、工具、追踪)都会重新聚焦到所选运行时。关于免费/付费的具体划分、层级矩阵、`/api/entitlement` 结构以及 `clawmetry license` CLI,请参见 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能获得什么

- **Flow(流程)** —— 实时动态图,展示消息如何流经渠道、大脑、工具并返回
- **Overview(概览)** —— 健康检查、活动热力图、会话计数、模型信息
- **Usage(用量)** —— 按日/周/月细分的令牌与成本跟踪
- **Sessions(会话)** —— 活跃智能体会话,包含模型、令牌数、最近活动
- **Crons(定时任务)** —— 计划任务及其状态、下次运行时间、耗时
- **Logs(日志)** —— 彩色实时日志流
- **Memory(记忆)** —— 浏览 SOUL.md、MEMORY.md、AGENTS.md、每日笔记
- **Transcripts(记录)** —— 聊天气泡界面,用于阅读会话历史
- **Alerts(告警)** —— 预算上限、错误率触发、智能体离线检测;可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals(审批)** —— 将破坏性删除、强制推送、数据库变更、sudo、软件包安装、网络调用置于一键签核之后

## 截图

### 🧠 Brain —— 实时智能体事件流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview —— 令牌用量与会话摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow —— 实时工具调用信息流
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens —— 按模型与会话划分的成本明细
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory —— 工作空间文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security —— 安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts —— 预算上限、错误率触发、通往 Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals —— 将风险工具调用置于人工签核之后;由策略驱动的保护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**面向 Claude Code 的预执行拦截** —— 一条命令即可安装
PreToolUse 钩子,在匹配的工具调用*执行前*将其暂停,等待你的决策(启用
[云端推送通知](https://app.clawmetry.com/push) 后,手机上点一下即可):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

一次拒绝只会拦下这一次工具调用——智能体的会话不受影响,可以尝试其他方案。
在手机上批准会跳过 Claude Code 自身的权限提示(你已经回答过了)。未匹配的
工具调用只会额外耗费约 40ms,并回落到 Claude Code 常规的权限流程。当
Claude Code 本身在等待你的响应时(`permission_prompt` / `idle_prompt`
通知),你同样会收到手机推送。

## 安装

**一键安装(推荐)：**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip：**
```bash
pip install clawmetry
clawmetry
```

**从源码安装：**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 前端开发

v2 版 React 应用位于 `frontend/` 目录,当 Flask 服务器以启用 v2 的方式启动时,
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

生产环境构建产物会写入 `clawmetry/static/v2/dist/`。

## 运行时/智能体兼容性

ClawMetry 观察的不仅是 OpenClaw,还有多种 AI 智能体运行时。每个非 OpenClaw 的运行时都配有专属的读取适配器,负责将其原生会话格式转换为 ClawMetry 的统一结构;守护进程会将这些数据摄取进同一个 DuckDB 存储和云端快照,并标注对应的运行时,当存在一个以上运行时时,Session replay(会话回放)标签页会显示**运行时切换器**。完整对照表及新增运行时的指南请见 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族入门介绍请见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 运行时 / 智能体 | 状态 | 说明 |
|---|---|---|
| **OpenClaw** | 原生支持 | 参考运行时,自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。支持记录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 按会话拆分的 SQLite(`data/v2-sessions`)。支持记录 + 消息计数。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。支持记录、模型、令牌/成本。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。支持记录、模型、工具调用 + 思考过程、令牌用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。支持记录、模型、工具调用、令牌用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。支持聊天/编辑记录、模型。 |
| **Aider** | Beta 适配器 | 每个项目对应的 `.aider.chat.history.md`。支持记录、模型、令牌计数。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。支持记录、模型、工具调用、令牌总量。 |
| **opencode** | Beta 适配器 | SQLite `~/.local/share/opencode`。支持记录、模型、工具调用、令牌 + 成本。 |
| **Qwen Code** | Beta 适配器 | JSONL `~/.qwen/projects/.../chats`。支持记录、模型、工具调用、令牌用量。 |
| **Pi** | Beta 适配器 | JSONL `~/.pi/agent/sessions`。支持记录、模型、工具调用、令牌 + 成本。 |
| **Deep Agents** | Beta 适配器 | SQLite `~/.deepagents/.state/sessions.db`。支持记录、模型、工具调用、令牌 + 成本。 |
| **n8n** | Beta 适配器 | SQLite `~/.n8n/database.sqlite`。工作流执行、节点运行、AI Agent 提示词,以及 n8n 有记录时的模型 + 令牌信息。 |

"Beta 适配器"意味着 ClawMetry 为该运行时真实的磁盘格式提供了读取器,每一个都在真实机器上的真实安装环境中构建并验证过(参见 `tests/fixtures/runtimes/<rt>/`)。适配器均为只读;每一个都会如实反映其运行时实际存储了什么(例如 PicoClaw/NanoClaw/Cursor 并不会把令牌成本写入磁盘)。当一个节点上运行多个运行时时,运行时切换器会将会话视图限定到某一个运行时,便于深入分析。

## 跟踪任意 SDK 智能体 —— 外部环路成本归因

上面提到的运行时都会将会话写入磁盘。而你自己构建的**生产环境智能体**——无论是基于 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,还是一个普通的 `httpx` 循环——并不会这样做。ClawMetry 的零配置拦截器通过对 `httpx`/`requests` 打补丁,依然能够捕获其 LLM 调用(成本、令牌、延迟、错误):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或环境变量 `CLAWMETRY_SOURCE=support-agent`)会为每次调用打上一个**命名来源**标签,这样你运行的每个产品都会在仪表盘 Overview 页面的 **🔌 Out-loop sources(外环来源)** 卡片中,以独立的、可归因成本的一行呈现——每个智能体的调用数、供应商、延迟、错误率一目了然。没有设置来源?调用依然会被跟踪,只是该卡片不会显示。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

这与运行时适配器所使用的数据层相同(DuckDB → 云端快照),因此外环来源会像其他所有数据一样同步到云端仪表盘,并进行端到端加密。

## OpenTelemetry —— 供应商中立,把追踪数据发到任何地方

ClawMetry 使用 **GenAI 语义约定**,双向支持 **OpenTelemetry**,因此你的智能体追踪数据永远不会被锁定在某一个工具里。

将每个会话——LLM 调用、工具、子智能体、令牌、成本——以 OTLP/HTTP GenAI span 的形式**导出**到任意采集器(Datadog、Grafana、Honeycomb,或者你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证头和轮询间隔是可选的环境变量:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**摄取** —— 内置的 OTLP 接收器可以在 `/v1/traces` 和 `/v1/metrics` 处接收来自其他任何来源的追踪与指标数据(如需 protobuf 摄取,请执行 `pip install clawmetry[otel]`)。

你既能获得零配置、本地优先的 ClawMetry 仪表盘,又能把数据同时送到你团队已经在使用的后端——不锁定,也无需安装第二个智能体。

## 配置

大多数人不需要任何配置。ClawMetry 会自动检测你的工作空间、日志、会话和定时任务。

如果确实需要自定义:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

全部选项参见:`clawmetry --help`

## 支持的渠道

对于你在 OpenClaw 中配置好的每一个渠道,ClawMetry 都会展示实时活动。只有在你的 `openclaw.json` 中实际配置过的渠道才会出现在 Flow 图中——未配置的渠道会被自动隐藏。

点击 Flow 图中的任意渠道节点,即可查看带有收发消息计数的实时聊天气泡视图。

| 渠道 | 状态 | 实时弹窗 | 说明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支持 | ✅ | 消息、统计信息,10 秒刷新一次 |
| 💬 **iMessage** | ✅ 完整支持 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支持 | ✅ | 通过 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支持 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完整支持 | ✅ | 服务器 + 频道检测 |
| 🟪 **Slack** | ✅ 完整支持 | ✅ | 工作区 + 频道检测 |
| 🌐 **Webchat** | ✅ 完整支持 | ✅ | 内置的 Web UI 会话 |
| 📡 **IRC** | ✅ 完整支持 | ✅ | 终端风格的气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完整支持 | ✅ | 通过 BlueBubbles REST API 实现的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支持 | ✅ | 通过 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支持 | ✅ | 通过 Teams 机器人插件 |
| 🔷 **Mattermost** | ✅ 完整支持 | ✅ | 自托管团队聊天 |
| 🟩 **Matrix** | ✅ 完整支持 | ✅ | 去中心化,支持端到端加密 |
| 🟢 **LINE** | ✅ 完整支持 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支持 | ✅ | 去中心化的 NIP-04 私信 |
| 🟣 **Twitch** | ✅ 完整支持 | ✅ | 通过 IRC 连接实现的聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整支持 | ✅ | WebSocket 事件订阅 |
| 🔵 **Zalo** | ✅ 完整支持 | ✅ | Zalo Bot API |

> **自动检测：** ClawMetry 会读取你的 `~/.openclaw/openclaw.json`,只渲染你实际配置过的渠道。无需手动设置。

## Docker 部署

想在容器中运行 ClawMetry?没问题!🐳

**使用 Docker 快速开始：**

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

**Docker Compose 示例：**

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

> **注意：** 在 Docker 中运行时,请挂载你的智能体的数据 + 日志目录(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),这样 ClawMetry 才能自动检测你的配置。

## 环境要求

- Python 3.8+
- Flask(通过 pip 自动安装)
- 同一台机器上运行的 AI 智能体运行时:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents 或 n8n(在 Docker 中则为对应的挂载卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 会自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw)—— NVIDIA 面向企业级安全打造的 OpenClaw 包装层,在沙盒化的 OpenShell 容器中运行智能体。

大多数情况下无需额外配置。无论会话文件位于主机上的 `~/.openclaw/` 还是 OpenShell 容器内部,同步守护进程都会自动发现它们。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw:

1. **二进制检测** —— 检查是否存在 `nemoclaw` CLI,并运行 `nemoclaw status` 获取沙盒信息
2. **容器检测** —— 扫描正在运行的 Docker 容器,查找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 镜像,然后通过卷挂载或 `docker cp` 读取会话数据

从 NemoClaw 容器同步来的会话文件会在云端仪表盘中标记 `runtime=nemoclaw` 及 `container_id` 元数据,让你能一眼将其与标准 OpenClaw 会话区分开来。

### 推荐配置:在宿主机上运行同步守护进程

为获得最佳体验,请在**宿主机**(而非沙盒内部)上运行 ClawMetry 的同步守护进程。这样可以避开 NemoClaw 的网络策略限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程会自动在任何正在运行的 OpenShell 容器内查找会话数据。

### 可选:显式指定沙盒名称

如果自动检测未能生效,可以将 ClawMetry 指向正确的沙盒:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙盒内部运行(进阶)

如果你必须在 OpenShell 沙盒**内部**运行同步守护进程,请在 NemoClaw 网络策略中添加以下出站规则,使其能够访问 ClawMetry 的接入 API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

应用该策略:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 端口与接入点

| 接入点 | 端口 | 协议 | 是否必需 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步守护进程 → 云端) |
| `localhost:8900` | 8900 | HTTP | 是(本地仪表盘界面) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用于容器会话发现 |

同步守护进程只会向 `ingest.clawmetry.com` 发起出站 HTTPS 调用,不需要任何入站端口。

---

## 云端部署

有关 SSH 隧道、反向代理和 Docker 的说明,请参见 **[云端测试指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目使用 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测

ClawMetry 会在你首次在一台新机器上运行 `clawmetry` CLI 时,向
`https://app.clawmetry.com/api/install` 发送一次匿名的"首次运行"信号。
我们用它来统计安装量(这是我们作为开源项目所拥有的唯一营销指标),
并了解用户都安装了哪些智能体框架。

**每次安装恰好发送一次 POST 请求**,包含以下内容:

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储在 `~/.clawmetry/install_id` 中的随机 UUID | 去重;不与你的邮箱或 api_key 关联 |
| `version` | `0.12.167` | 了解各版本的实际使用分布 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支持优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我们接下来应该集成哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 将人工安装与 CI 噪声区分开 |

**我们不会发送以下内容**:IP 地址(云端会在服务器端根据请求推导出国家代码,
随后丢弃 IP)、主机名、用户名、工作空间路径、文件内容、你的 api_key、
你的邮箱,以及任何 PII 或工作空间相关的信息。传输载荷可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审计。

**退出遥测**(以下任一方式均可永久关闭):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

网络故障不会阻止 `clawmetry` 运行——该信号在守护线程上以"发送即忘"
的方式发出,超时时间为 3 秒。

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
  <strong>🦞 看见你的智能体如何思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 构建 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生态系统的一部分</sub>
</p>
