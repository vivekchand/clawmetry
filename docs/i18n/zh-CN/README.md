<!-- i18n-src:48548997be76 -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体思考。** 面向 **12 种 AI 智能体运行时**的实时可观测性仪表板：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及其他 8 种。一个仪表板，掌控你的整个智能体集群。

> 🌐 **阅读其他语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令，零配置，自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开即可完成。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 12 种智能体运行时

ClawMetry 最初作为 OpenClaw 的可观测性工具诞生，现已在同一仪表板中监控你的**整个智能体集群**，自动检测你机器上的每种运行时：

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw 和 NemoClaw 在开源版本中免费使用；其他运行时需通过 ClawMetry Cloud 或自托管 Pro 授权才能启用。从页面顶部切换运行时后，费用、Token、工具、追踪等所有标签页的数据范围均会随之切换。

## 你能获得什么

- **Flow** — 实时动态图，展示消息在频道、大脑、工具之间的流转过程
- **Overview** — 健康检查、活动热力图、会话数量、模型信息
- **Usage** — Token 和费用追踪，支持按日、按周、按月细分
- **Sessions** — 活跃智能体会话列表，含模型、Token、最近活动信息
- **Crons** — 定时任务及其状态、下次执行时间、持续时长
- **Logs** — 彩色实时日志流
- **Memory** — 浏览 SOUL.md、MEMORY.md、AGENTS.md 及日常笔记
- **Transcripts** — 以对话气泡形式阅读会话历史
- **Alerts** — 预算上限、错误率触发、智能体离线检测；可路由至 Slack、Discord、PagerDuty、Telegram、邮件
- **Approvals** — 对危险的删除操作、强制推送、数据库变更、sudo、包安装、网络调用设置一键审批门控

## 截图

### 🧠 Brain — 智能体实时事件流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token 用量与会话概览
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 实时工具调用动态
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 按模型与会话细分的费用明细
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作区文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 预算上限、错误率触发，以及推送至 Slack / Discord / PagerDuty / 邮件的 Webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 对高风险工具调用设置人工审批门控，并配有策略驱动的保护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## 安装

**一键安装（推荐）：**
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

v2 React 应用位于 `frontend/` 目录，启用 v2 后由 Flask 服务在 `/v2` 路径提供服务。

开发时请使用两个终端：

```bash
# 终端 1：Flask API/服务器，监听 :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# 终端 2：Vite 开发服务器，监听 :5173
cd frontend
nvm use
npm ci
npm run dev
```

打开 `http://localhost:5173/v2/`。Vite 会将 `/api` 请求代理到 `http://localhost:8900`，因此 React 应用无需额外配置 CORS 即可与本地 Flask 服务器通信。

构建随 Python 包一起发布的生产包：

```bash
cd frontend
npm run build
```

生产构建产物将写入 `clawmetry/static/v2/dist/`。

## 运行时 / 智能体兼容性

