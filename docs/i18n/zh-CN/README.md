<!-- i18n-src:191e9094d7fa -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体在思考。** 为 **14 种 AI 智能体运行时** 提供实时可观测性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 10 种。一个仪表盘,统管你的整个智能体舰队。

> 🌐 **阅读其他语言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令,零配置,自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开,大功告成。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 14 种智能体运行时

ClawMetry 最初是为 OpenClaw 打造的可观测性工具,如今已能在一个仪表盘中统一计量你的**整个智能体舰队**,并自动检测你机器上运行的每一种运行时:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw 和 NemoClaw 在开源版应用中免费使用;其他运行时则需要 ClawMetry Cloud 或自托管的 Pro 许可证才能启用。从页头切换运行时,每个标签页(成本、令牌、工具、追踪)都会重新聚焦到该运行时。免费/付费的具体划分、层级矩阵、`/api/entitlement` 数据结构以及 `clawmetry license` CLI,详见 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能获得什么

- **Flow(流程)** —— 实时动态图,展示消息如何流经渠道、大脑、工具并返回
- **Overview(概览)** —— 健康检查、活动热力图、会话计数、模型信息
- **Usage(用量)** —— 按日/周/月细分的令牌与成本追踪
- **Sessions(会话)** —— 活跃智能体会话,含模型、令牌、最近活动
- **Crons(定时任务)** —— 定时作业的状态、下次运行时间、耗时
- **Logs(日志)** —— 彩色编码的实时日志流
- **Memory(记忆)** —— 浏览 SOUL.md、MEMORY.md、AGENTS.md、每日笔记
- **Transcripts(转录)** —— 以聊天气泡界面阅读会话历史
- **Alerts(告警)** —— 预算上限、错误率触发器、智能体离线检测;可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals(审批)** —— 将破坏性删除、强制推送、数据库变更、sudo、包安装、网络调用拦截在一键签核之后

## 截图

