<!-- i18n-src:56ff57310588 -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体在思考。** 面向 [OpenClaw](https://github.com/openclaw/openclaw) AI 智能体的实时可观测性。

> 🌐 **以其他语言阅读：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开，搞定。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 你将获得什么

- **Flow** — 实时动画图，展示消息在各渠道、大脑、工具之间往返流动
- **Overview** — 健康检查、活动热力图、会话计数、模型信息
- **Usage** — 按日/周/月细分的 token 与成本追踪
- **Sessions** — 活跃的智能体会话，含模型、token、最近活动
- **Crons** — 定时任务，含状态、下次运行、时长
- **Logs** — 彩色编码的实时日志流
- **Memory** — 浏览 SOUL.md、MEMORY.md、AGENTS.md、每日笔记
- **Transcripts** — 用于阅读会话历史的聊天气泡界面
- **Alerts** — 预算上限、错误率触发、智能体离线检测；可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals** — 将破坏性删除、强制推送、数据库变更、sudo、软件包安装、网络调用全部置于一键审批之后

## 截图

### 🧠 Brain — 实时智能体事件流
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — token 使用量与会话摘要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — 实时工具调用流
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — 按模型与会话拆分的成本
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — 工作区文件浏览器
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 安全态势与审计日志
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 预算上限、错误率触发、发往 Slack / Discord / PagerDuty / Email 的 webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — 将高风险工具调用置于人工审批之后；由策略支撑的保护规则
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## 安装

**一行命令（推荐）：**
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

v2 React 应用位于 `frontend/`，当 Flask 服务器以启用 v2 的方式启动时，会在 `/v2` 提供服务。

开发时使用两个终端：

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

打开 `http://localhost:5173/v2/`。Vite 会把 `/api` 请求代理到 `http://localhost:8900`，因此 React 应用无需额外的 CORS 设置即可与本地 Flask 服务器通信。

构建随 Python 包一起发布的 bundle：

```bash
cd frontend
npm run build
```

生产 bundle 会写入 `clawmetry/static/v2/dist/`。

## 运行时 / 智能体兼容性

ClawMetry 可观测多种 AI 智能体运行时，而不仅仅是 OpenClaw。每一个非 OpenClaw 运行时都附带一个专用的 reader 适配器，将其原生会话格式转换为 ClawMetry 的统一结构；守护进程把它们摄取进同一个 DuckDB 存储 + 云端快照，并标注所属运行时，当存在多个运行时时，Session replay 标签页会显示一个**运行时切换器**。完整矩阵以及添加运行时的指南见 [`docs/compatibility.md`](docs/compatibility.md)，OpenClaw 系列入门见 [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)。

| 运行时 / 智能体 | 状态 | 备注 |
|---|---|---|
| **OpenClaw** | 原生 | 参考运行时，自动检测 |
| **PicoClaw** | Beta 适配器 | 扁平的 `providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。会话记录、模型、工具调用。 |
| **NanoClaw** | Beta 适配器 | 每会话一个 SQLite（`data/v2-sessions`）。会话记录 + 消息计数。 |
| **Hermes** | Beta 适配器 | SQLite `~/.hermes/state.db`。会话记录、模型、token/成本。 |
| **Claude Code** | Beta 适配器 | JSONL `~/.claude/projects/.../<id>.jsonl`。会话记录、模型、工具调用 + 思考过程、token 用量。 |
| **Codex** | Beta 适配器 | Rollout JSONL `~/.codex/sessions/...`。会话记录、模型、工具调用、token 用量。 |
| **Cursor** | Beta 适配器 | SQLite `state.vscdb`。聊天/composer 会话记录、模型。 |
| **Aider** | Beta 适配器 | 每个项目一个 `.aider.chat.history.md`。会话记录、模型、token 计数。 |
| **Goose** | Beta 适配器 | SQLite `~/.local/share/goose`。会话记录、模型、工具调用、token 总计。 |

“Beta 适配器”意味着 ClawMetry 为该运行时真实的磁盘格式提供了一个 reader，每个都在真实机器上的真实安装环境中构建并验证过（见 `tests/fixtures/runtimes/<rt>/`）。适配器为只读；每个适配器都如实反映其运行时实际存储的内容（例如 PicoClaw/NanoClaw/Cursor 并不把 token 成本写到磁盘上）。当一个节点上运行多个运行时时，运行时切换器会将会话视图限定到其中一个，便于干净地深入分析。

## OpenTelemetry — 厂商中立，把你的 trace 发往任何地方

ClawMetry 双向支持 **OpenTelemetry**，采用 **GenAI 语义约定**，因此你的智能体 trace 永远不会被锁定在某一种工具里。

将每个会话（LLM 调用、工具、子智能体、token、成本）作为 OTLP/HTTP GenAI span **导出**到任意 collector（Datadog、Grafana、Honeycomb，或你自己的 OTel Collector）：

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

认证头与轮询间隔是可选的环境变量：

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**摄取** — 内置的 OTLP 接收器可在 `/v1/traces` 和 `/v1/metrics` 接收来自其他任何来源的 trace 和 metric（`pip install clawmetry[otel]` 以启用 protobuf 摄取）。

你既获得零配置、本地优先的 ClawMetry 仪表盘，**也能**把数据存放进你团队已有的任意后端，没有锁定，也无需安装第二个智能体。

## 配置

大多数人不需要任何配置。ClawMetry 会自动检测你的工作区、日志、会话和 cron。

如果你确实需要自定义：

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

全部选项：`clawmetry --help`

## 支持的渠道

ClawMetry 会展示你已配置的每一个 OpenClaw 渠道的实时活动。只有在你的 `openclaw.json` 中实际设置过的渠道才会出现在 Flow 图中，未配置的会被自动隐藏。

点击 Flow 中的任意渠道节点，即可看到带有收发消息计数的实时聊天气泡视图。

| 渠道 | 状态 | 实时弹窗 | 备注 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完整 | ✅ | 消息、统计、10s 刷新 |
| 💬 **iMessage** | ✅ 完整 | ✅ | 直接读取 `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ 完整 | ✅ | 通过 WhatsApp Web（Baileys） |
| 🔵 **Signal** | ✅ 完整 | ✅ | 通过 signal-cli |
| 🟣 **Discord** | ✅ 完整 | ✅ | 服务器 + 频道检测 |
| 🟪 **Slack** | ✅ 完整 | ✅ | 工作区 + 频道检测 |
| 🌐 **Webchat** | ✅ 完整 | ✅ | 内置 Web UI 会话 |
| 📡 **IRC** | ✅ 完整 | ✅ | 终端风格的气泡界面 |
| 🍏 **BlueBubbles** | ✅ 完整 | ✅ | 通过 BlueBubbles REST API 接入 iMessage |
| 🔵 **Google Chat** | ✅ 完整 | ✅ | 通过 Chat API webhook |
| 🟣 **MS Teams** | ✅ 完整 | ✅ | 通过 Teams bot 插件 |
| 🔷 **Mattermost** | ✅ 完整 | ✅ | 自托管团队聊天 |
| 🟩 **Matrix** | ✅ 完整 | ✅ | 去中心化，支持 E2EE |
| 🟢 **LINE** | ✅ 完整 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完整 | ✅ | 去中心化的 NIP-04 私信 |
| 🟣 **Twitch** | ✅ 完整 | ✅ | 通过 IRC 连接接入聊天 |
| 🔷 **Feishu/Lark** | ✅ 完整 | ✅ | WebSocket 事件订阅 |
| 🔵 **Zalo** | ✅ 完整 | ✅ | Zalo Bot API |

> **自动检测：** ClawMetry 读取你的 `~/.openclaw/openclaw.json`，只渲染你实际配置过的渠道。无需手动设置。

## Docker 部署

想在容器中运行 ClawMetry？没问题！🐳

**用 Docker 快速开始：**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **注意：** 在 Docker 中运行时，务必挂载你的 OpenClaw 工作区和日志目录，以便 ClawMetry 能自动检测你的环境。

## 环境要求

- Python 3.8+
- Flask（通过 pip 自动安装）
- 在同一台机器上运行的 OpenClaw（或为 Docker 挂载的卷）
- Linux 或 macOS

## NemoClaw / OpenShell 支持

ClawMetry 会自动检测 [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA 面向 OpenClaw 的企业级安全封装，它让智能体在沙箱化的 OpenShell 容器内运行。

大多数情况下无需额外配置。无论会话文件位于宿主机的 `~/.openclaw/` 还是某个 OpenShell 容器内部，同步守护进程都会自动发现它们。

### 工作原理

ClawMetry 通过两种方式检测 NemoClaw：

1. **二进制检测** — 检查 `nemoclaw` CLI 并运行 `nemoclaw status` 以获取沙箱信息
2. **容器检测** — 扫描运行中的 Docker 容器，查找 `openshell`、`nemoclaw` 或 `ghcr.io/nvidia/` 镜像，然后通过卷挂载或 `docker cp` 读取会话

从 NemoClaw 容器同步过来的会话文件，会在云端仪表盘中被标注 `runtime=nemoclaw` 和 `container_id` 元数据，因此你可以一眼把它们与标准 OpenClaw 会话区分开。

### 推荐设置：在宿主机上运行同步守护进程

为获得最佳体验，请在**宿主机**上（而非沙箱内）运行 ClawMetry 的同步守护进程。这样可以避免 NemoClaw 网络策略限制。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同步守护进程会自动找到任意运行中的 OpenShell 容器内部的会话。

### 可选：显式指定沙箱名

如果自动检测不起作用，请把 ClawMetry 指向正确的沙箱：

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### 在沙箱内部运行（高级）

如果你必须在 OpenShell 沙箱**内部**运行同步守护进程，请在你的 NemoClaw 网络策略中添加如下出站规则，使其能够访问 ClawMetry 摄取 API：

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

通过以下命令应用：

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### 端口与端点

| 端点 | 端口 | 协议 | 是否必需 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 是（同步守护进程 → 云端） |
| `localhost:8900` | 8900 | HTTP | 是（本地仪表盘 UI） |
| Docker socket（`/var/run/docker.sock`） | — | Unix socket | 用于容器会话发现 |

同步守护进程只会向 `ingest.clawmetry.com` 发起出站 HTTPS 调用。无需任何入站端口。

---

## 云端部署

关于 SSH 隧道、反向代理和 Docker，请参阅 **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**。

## 测试

本项目使用 BrowserStack 进行测试。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## 遥测

当你在一台新机器上首次运行 `clawmetry` CLI 时，ClawMetry 会向 `https://app.clawmetry.com/api/install` 发送一次匿名的“首次运行”ping。我们用它来统计安装量（这是我们这个 OSS 项目唯一拥有的营销指标），并了解用户安装了哪些智能体框架。

**每次安装恰好一个 POST**，包含：

| 字段 | 示例 | 用途 |
|---|---|---|
| `install_id` | 存储于 `~/.clawmetry/install_id` 的随机 UUID | 去重；不与你的 email 或 api_key 关联 |
| `version` | `0.12.167` | 了解线上有哪些版本 |
| `os` / `os_version` | `Darwin` / `25.3.0` | 平台支持优先级 |
| `python` | `3.11.15` | Python 版本支持矩阵 |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 接下来我们应优先集成哪些智能体 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 将人工安装与 CI 噪声区分开 |

**我们不发送的内容**：IP（云端会在服务端从请求中推导出国家码，然后丢弃 IP）、主机名、用户名、工作区路径、文件内容、你的 api_key、你的 email，以及任何 PII 或与工作区相关的信息。线上传输的载荷可在 [`clawmetry/telemetry.py`](clawmetry/telemetry.py) 中审计。

**退出**（以下任意一种都会永久禁用它）：

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

此处的网络失败绝不会阻止 `clawmetry` 运行 — 该 ping 在守护线程上以即发即忘方式发送，超时为 3 秒。

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
  <strong>🦞 See your agent think</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
