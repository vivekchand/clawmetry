<!-- i18n-src:bab48eec552f -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体思考。** 面向 **14 种 AI 智能体运行时**的实时可观测性工具：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 10 种。一个仪表盘，掌控你整个智能体舰队。

> 🌐 **切换语言：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开，就这么简单。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 14 种智能体运行时

ClawMetry 最初是为 OpenClaw 打造的可观测性工具，如今已在一个仪表盘中为你的**整个智能体舰队**计量数据，自动检测你机器上的每一种运行时：

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw 和 NemoClaw 在开源应用中免费提供;其他运行时则需要 ClawMetry Cloud 或自托管的 Pro 许可证来解锁。可以在页头切换运行时,每个标签页——成本、Token、工具、追踪——都会重新聚焦到该运行时上。关于免费/付费的具体划分、层级矩阵、`/api/entitlement` 结构以及 `clawmetry license` CLI,请参阅 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能获得什么

- **Flow(流程图)**——实时动画图表,展示消息如何流经渠道、大脑、工具并返回
- **Overview(概览)**——健康检查、活跃度热力图、会话计数、模型信息
- **Usage(用量)**——按日/周/月细分的 Token 与成本追踪
- **Sessions(会话)**——展示模型、Token、最近活动的活跃智能体会话
- **Crons(定时任务)**——展示状态、下次运行时间、耗时的计划任务
- **Logs(日志)**——彩色实时日志流
- **Memory(记忆)**——浏览 SOUL.md、MEMORY.md、AGENTS.md 及每日笔记
- **Transcripts(转录)**——用于阅读会话历史的聊天气泡界面
- **Alerts(告警)**——预算上限、错误率触发、智能体离线检测;可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals(审批)**——将破坏性删除、强制推送、数据库变更、sudo、软件包安装、网络调用置于一键签核之后

## 截图

