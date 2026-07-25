<!-- i18n-src:8f42d460a973 -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体在思考。** 面向 **14 种 AI 智能体运行时**的实时可观测性工具：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 10 种。一个仪表盘,掌控你的整个智能体舰队。

> 🌐 **多语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令,零配置,自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开,即可完成。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 14 种智能体运行时

ClawMetry 最初是为 OpenClaw 打造的可观测性工具,如今已经能在一个仪表盘中统一计量你的**整个智能体舰队**,并自动检测你机器上运行的每种运行时:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw 和 NemoClaw 在开源版应用中免费提供;其他运行时需要通过 ClawMetry Cloud 或自托管 Pro 许可证解锁。可以在页面头部切换运行时,切换后每个标签页(成本、Token、工具、追踪)都会重新聚焦到该运行时。关于免费/付费的具体划分、层级矩阵、`/api/entitlement` 返回结构以及 `clawmetry license` CLI 的详细说明,请见 **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**。

## 你能获得什么

- **Flow(流程)** — 实时动画图,展示消息如何在渠道、大脑、工具之间流转并返回
- **Overview(概览)** — 健康检查、活动热力图、会话计数、模型信息
- **Usage(用量)** — 按日/周/月细分的 Token 与成本追踪
- **Sessions(会话)** — 活跃智能体会话,包含模型、Token、最后活动时间
- **Crons(定时任务)** — 计划任务的状态、下次运行时间、运行时长
- **Logs(日志)** — 彩色实时日志流
- **Memory(记忆)** — 浏览 SOUL.md、MEMORY.md、AGENTS.md、每日笔记
- **Transcripts(会话记录)** — 聊天气泡式界面,便于阅读会话历史
- **Alerts(告警)** — 预算上限、错误率触发、智能体离线检测;可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals(审批)** — 将破坏性删除、强制推送、数据库变更、sudo、软件包安装、网络调用等操作拦截在一键签核之后

## 截图

### 🧠 Brain — 实时智能体事件流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 用量与会话摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 实时工具调用信息流
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 按模型与会话的成本细分
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作区文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 预算上限、错误率触发、Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 将高风险工具调用拦截在人工签核之后;基于策略的防护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

v2 版 React 应用位于 `frontend/` 目录,当 Flask 服务器以启用 v2 的方式启动时,会在 `/v2` 路径下提供服务。

开发时请使用两个终端:

```bash
# 终端 1:在 :8900 上运行 Flask API/服务器
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 终端 2:在 :5173 上运行 Vite 开发服务器
cd frontend
nvm use
npm ci
npm run dev
```

打开 `http://localhost:5173/v2/`。Vite 会将 `/api` 请求代理到
`http://localhost:8900`,因此 React 应用无需额外的 CORS 配置即可与本地 Flask 服务器通信。

要构建随 Python 包一起发布的产物包:

```bash
cd frontend
npm run build
```

生产构建产物会写入 `clawmetry/static/v2/dist/`。

## 运行时/智能体兼容性

ClawMetry 观察的运行时不止 OpenClaw 一种。每个非 OpenClaw 的运行时都配有专用的读取适配器,将其原生会话格式转换为 ClawMetry 的统一数据结构;守护进程将它们摄入同一个 DuckDB 存储 + 云端快照,并打上运行时标签,当存在多个运行时时,Session 回放标签页会显示**运行时切换器**。完整矩阵及新增运行时指南见 [`docs/compatibility.md`](docs/compatibility.md),OpenClaw 家族入门介绍见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 运行时/智能体 | 状态 | 说明 |
|---|---|---|
| **OpenClaw** | 原生支持 | 参考运行时,自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平的 `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。会话记录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 每会话一个 SQLite 文件(`data/v2-sessions`)。会话记录 + 消息计数。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。会话记录、模型、Token/成本。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。会话记录、模型、工具调用 + 思考过程、Token 用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。会话记录、模型、工具调用、Token 用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。聊天/编辑器会话记录、模型。 |
| **Aider** | Beta 适配器 | 每个项目一个 `.aider.chat.history.md`。会话记录、模型、Token 计数。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。会话记录、模型、工具调用、Token 总量。 |
| **opencode** | Beta 适配器 | SQLite `~/.local/share/opencode`。会话记录、模型、工具调用、Token + 成本。 |
| **Qwen Code** | Beta 适配器 | JSONL `~/.qwen/projects/.../chats`。会话记录、模型、工具调用、Token 用量。 |
| **Pi** | Beta 适配器 | JSONL `~/.pi/agent/sessions`。会话记录、模型、工具调用、Token + 成本。 |
| **Deep Agents** | Beta 适配器 | SQLite `~/.deepagents/.state/sessions.db`。会话记录、模型、工具调用、Token + 成本。 |

"Beta 适配器"意味着 ClawMetry 为该运行时的真实磁盘格式提供了读取器,每一个都是针对真实机器上的真实安装构建并验证的(参见 `tests/fixtures/runtimes/<rt>/`)。这些适配器都是只读的,并且如实反映各运行时实际存储的内容(例如 PicoClaw/NanoClaw/Cursor 并不会把 Token 成本写入磁盘)。当一个节点上运行多个运行时时,运行时切换器可以将会话视图聚焦到单一运行时,便于深入排查。

## 追踪任意 SDK 智能体 — 环外(out-loop)成本归因

以上运行时都会把会话写入磁盘。但你自己构建的**生产环境智能体**——基于 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B,或者一个普通的 `httpx` 循环——并不会这样做。ClawMetry 的零配置拦截器仍然可以通过对 `httpx`/`requests` 打补丁的方式,捕获它的 LLM 调用(成本、Token、延迟、错误):

```python
import clawmetry.track            # 激活拦截器
clawmetry.track.set_source("support-agent")   # 为该产品命名