ClawMetry 可观测多种 AI 智能体运行时，而不仅限于 OpenClaw。每种非 OpenClaw 运行时都内置了专用读取适配器，将其原生会话格式转换为 ClawMetry 的统一数据结构；守护进程将它们标记运行时信息后一并写入 DuckDB 存储和云端快照，会话回放标签页在检测到多种运行时时会显示**运行时切换器**。完整兼容矩阵及添加运行时的指南请参见 [`docs/compatibility.md`](docs/compatibility.md)，OpenClaw 系列入门介绍请参见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 运行时 / 智能体 | 状态 | 说明 |
|---|---|---|
| **OpenClaw** | 原生支持 | 参考运行时，自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平 `providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。支持对话记录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 按会话存储的 SQLite（`data/v2-sessions`）。支持对话记录及消息数量。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。支持对话记录、模型、Token/费用。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。支持对话记录、模型、工具调用及思考过程、Token 用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。支持对话记录、模型、工具调用、Token 用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。支持聊天/编辑器对话记录、模型。 |
| **Aider** | Beta 适配器 | 每个项目的 `.aider.chat.history.md`。支持对话记录、模型、Token 数量。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。支持对话记录、模型、工具调用、Token 总量。 |
| **opencode** | Beta 适配器 | SQLite `~/.local/share/opencode`。支持对话记录、模型、工具调用、Token 及费用。 |
| **Qwen Code** | Beta 适配器 | JSONL `~/.qwen/projects/.../chats`。支持对话记录、模型、工具调用、Token 用量。 |

"Beta 适配器"意味着 ClawMetry 已为该运行时的实际磁盘格式实现了读取器，每个读取器均在真实机器的真实安装环境中构建并验证（参见 `tests/fixtures/runtimes/<rt>/`）。适配器均为只读；每个适配器如实反映其运行时实际存储的内容（例如 PicoClaw、NanoClaw、Cursor 不会将 Token 费用写入磁盘）。当多个运行时在同一节点上运行时，运行时切换器可将会话视图锁定到单个运行时，便于深入分析。

## 追踪任意 SDK 智能体 — 环外费用归因

上述运行时均将会话写入磁盘。而你自己构建的**生产智能体**（基于 OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B 或普通 `httpx` 循环）则不会。ClawMetry 的零配置拦截器通过猴子补丁 `httpx`/`requests` 仍能捕获其 LLM 调用（费用、Token、延迟、错误）：

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`（或环境变量 `CLAWMETRY_SOURCE=support-agent`）会为每次调用打上**命名来源**标签，使你运行的每个产品都作为独立的、可进行费用归因的条目出现在仪表板 Overview 的 **🔌 Out-loop sources** 卡片中，包含每个智能体的调用次数、提供商、延迟和错误率。若未设置来源，调用仍会被追踪，但该卡片不会显示。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

这与运行时适配器使用的是同一数据层（DuckDB 云端快照），因此环外来源的数据与其他所有数据一样同步到云端仪表板，并经过端对端加密。

## OpenTelemetry — 厂商中立，追踪数据发往任意目标

ClawMetry 双向支持 **OpenTelemetry**，采用 **GenAI 语义约定**，确保你的智能体追踪数据不受任何单一工具锁定。

**导出**每个会话（LLM 调用、工具、子智能体、Token、费用）为 OTLP/HTTP GenAI Span，发往任意采集器（Datadog、Grafana、Honeycomb 或你自己的 OTel Collector）：

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证头和轮询间隔为可选环境变量：

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**接收** — 内置 OTLP 接收器可在 `/v1/traces` 和 `/v1/metrics` 接受来自其他任意系统的追踪和指标（Protobuf 接收需 `pip install clawmetry[otel]`）。

你既能享有零配置、本地优先的 ClawMetry 仪表板，同时还能将数据发送到团队已有的任意后端，无锁定，无需安装第二个智能体。

## 配置

大多数人无需任何配置。ClawMetry 会自动检测你的工作区、日志、会话和 cron 任务。

如有自定义需求：

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

所有选项：`clawmetry --help`

## 支持的频道

ClawMetry 显示你已配置的每个 OpenClaw 频道的实时活动。只有在你的 `openclaw.json` 中实际配置的频道才会出现在 Flow 图中，未配置的频道将自动隐藏。

点击 Flow 中的任意频道节点，可查看含收发消息数量的实时对话气泡视图。

| 频道 | 状态 | 实时弹窗 | 说明 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整 | ✅ | 消息、统计数据，每 10 秒刷新 |
| 💬 **iMessage** | ✅ 完整 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整 | ✅ | 通过 WhatsApp Web（Baileys） |
| 🔵 **Signal** | ✅ 完整 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完整 | ✅ | 服务器及频道自动检测 |
| 🟪 **Slack** | ✅ 完整 | ✅ | 工作区及频道自动检测 |
| 🌐 **Webchat** | ✅ 完整 | ✅ | 内置 Web UI 会话 |
| 📡 **IRC** | ✅ 完整 | ✅ | 终端风格气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完整 | ✅ | 通过 BlueBubbles REST API 实现 iMessage |
| 🔵 **Google Chat** | ✅ 完整 | ✅ | 通过 Chat API Webhook |
| 🟣 **MS Teams** | ✅ 完整 | ✅ | 通过 Teams 机器人插件 |
| 🔷 **Mattermost** | ✅ 完整 | ✅ | 自托管团队聊天 |
| 🟩 **Matrix** | ✅ 完整 | ✅ | 去中心化，支持端对端加密 |
| 🟢 **LINE** | ✅ 完整 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整 | ✅ | 去中心化 NIP-04 私信 |
| 🟣 **Twitch** | ✅ 完整 | ✅ | 通过 IRC 连接实现聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整 | ✅ | WebSocket 事件订阅 |
| 🔵 **Zalo** | ✅ 完整 | ✅ | Zalo Bot API |