### 🧠 Brain(大脑)——实时智能体事件流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview(概览)——Token 用量与会话摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow(流程图)——实时工具调用信息流
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens(令牌)——按模型与会话划分的成本明细
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory(记忆)——工作区文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security(安全)——安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts(告警)——预算上限、错误率触发、Slack / Discord / PagerDuty / Email 的 Webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals(审批)——将高风险工具调用置于手动签核之后;由策略支持的保护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**面向 Claude Code 的执行前拦截**——一条命令即可安装一个
PreToolUse 钩子,它会在匹配的工具调用*执行前*暂停,并等待你的决策(启用
[云端推送通知](https://app.clawmetry.com/push)后,在手机上一键即可完成):

```bash
clawmetry hooks install     # 写入 ~/.claude/settings.json(幂等操作)
clawmetry hooks status      # 查看已接入的内容以及生效的策略数量
clawmetry hooks uninstall   # 仅移除 ClawMetry 添加的条目
```

拒绝操作只会阻止那一次工具调用——智能体仍保留其会话,可以尝试其他方案。在手机上批准会跳过
Claude Code 自身的权限提示(你已经回答过了)。未匹配的工具大约耗费 40ms,
并会回退到 Claude Code 的常规权限流程。当 Claude Code 本身在等待你的响应时
(`permission_prompt` / `idle_prompt` 通知),你同样会收到手机推送。

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

v2 版 React 应用位于 `frontend/` 目录下,当 Flask
服务器以启用 v2 的方式启动时,会在 `/v2` 路径提供服务。

开发时请使用两个终端:

```bash
# 终端 1:在 :8900 端口运行 Flask API/服务器
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 终端 2:在 :5173 端口运行 Vite 开发服务器
cd frontend
nvm use
npm ci
npm run dev
```

打开 `http://localhost:5173/v2/`。Vite 会将 `/api` 请求代理到
`http://localhost:8900`,这样 React 应用无需额外的 CORS 配置
即可与本地 Flask 服务器通信。

要构建随 Python 包一起发布的打包文件:

```bash
cd frontend
npm run build
```

生产环境打包文件会写入 `clawmetry/static/v2/dist/`。

## 运行时/智能体兼容性

ClawMetry 观测的智能体运行时不止 OpenClaw 一种。每个非 OpenClaw 运行时都配有一个专用的读取适配器,负责将其原生会话格式转换为 ClawMetry 的统一数据形态;守护进程会将它们摄入同一个 DuckDB 存储和云端快照,并标注运行时来源,当存在多个运行时时,Session replay(会话回放)标签页会显示**运行时切换器**。完整矩阵和新增运行时的指南参见 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 系列入门介绍参见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 运行时/智能体 | 状态 | 说明 |
|---|---|---|
| **OpenClaw** | 原生支持 | 参考运行时,自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平化的 `providers.Message` JSONL 格式(`~/.picoclaw/workspace/sessions`)。支持转录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 按会话的 SQLite 存储(`data/v2-sessions`)。支持转录 + 消息计数。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。支持转录、模型、Token/成本。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。支持转录、模型、工具调用 + 思考过程、Token 用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。支持转录、模型、工具调用、Token 用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。支持聊天/编辑器会话转录、模型。 |
| **Aider** | Beta 适配器 | 每个项目一个 `.aider.chat.history.md`。支持转录、模型、Token 计数。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。支持转录、模型、工具调用、Token 总量。 |
| **opencode** | Beta 适配器 | SQLite `~/.local/share/opencode`。支持转录、模型、工具调用、Token + 成本。 |
| **Qwen Code** | Beta 适配器 | JSONL `~/.qwen/projects/.../chats`。支持转录、模型、工具调用、Token 用量。 |
| **Pi** | Beta 适配器 | JSONL `~/.pi/agent/sessions`。支持转录、模型、工具调用、Token + 成本。 |
| **Deep Agents** | Beta 适配器 | SQLite `~/.deepagents/.state/sessions.db`。支持转录、模型、工具调用、Token + 成本。 |

"Beta 适配器"意味着 ClawMetry 为该运行时真实的磁盘存储格式提供了一个读取器,每一个都在真实机器上针对真实安装构建并验证过(参见 `tests/fixtures/runtimes/<rt>/`)。适配器是只读的;每一个都如实反映其运行时实际存储的内容(例如 PicoClaw/NanoClaw/Cursor 并不会将 Token 成本写入磁盘)。当一台机器上运行多个运行时时,运行时切换器可以将会话视图聚焦到某一个,便于深入排查。

## 追踪任意 SDK 智能体——环外成本归因

上面这些运行时都会将会话写入磁盘。而你自己构建的**生产智能体**——无论是基于
OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,还是一个纯粹的
`httpx` 循环——则不会。ClawMetry 的零配置拦截器仍能通过对 `httpx`/`requests`
进行猴子补丁(monkey-patch),捕获其 LLM 调用(成本、Token、延迟、错误):

```python
import clawmetry.track            # 激活拦截器
clawmetry.track.set_source("support-agent")   # 为该产品命名

# ……你的智能体照常运行;每一次 LLM 调用现在都会被追踪并归因。
```

`set_source()`(或 `CLAWMETRY_SOURCE=support-agent` 环境变量)会为每次调用打上一个**命名来源**标签,这样你运行的每个产品都会作为一条独立的、可归因成本的记录,出现在仪表盘 Overview 页面的 **🔌 环外来源** 卡片中——每个智能体的调用次数、供应商、延迟、错误率一目了然。没有设置来源?调用依旧会被追踪,只是该卡片会保持隐藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

这与运行时适配器所使用的数据层完全相同(DuckDB → 云端快照),因此环外来源数据会像其他一切数据一样,以端到端加密的方式同步到云端仪表盘。

## OpenTelemetry——供应商中立,随时随地发送你的追踪数据

ClawMetry 使用 **GenAI 语义约定**在两个方向上都支持 **OpenTelemetry**,因此你的智能体追踪数据永远不会被锁定在单一工具中。

将每个会话——LLM 调用、工具、子智能体、Token、成本——以 OTLP/HTTP GenAI span 的形式**导出**到任意采集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 等效写法:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证请求头和轮询间隔为可选的环境变量:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 额外的 HTTP 请求头
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒(默认 60)
```

**导入**——内置的 OTLP 接收器可在 `/v1/traces` 和 `/v1/metrics` 接受来自其他任意来源的追踪数据和指标(如需 protobuf 摄入,请运行 `pip install clawmetry[otel]`)。

你既能获得零配置、本地优先的 ClawMetry 仪表盘,**又**能把数据发送到你团队已经在用的任意后端——无锁定,无需额外安装第二个智能体。

## 配置

大多数人不需要任何配置。ClawMetry 会自动检测你的工作区、日志、会话和定时任务。

如果确实需要自定义:

```bash
clawmetry --port 9000              # 自定义端口(默认:8900)
clawmetry --host 127.0.0.1         # 仅绑定本地回环地址
clawmetry --workspace ~/mybot      # 自定义工作区路径
clawmetry --name "Alice"           # 你在 Flow 可视化图中显示的名字
```

查看所有选项:`clawmetry --help`

## 支持的渠道

ClawMetry 会为你配置的每一个 OpenClaw 渠道展示实时活动。只有在你的 `openclaw.json` 中实际配置过的渠道才会出现在 Flow 图中——未配置的渠道会自动隐藏。

点击 Flow 图中的任意渠道节点,即可查看包含收发消息计数的实时聊天气泡视图。

| 渠道 | 状态 | 实时弹窗 | 说明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完全支持 | ✅ | 消息、统计信息,10 秒刷新一次 |
| 💬 **iMessage** | ✅ 完全支持 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完全支持 | ✅ | 通过 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完全支持 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完全支持 | ✅ | 支持服务器 + 频道检测 |
| 🟪 **Slack** | ✅ 完全支持 | ✅ | 支持工作区 + 频道检测 |
| 🌐 **Webchat** | ✅ 完全支持 | ✅ | 内置网页 UI 会话 |
| 📡 **IRC** | ✅ 完全支持 | ✅ | 终端风格的气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完全支持 | ✅ | 通过 BlueBubbles REST API 实现的 iMessage |
| 🔵 **Google Chat** | ✅ 完全支持 | ✅ | 通过 Chat API Webhook |
| 🟣 **MS Teams** | ✅ 完全支持 | ✅ | 通过 Teams 机器人插件 |
| 🔷 **Mattermost** | ✅ 完全支持 | ✅ | 自托管团队聊天工具 |
| 🟩 **Matrix** | ✅ 完全支持 | ✅ | 去中心化,支持端到端加密 |
| 🟢 **LINE** | ✅ 完全支持 | ✅ | LINE 消息 API |
| ⚡ **Nostr** | ✅ 完全支持 | ✅ | 去中心化的 NIP-04 私信 |
| 🟣 **Twitch** | ✅ 完全支持 | ✅ | 通过 IRC 连接实现的聊天 |
| 🔷 **Feishu/Lark** | ✅ 完全支持 | ✅ | WebSocket 事件订阅 |
| 🔵 **Zalo** | ✅ 完全支持 | ✅ | Zalo 机器人 API |

> **自动检测:** ClawMetry 会读取你的 `~/.openclaw/openclaw.json`,只渲染你实际配置过的渠道。无需手动设置。

## Docker 部署

想在容器中运行 ClawMetry?完全没问题!🐳

**使用 Docker 快速开始:**

```bash
# 构建镜像
docker build -t clawmetry .

# 使用默认设置运行
docker run -p 8900:8900 clawmetry

# 或挂载你的智能体数据目录(此处以 OpenClaw 的 ~/.openclaw 为例)
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

> **注意:** 在 Docker 中运行时,请挂载你的智能体数据 + 日志目录(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),以便 ClawMetry 能自动检测你的配置。

## 系统要求

- Python 3.8+
- Flask(通过 pip 自动安装)
- 同一台机器上运行的 AI 智能体运行时:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi 或 Deep Agents(Docker 场景下则为挂载卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 会自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw)——NVIDIA 面向企业级安全打造的 OpenClaw 封装工具,可在沙箱化的 OpenShell 容器中运行智能体。

大多数情况下无需额外配置。同步守护进程会自动发现会话文件,无论它们位于主机上的 `~/.openclaw/`,还是位于某个 OpenShell 容器内部。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw:

1. **二进制检测**——检查是否存在 `nemoclaw` CLI,并运行 `nemoclaw status` 获取沙箱信息
2. **容器检测**——扫描正在运行的 Docker 容器,查找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 相关镜像,然后通过卷挂载或 `docker cp` 读取会话数据

从 NemoClaw 容器同步的会话文件会在云端仪表盘中被标记 `runtime=nemoclaw` 及 `container_id` 元数据,因此你可以一眼将它们与标准的 OpenClaw 会话区分开来。

### 推荐配置:在主机上运行同步守护进程

为获得最佳体验,建议在**主机**上(而非沙箱内部)运行 ClawMetry 的同步守护进程。这样可以避免触发 NemoClaw 的网络策略限制。

```bash
# 在主机上(沙箱之外)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程会自动查找运行中的 OpenShell 容器内部的会话数据。

### 可选:显式指定沙箱名称

如果自动检测未生效,可以指定 ClawMetry 应连接到的具体沙箱:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱内部运行(进阶)

如果你必须在 OpenShell 沙箱**内部**运行同步守护进程,请在你的 NemoClaw 网络策略中添加以下出站规则,使其能够访问 ClawMetry 的接入 API:

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

同步守护进程只会向 `ingest.clawmetry.com` 发起出站 HTTPS 调用,无需任何入站端口。

---

## 云端部署

有关 SSH 隧道、反向代理和 Docker 的内容,请参见 **[云端测试指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目使用 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测

ClawMetry 会在你首次在新机器上运行 `clawmetry` CLI 时,向
`https://app.clawmetry.com/api/install` 发送一次匿名的"首次运行"信号。
我们用它来统计安装量(这是我们这个开源项目唯一的营销指标),
并了解用户都安装了哪些智能体框架。

**每次安装只会发送一次 POST 请求**,内容包括:

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储于 `~/.clawmetry/install_id` 的随机 UUID | 去重;不与你的邮箱或 api_key 关联 |
| `version` | `0.12.167` | 了解各版本的实际使用分布 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 明确平台支持的优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 我们下一步应对接哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 将人工安装与 CI 噪声区分开来 |

**我们不会发送**:IP 地址(云端会在服务端根据请求推断国家代码,随后丢弃该
IP)、主机名、用户名、工作区路径、文件内容、你的 api_key、你的邮箱,
以及任何个人身份信息或工作区相关的数据。传输的负载内容可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审计。

**退出遥测**(以下任意一种方式即可永久关闭):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # 按 shell 会话生效
export DO_NOT_TRACK=1                          # W3C 跨工具标准
touch ~/.clawmetry/notelemetry                 # 持久化的文件标记
```

网络故障绝不会阻止 `clawmetry` 正常运行——该信号是在守护线程上发送的
即发即忘请求,超时时间为 3 秒。

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
  <strong>🦞 看见你的智能体思考</strong><br>
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 打造 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生态系统的一部分</sub>
</p>