# ...你的智能体正常运行;此后每次 LLM 调用都会被追踪并归因。
```

`set_source()`(或环境变量 `CLAWMETRY_SOURCE=support-agent`)会为每次调用打上一个**命名来源**标签,这样你运行的每个产品都会作为独立的、可归因成本的条目,出现在仪表盘 Overview 页面的 **🔌 环外来源(Out-loop sources)** 卡片中——按每个智能体展示调用次数、提供商、延迟、错误率。如果没有设置来源?调用依然会被追踪,只是该卡片会保持隐藏。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

这与运行时适配器所使用的数据层完全相同(DuckDB → 云端快照),因此环外来源会像其他数据一样同步到云端仪表盘,并进行端到端加密。

## OpenTelemetry — 厂商中立,你的追踪数据发送到任何地方

ClawMetry 在收发两个方向上都支持 **OpenTelemetry**,并使用 **GenAI 语义约定**,因此你的智能体追踪数据永远不会被锁定在某一个工具里。

**导出**每个会话——LLM 调用、工具、子智能体、Token、成本——以 OTLP/HTTP GenAI span 的形式发送到任意采集器(Datadog、Grafana、Honeycomb,或你自己的 OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 等效写法:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证请求头和轮询间隔是可选的环境变量:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 额外的 HTTP 请求头
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒(默认 60)
```

**接收(Ingest)** — 内置的 OTLP 接收器可在 `/v1/traces` 和 `/v1/metrics` 上接收来自其他任意来源的追踪与指标数据(protobuf 接收需要 `pip install clawmetry[otel]`)。

你既能获得零配置、本地优先的 ClawMetry 仪表盘,又能把数据同步到团队现有的任意后端——没有锁定,也不需要安装第二个智能体。

## 配置

大多数人不需要任何配置。ClawMetry 会自动检测你的工作区、日志、会话和定时任务。

如果确实需要自定义:

```bash
clawmetry --port 9000              # 自定义端口(默认:8900)
clawmetry --host 127.0.0.1         # 仅绑定本地地址
clawmetry --workspace ~/mybot      # 自定义工作区路径
clawmetry --name "Alice"           # 在 Flow 可视化中显示你的名字
```

查看全部选项:`clawmetry --help`

## 支持的渠道

ClawMetry 会为你配置的每个 OpenClaw 渠道展示实时活动。只有在你的 `openclaw.json` 中真正配置过的渠道才会出现在 Flow 图中,未配置的渠道会被自动隐藏。

点击 Flow 中的任意渠道节点,即可看到实时聊天气泡视图,包含收发消息计数。

| 渠道 | 状态 | 实时弹窗 | 说明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整支持 | ✅ | 消息、统计,10 秒刷新 |
| 💬 **iMessage** | ✅ 完整支持 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整支持 | ✅ | 通过 WhatsApp Web(Baileys) |
| 🔵 **Signal** | ✅ 完整支持 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完整支持 | ✅ | 服务器 + 频道检测 |
| 🟪 **Slack** | ✅ 完整支持 | ✅ | 工作区 + 频道检测 |
| 🌐 **Webchat** | ✅ 完整支持 | ✅ | 内置网页 UI 会话 |
| 📡 **IRC** | ✅ 完整支持 | ✅ | 终端风格气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完整支持 | ✅ | 通过 BlueBubbles REST API 的 iMessage |
| 🔵 **Google Chat** | ✅ 完整支持 | ✅ | 通过 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整支持 | ✅ | 通过 Teams bot 插件 |
| 🔷 **Mattermost** | ✅ 完整支持 | ✅ | 自托管团队聊天工具 |
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