> **自动检测：** ClawMetry 读取你的 `~/.openclaw/openclaw.json`，仅渲染你实际配置的频道，无需手动设置。

## Docker 部署

想在容器中运行 ClawMetry？没问题！🐳

**Docker 快速启动：**

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

> **注意：** 在 Docker 中运行时，请挂载你的智能体数据目录和日志目录（如 `~/.openclaw`、`~/.claude`、`~/.codex`），以便 ClawMetry 自动检测你的配置。

## 系统要求

- Python 3.8+
- Flask（通过 pip 自动安装）
- 同一台机器上安装有 AI 智能体运行时：OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw 或 PicoClaw（Docker 方式则通过挂载卷提供）
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw)，即 NVIDIA 面向 OpenClaw 的企业级安全封装，可在沙箱化的 OpenShell 容器内运行智能体。

大多数情况下无需额外配置。同步守护进程会自动发现会话文件，无论它们位于主机的 `~/.openclaw/` 还是 OpenShell 容器内部。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw：

1. **二进制检测** — 查找 `nemoclaw` CLI 并运行 `nemoclaw status` 获取沙箱信息
2. **容器检测** — 扫描运行中的 Docker 容器，查找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 镜像，然后通过卷挂载或 `docker cp` 读取会话

从 NemoClaw 容器同步的会话文件在云端仪表板中会被标记 `runtime=nemoclaw` 和 `container_id` 元数据，一眼即可与标准 OpenClaw 会话区分。

### 推荐配置：在宿主机上运行同步守护进程

为获得最佳体验，请在**宿主机**上（而非沙箱内部）运行 ClawMetry 的同步守护进程，以避免受到 NemoClaw 网络策略的限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程将自动发现所有运行中 OpenShell 容器内的会话。

### 可选：显式指定沙箱名称

若自动检测不生效，可手动指向正确的沙箱：

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱内部运行（高级用法）

如果必须在 OpenShell 沙箱**内部**运行同步守护进程，请在 NemoClaw 网络策略中添加以下出站规则，以便其访问 ClawMetry 接收 API：

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

应用配置：

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 端口与端点

| 端点 | 端口 | 协议 | 是否必需 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是（同步守护进程 → 云端） |
| `localhost:8900` | 8900 | HTTP | 是（本地仪表板 UI） |
| Docker socket（`/var/run/docker.sock`） | — | Unix socket | 用于容器会话发现 |

同步守护进程仅向 `ingest.clawmetry.com` 发起出站 HTTPS 请求，无需开放任何入站端口。

---

## 云端部署

关于 SSH 隧道、反向代理和 Docker，请参阅 **[云端测试指南](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目通过 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测

ClawMetry 在新机器上首次运行 `clawmetry` CLI 时，会向 `https://app.clawmetry.com/api/install` 发送一次匿名的"首次运行"ping。我们以此统计安装数量（这是一个开源项目，唯一可用的营销指标）并了解用户安装了哪些智能体框架。

**每次安装仅发送一次 POST 请求**，内容包含：

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储于 `~/.clawmetry/install_id` 的随机 UUID | 去重；不与你的邮箱或 api_key 关联 |
| `version` | `0.12.167` | 了解线上版本分布 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支持优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 下一步应优先集成哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 区分真实用户安装与 CI 噪声 |

**我们不发送以下内容**：IP（云端从请求中提取国家代码后立即丢弃 IP）、主机名、用户名、工作区路径、文件内容、api_key、邮箱，以及任何个人身份信息或工作区相关数据。实际传输的内容可在 [`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审查。

**退出遥测**（以下任意一种方式均可永久禁用）：

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

此处的网络故障绝不会阻碍 `clawmetry` 正常运行，ping 在守护线程中以"发后即忘"方式发出，超时时间为 3 秒。

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
  <sub>由 <a href="https://github.com/vivekchand">@vivekchand</a> 构建 · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 生态系统的一部分</sub>
</p>