### 🧠 Brain(大脑)—— 实时智能体事件流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview(概览)—— 令牌用量与会话汇总
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow(流程)—— 实时工具调用信息流
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens(令牌)—— 按模型与会话划分的成本明细
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory(记忆)—— 工作区文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security(安全)—— 安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts(告警)—— 预算上限、错误率触发器、面向 Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals(审批)—— 在人工签核之前拦截高风险工具调用;策略驱动的保护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**面向 Claude Code 的执行前拦截** —— 一条命令即可安装一个
PreToolUse 钩子,它会在匹配的工具调用*执行前*暂停,并等待你的决策
(启用[云端推送通知](https://app.clawmetry.com/push)后,手机上一键即可完成):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒绝操作只会拦截那一次工具调用,智能体仍保留其会话,可以尝试其他方案。
在手机上批准会跳过 Claude Code 自身的权限提示(因为你已经回答过了)。
当 Claude Code 本身在等待你时,你同样会收到手机推送
(`permission_prompt` / `idle_prompt` 通知)。

## 安装

**一键安装(推荐):**
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

v2 React 应用位于 `frontend/` 目录,当 Flask 服务器以启用 v2 的方式启动时,
会在 `/v2` 路径下提供服务。

开发时请打开两个终端:

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
`http://localhost:8900`,因此 React 应用无需额外的 CORS 配置即可
与本地 Flask 服务器通信。

要构建随 Python 包一起发布的产物:

```bash
cd frontend
npm run build
```

生产构建产物会被写入 `clawmetry/static/v2/dist/`。

## 运行时/智能体兼容性

ClawMetry 支持观测许多 AI 智能体运行时,而不仅仅是 OpenClaw。每个非 OpenClaw 运行时都配有专属的读取适配器,负责将其原生会话格式转换为 ClawMetry 的统一数据结构;守护进程会将这些数据摄入同一个 DuckDB 存储和云端快照中,并标注对应运行时,当存在多个运行时时,Session replay(会话回放)标签页会显示一个**运行时切换器**。完整的兼容矩阵及新增运行时的指南请见 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 系列产品的入门介绍请见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

正在使用 [Perplexity 的 numbat](https://github.com/perplexityai/numbat) 智能体安全工具?ClawMetry 开箱即可摄入其检测结果与执行决策,详见 [`docs/NUMBAT.md`](docs/NUMBAT.md)。

| 运行时/智能体 | 状态 | 说明 |
|---|---|---|
| **OpenClaw** | 原生支持 | 参考运行时,自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平化的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。转录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 每会话一个 SQLite(`data/v2-sessions`)。转录 + 消息计数。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。转录、模型、令牌/成本。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。转录、模型、工具调用 + 思考过程、令牌用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。转录、模型、工具调用、令牌用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。聊天/合成器转录、模型。 |
| **Aider** | Beta 适配器 | 每个项目一个 `.aider.chat.history.md`。转录、模型、令牌计数。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。转录、模型、工具调用、令牌总量。 |
| **opencode** | Beta 适配器 | SQLite `~/.local/share/opencode`。转录、模型、工具调用、令牌 + 成本。 |
| **Qwen Code** | Beta 适配器 | JSONL `~/.qwen/projects/.../chats`。转录、模型、工具调用、令牌用量。 |
| **Pi** | Beta 适配器 | JSONL `~/.pi/agent/sessions`。转录、模型、工具调用、令牌 + 成本。 |
| **Deep Agents** | Beta 适配器 | SQLite `~/.deepagents/.state/sessions.db`。转录、模型、工具调用、令牌 + 成本。 |
| **n8n** | Beta 适配器 | SQLite `~/.n8n/database.sqlite`。工作流执行、节点运行、AI Agent 提示词,以及 n8n 有记录时的模型 + 令牌。 |
| **Antigravity** | Beta 适配器 | `~/.gemini/<flavor>/brain/` 下的 Brain JSONL。对话、工具步骤、思考过程、按生成划分的 Gemini 令牌拆分与成本、后台生成消耗。 |

"Beta 适配器"意味着 ClawMetry 为该运行时的真实磁盘格式提供了读取器,每一个都是基于真实机器上的真实安装构建并验证的(参见 `tests/fixtures/runtimes/<rt>/`)。这些适配器都是只读的,并且对各自运行时实际存储了什么内容如实呈现(例如 PicoClaw/NanoClaw/Cursor 不会将令牌成本写入磁盘)。当一个节点上运行多个运行时时,运行时切换器会将会话视图聚焦到某一个,便于深入排查。

## 追踪任意 SDK 智能体 —— 环外(out-loop)成本归因

上面这些运行时都会将会话写入磁盘。而你自己的**生产智能体**——无论是基于 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 构建的,还是一个纯粹的 `httpx` 循环——并不会这样做。ClawMetry 的零配置拦截器依然能够通过对 `httpx`/`requests` 进行猴子补丁(monkey-patching)来捕获它的 LLM 调用(成本、令牌、延迟、错误):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 环境变量)会为每次调用打上一个**命名来源**标签,这样你运行的每个产品都会在仪表盘 Overview 页面的 **🔌 Out-loop sources(环外来源)** 卡片中,以独立的一级、可归因成本的形式展现:每个智能体的调用数、提供商、延迟、错误率。如果没有设置来源?调用依然会被追踪,只是该卡片会保持隐藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

这与运行时适配器所使用的数据层完全相同(DuckDB → 云端快照),因此环外来源会像其他一切数据一样同步到云端仪表盘,并进行端到端加密。

## OpenTelemetry —— 厂商中立,把你的追踪数据发送到任何地方

ClawMetry 在双向都使用 **GenAI 语义约定** 支持 **OpenTelemetry**,因此你的智能体追踪数据永远不会被锁定在某一个工具里。

**导出** 每个会话的数据——LLM 调用、工具、子智能体、令牌、成本——以 OTLP/HTTP GenAI span 的形式发送到任意采集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证头和轮询间隔为可选环境变量:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**摄入** —— 内置的 OTLP 接收器可在 `/v1/traces` 和 `/v1/metrics` 接收来自任何其他系统的追踪数据和指标(执行 protobuf 摄入需要 `pip install clawmetry[otel]`)。

你既能获得零配置、本地优先的 ClawMetry 仪表盘,又能让数据进入你团队已经在使用的任何后端,没有锁定,也不必再安装第二个智能体。

## 配置

大多数人不需要任何配置。ClawMetry 会自动检测你的工作区、日志、会话和定时任务。

如果确实需要自定义:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

查看所有选项:`clawmetry --help`

## 支持的渠道

ClawMetry 会为你配置的每个 OpenClaw 渠道显示实时活动。只有在你的 `openclaw.json` 中实际配置过的渠道才会出现在 Flow 图中,未配置的渠道会自动隐藏。

点击 Flow 图中的任意渠道节点,即可看到带有收发消息计数的实时聊天气泡视图。

| 渠道 | 状态 | 实时弹窗 | 说明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支持 | ✅ | 消息、统计信息,10 秒刷新 |
| 💬 **iMessage** | ✅ 完整支持 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支持 | ✅ | 通过 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支持 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完整支持 | ✅ | 服务器 + 频道检测 |
| 🟪 **Slack** | ✅ 完整支持 | ✅ | 工作区 + 频道检测 |
| 🌐 **Webchat** | ✅ 完整支持 | ✅ | 内置网页 UI 会话 |
| 📡 **IRC** | ✅ 完整支持 | ✅ | 终端风格气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完整支持 | ✅ | 通过 BlueBubbles REST API 实现 iMessage |
| 🔵 **Google Chat** | ✅ 完整支持 | ✅ | 通过 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支持 | ✅ | 通过 Teams 机器人插件 |
| 🔷 **Mattermost** | ✅ 完整支持 | ✅ | 自托管团队聊天 |
| 🟩 **Matrix** | ✅ 完整支持 | ✅ | 去中心化,支持端到端加密 |
| 🟢 **LINE** | ✅ 完整支持 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整支持 | ✅ | 去中心化 NIP-04 私信 |
| 🟣 **Twitch** | ✅ 完整支持 | ✅ | 通过 IRC 连接的聊天 |
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

> **注意:** 在 Docker 中运行时,请挂载你的智能体的数据 + 日志目录(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),以便 ClawMetry 能自动检测你的配置。

## 环境要求

- Python 3.8+
- Flask(通过 pip 自动安装)
- 同一台机器上运行的 AI 智能体运行时:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n 或 Antigravity(如使用 Docker,则为挂载的卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 会自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw)—— NVIDIA 面向企业级安全打造的 OpenClaw 封装层,可在沙箱化的 OpenShell 容器中运行智能体。

大多数情况下无需额外配置。无论会话文件位于主机上的 `~/.openclaw/` 还是 OpenShell 容器内部,同步守护进程都会自动发现它们。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw:

1. **二进制检测** —— 检查是否存在 `nemoclaw` CLI,并运行 `nemoclaw status` 获取沙箱信息
2. **容器检测** —— 扫描正在运行的 Docker 容器,查找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 镜像,然后通过卷挂载或 `docker cp` 读取会话

从 NemoClaw 容器同步的会话文件会在云端仪表盘中标注 `runtime=nemoclaw` 和 `container_id` 元数据,便于你一眼分辨它们与标准 OpenClaw 会话的区别。

### 推荐配置:在宿主机上运行同步守护进程

为获得最佳体验,请在**宿主机**(而非沙箱内部)上运行 ClawMetry 的同步守护进程。这样可以避免 NemoClaw 网络策略的限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程会自动查找运行中的 OpenShell 容器内的会话。

### 可选:显式指定沙箱名称

如果自动检测不起作用,可以将 ClawMetry 指向正确的沙箱:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱内运行(进阶)

如果你必须**在** OpenShell 沙箱内部运行同步守护进程,请在你的 NemoClaw 网络策略中添加以下出站规则,以便它能访问 ClawMetry 的摄入 API:

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
| `localhost:8900` | 8900 | HTTP | 是(本地仪表盘 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用于容器会话发现 |

同步守护进程只会向 `ingest.clawmetry.com` 发起出站 HTTPS 调用,不需要任何入站端口。

---

## 云端部署

关于 SSH 隧道、反向代理和 Docker 的说明,请参阅 **[云端测试指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目使用 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测

ClawMetry 会向 `https://app.clawmetry.com/api/install` 发送匿名的
安装生命周期心跳:在新机器上首次运行 `clawmetry` CLI 时发送一次
`install` 心跳,升级到新版本后首次运行时发送一次 `update` 心跳,
完成仪表盘内引导选择时发送一次 `onboarded` 心跳。我们用这些数据
统计真实安装量(原始的 PyPI 下载数字中约 98% 来自镜像、CI 以及
自动更新的重复下载),并了解实际使用中都存在哪些智能体框架及其版本。

**每个生命周期事件、每个版本最多发送一次 POST 请求**,内容包含:

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储在 `~/.clawmetry/install_id` 的随机 UUID | 去重;在你显式连接 Cloud 同步之前保持匿名(之后经过认证的守护进程心跳会携带它,将此次安装与你的账号关联) |
| `event` | `install` / `update` / `onboarded` | 区分全新安装与现有安装的升级 |
| `version` | `0.12.167` | 了解各版本的实际使用分布 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支持优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我们接下来应该集成哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 将人工安装与 CI 噪音区分开 |

**我们不会发送**:IP(云端会在服务端根据请求推导出国家代码,随后
丢弃该 IP)、主机名、用户名、工作区路径、文件内容、你的 api_key、
你的邮箱,以及任何 PII 或工作区特定信息。传输负载的内容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审计。

**退出遥测**(以下任意一种方式都可永久关闭它):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

网络故障绝不会阻塞 `clawmetry` 的运行,这个心跳请求是在守护线程上
以“发出即忘”的方式发送的,超时时间为 3 秒。

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
  <strong>🦞 看见你的智能体在思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 构建 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生态系统的一部分</sub>
</p>