> **注意:** 在 Docker 中运行时,请挂载你的智能体数据 + 日志目录(例如 `~/.openclaw`、`~/.claude`、`~/.codex`),这样 ClawMetry 才能自动检测你的配置。

## 环境要求

- Python 3.8+
- Flask(通过 pip 自动安装)
- 同一台机器上运行的 AI 智能体运行时:OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi 或 Deep Agents(Docker 场景下也可以是挂载的卷)
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 会自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw) —— NVIDIA 为 OpenClaw 打造的企业级安全封装层,能在沙箱化的 OpenShell 容器内运行智能体。

大多数情况下无需额外配置。无论会话文件位于宿主机的 `~/.openclaw/` 还是某个 OpenShell 容器内部,同步守护进程都会自动发现它们。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw:

1. **二进制检测** —— 检查是否存在 `nemoclaw` CLI,并运行 `nemoclaw status` 获取沙箱信息
2. **容器检测** —— 扫描正在运行的 Docker 容器,查找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 镜像,然后通过卷挂载或 `docker cp` 读取会话数据

从 NemoClaw 容器同步的会话文件,在云端仪表盘中会带有 `runtime=nemoclaw` 和 `container_id` 元数据标签,方便你一眼将其与标准 OpenClaw 会话区分开来。

### 推荐配置:在宿主机上运行同步守护进程

为获得最佳体验,建议在**宿主机**(而非沙箱内部)上运行 ClawMetry 的同步守护进程。这样可以避免触发 NemoClaw 的网络策略限制。

```bash
# 在宿主机上(沙箱之外)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程会自动在任何正在运行的 OpenShell 容器内查找会话数据。

### 可选:指定沙箱名称

如果自动检测未生效,可以让 ClawMetry 明确指向正确的沙箱:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱内部运行(进阶)

如果必须在 OpenShell 沙箱**内部**运行同步守护进程,请在你的 NemoClaw 网络策略中添加以下出站(egress)规则,以便它能访问 ClawMetry 的接收 API:

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

### 端口与端点

| 端点 | 端口 | 协议 | 是否必需 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是(同步守护进程 → 云端) |
| `localhost:8900` | 8900 | HTTP | 是(本地仪表盘 UI) |
| Docker socket(`/var/run/docker.sock`) | — | Unix socket | 用于容器会话发现 |

同步守护进程只会向 `ingest.clawmetry.com` 发起出站 HTTPS 调用,不需要任何入站端口。

---

## 云端部署

关于 SSH 隧道、反向代理与 Docker 的说明,请参见 **[云端测试指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目使用 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测(Telemetry)

在新机器上首次运行 `clawmetry` CLI 时,ClawMetry 会向
`https://app.clawmetry.com/api/install` 发送一次匿名的"首次运行"上报。
我们用它来统计安装量(这是我们这个开源项目唯一拥有的市场指标),
并了解用户都安装了哪些智能体框架。

**每次安装恰好发送一次 POST 请求**,内容包括:

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储在 `~/.clawmetry/install_id` 的随机 UUID | 用于去重;不与你的邮箱或 api_key 关联 |
| `version` | `0.12.167` | 了解线上各版本的分布情况 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 确定平台支持优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 了解接下来应优先对接哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 区分人工安装与 CI 产生的噪音 |

**我们不会发送**:IP 地址(云端会在服务器端从请求中推导国家代码,随后丢弃 IP)、主机名、用户名、工作区路径、文件内容、你的 api_key、你的邮箱,以及任何 PII 或与工作区相关的信息。该上报的完整载荷可在
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审计。

**退出遥测**(以下任意一种方式即可永久禁用):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # 仅当前 shell 会话生效
export DO_NOT_TRACK=1                          # W3C 跨工具通用标准
touch ~/.clawmetry/notelemetry                 # 持久化的文件标记
```

网络故障不会阻塞 `clawmetry` 的正常运行——该上报是在后台线程中以
"发送后不管"的方式执行的,超时时间为 3 秒。

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
