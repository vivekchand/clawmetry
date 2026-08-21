<!-- i18n-src:dc34072b2955 -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看见你的智能体在思考。** 面向 **23 种 AI 智能体运行时**的实时可观测性方案：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及其他 19 种。一个仪表盘,覆盖你的整个智能体机群。

> 🌐 **切换语言：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多语言 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置：它会找到你机器上已有的智能体运行时,以只读方式读取它们,不改变它们的任何运行方式。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支持 23 种智能体运行时

**开源应用中免费：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**付费计划中包含：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

每种运行时都能使用同一个仪表盘。同时运行多个运行时,顶部切换器会将每个标签页重新聚焦到其中一个。

用某个 SDK 自己搭建了智能体?拦截器同样可以追踪它的 LLM 调用。参见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**：每个智能体逐轮做了什么,支持回放
- **成本与令牌**：按运行时、模型、会话和日期统计,并带异常标记
- **Flow**：消息在渠道、模型和工具之间流转的实时图示
- **Brain**：实时呈现推理与工具调用事件流
- **Memory 与 skills**：每个运行时实际加载的文件和技能
- **Health 与日志**：磁盘、内存、错误率、速率限制、实时日志流
- **Alerts**：预算上限、错误突增、智能体离线,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **Approvals**：在高风险工具调用*执行前*暂停,并可在手机上审批([了解方式](docs/APPROVALS.md))

## 定价

| 计划 | 覆盖范围 | 价格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw,完整仪表盘,仅限本地 | $0 |
| **Starter** | 上述其他所有运行时、机群视图、云同步 | 每节点每月 $9 |
| **Pro** | Starter + 治理能力：审批、工具风险策略、评估、异常检测、成本优化器、OTel 导出 | 每节点每月 $19 |

年付方案、企业版及最新价格见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管许可证密钥
无需云端即可使用(`clawmetry license`)。免费/付费的详细划分见
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你的机器上

ClawMetry 读取本地会话文件和日志。除非你运行 `clawmetry connect`,
否则不会有任何数据离开你的设备。即便如此,快照也会使用一个永远不会
离开你机器的密钥进行端到端加密,并在你的浏览器中解密。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或使用一行命令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要在 macOS、Linux 或 Windows 上运行 Python 3.8+,并且同一台机器上至少
安装了一种智能体运行时。Docker 说明见 [docs/DOCKER.md](docs/DOCKER.md)。

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取的内容,以及如何添加新的运行时 |
| [权益(Entitlements)](docs/ENTITLEMENTS.md) | 免费 vs 付费、层级矩阵、许可证 CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前门控、风险评分、手机审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任何地方,从任何来源接收 OTLP |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自己构建的智能体做成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 配置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理;从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名的安装与桌面打开 ping,以及如何关闭它们 |

## 截图

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**：令牌、会话、健康状态 | **Brain**：实时智能体事件流 |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**：按模型和会话统计 | **Approvals**：为高风险工具调用设置门控 |

按运行时查看更多截图：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## Star 历史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 许可证

MIT · 由 [@vivekchand](https://github.com/vivekchand) 构建 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
