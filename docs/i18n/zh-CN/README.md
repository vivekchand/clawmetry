<!-- i18n-src:c111f32e69a5 -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看看你的智能体在想什么。** 面向 **26 种 AI 智能体运行时**的实时可观测性工具：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 22 种。一个仪表盘，管理你的整个智能体舰队。

> 🌐 **本文档语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置：它会找到你机器上已有的智能体运行时，以只读方式读取它们的数据，不会改变它们的任何运行方式。

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 支持 26 种智能体运行时

**开源应用中免费：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付费套餐中支持：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每种运行时都使用同一个仪表盘。可以同时运行多个，页头的切换器会把每个标签页重新聚焦到其中一个运行时上。

用 SDK 自己搭建了智能体，而不是用某个现成运行时？拦截器同样会追踪它的 LLM 调用。详见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**：每个智能体逐轮做了什么,可回放
- **成本与 Token**：按运行时、模型、会话和天数统计,并标记异常
- **Flow**：消息在渠道、模型和工具之间流动的实时图示
- **Brain**：实时展现推理与工具调用事件流
- **记忆与技能**：每个运行时实际加载过的文件与技能
- **健康状况与日志**：磁盘、内存、错误率、速率限制、实时日志流
- **告警**：预算上限、错误激增、智能体离线,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **审批**：在高风险工具调用*执行前*暂停,并可从手机端批准（[了解详情](docs/APPROVALS.md)）

## 定价

| 套餐 | 覆盖范围 | 价格 |
|---|---|---|
| **免费版** | OpenClaw + NVIDIA NemoClaw + Goose,完整仪表盘,仅限本地 | $0 |
| **入门版** | 以上以外的所有运行时,舰队视图,云同步 | 每节点每月 $9 |
| **Pro** | 入门版 + 治理能力：审批、工具风险策略、评测、异常检测、成本优化器、OTel 导出 | 每节点每月 $19 |

年付方案、企业版及最新价格见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管授权密钥
无需云端即可使用（`clawmetry license`）。免费/付费的具体划分见
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地会话文件与日志。除非你运行了 `clawmetry connect`，
否则任何数据都不会离开你的设备。即便运行了该命令,快照也会使用一个
永不离开你机器的密钥进行端到端加密,并在你的浏览器中解密。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或使用一键安装命令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+，以及同一台机器上至少运行
一种智能体运行时。Docker 使用说明见：[docs/DOCKER.md](docs/DOCKER.md)。

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取哪些内容,以及如何新增一种运行时 |
| [权益（Entitlements）](docs/ENTITLEMENTS.md) | 免费与付费对比、套餐矩阵、授权 CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前拦截、风险评分、手机端审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任意位置,从任意来源接入 OTLP |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自建的智能体做成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 配置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理;从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名安装与桌面打开的上报,以及如何关闭它们 |

## 截图

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**：Token、会话、健康状况 | **代理** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**：按模型和会话统计 | **Approvals**：拦截高风险工具调用 |

更多按运行时划分的截图见：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
