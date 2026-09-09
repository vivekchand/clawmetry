<!-- i18n-src:61beb8393e2f -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**一个智能体可以调用一百次工具却毫无进展。** ClawMetry
读取你的编码智能体已经在写入的会话文件，并将时间线、
工具调用以及运行时所暴露的任何 token 和成本数据整合到一个
视图中——这样你就能分辨出一次长时间运行是在正常推进，还是已经卡住了。

支持 **30 种 AI 智能体运行时**——Claude Code、OpenAI Codex、Hermes、OpenClaw 及另外 26 种。一个仪表盘管理你整个智能体机群。（[完整列表](SUPPORTED_RUNTIMES.txt)，由目录自动生成。）

> 🌐 **切换语言：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置：它会找到你机器上已有的
智能体运行时，以只读方式读取它们，不会改变它们的任何运行方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安装前须知

| | |
|---|---|
| **它做什么** | 读取你的智能体已经在写入的会话文件和日志。无需 SDK，无需改代码，不在你的应用中植入任何埋点。 |
| **你能看到什么** | 会话时间线、逐工具回放、token 和成本明细，以及轨迹信号（循环、重复失败）——按运行时区分。 |
| **哪些是免费的** | `pip install clawmetry` 可以读取 **OpenClaw、NVIDIA NemoClaw 和 Goose**，无需账户、无需密钥、也不发出任何网络请求。另外 27 种——Claude Code、Codex、Cursor 及其余——由闭源的 `clawmetry-pro` 配套组件读取，该组件随 7 天试用或付费套餐一起提供——精确的划分见 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何开始** | `pip install clawmetry && clawmetry`，然后打开 localhost:8900。这台机器上还没有智能体？`clawmetry --sample` 会打开三个标注清楚的合成会话。 |
| **哪些数据会离开你的机器** | 除非你运行 `clawmetry connect`，否则没有任何会话数据会离开。默认会运行两件事，均可关闭，且都不携带会话内容：一次匿名安装 ping 和一次 PyPI 版本检查。每一个目的地都在 [docs/EGRESS.md](docs/EGRESS.md) 中列出，该清单是通过抓包重建的，而不是靠读代码注释得来的。 |

在你评判输出之前，有两个限制值得了解：不同运行时暴露的数据差异很大（有些完全不发布成本数据——[对照表](docs/compatibility.md) 会按运行时说明哪些可以），并且能观察到某个动作并不等于能够阻止它（[各运行时的实际可控能力](docs/APPROVALS.md)）。


## 支持 30 种智能体运行时

**开源应用中免费：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付费套餐中：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每种运行时都拥有相同的仪表盘。同时运行多个时，顶部的切换器
可以把每个标签页重新定位到其中任意一个。

用某个 SDK 自己搭建了智能体？拦截器同样会追踪它的 LLM 调用。
详见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与会话记录**：每个智能体逐轮做了什么，支持回放
- **成本与 token**：按运行时、模型、会话和天数划分，并带有异常标记
- **Flow（流程）**：消息在频道、模型和工具之间流动的实时图示
- **Brain（推理流）**：推理过程和工具调用事件流的实时呈现
- **上下文溢出**：按提供商精确计算的窗口利用率、区分压缩（compaction）与强制溢出，以及按运行时列出我们*看不到*什么的对照图（[原理](docs/CONTEXT_BLOWOUT.md)）
- **记忆与技能**：每个运行时实际加载的文件和技能
- **健康状况与日志**：磁盘、内存、错误率、速率限制、实时日志流
- **告警**：预算上限、错误突增、智能体离线，可推送至 Slack、Discord、PagerDuty、Telegram、Email
- **审批**：在风险工具调用*执行前*暂停并在手机上批准（[原理](docs/APPROVALS.md)）

## 上下文溢出，以及监控的成本

在你信任任何智能体对比工具之前，值得先回答两个问题。

**它如何处理跨运行时的上下文窗口溢出？**

利用率百分比的可信度，取决于它的分母是否诚实。ClawMetry
按提供商从[一份你可以阅读并提交 PR 的表格](clawmetry/context_windows.py)中确定窗口大小，
涵盖 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不会用某一家供应商的
标尺去衡量全部 30 种运行时。这一点很重要：一次 300K 的 GPT-5 轮次，
如果按 Anthropic 的 200K 计算，会显示为">100%，已溢出"，
但实际上它只用了 GPT-5 400K 窗口的 75%。同一把标尺也会把一次真正溢出的
130K DeepSeek 轮次，掩盖成看起来舒适的 65%。

每个窗口都附带其来源标注：`model_table`、`explicit_marker`、
`observed_floor`，或者当我们不知道模型时给出诚实的 `default`。
基于猜测构建的仪表盘，永远不该以和基于查表构建的仪表盘同等的权威性呈现。

ClawMetry 只能在部分运行时上看到压缩（compaction）事件。因此
`GET /api/context-coverage` 会按运行时报告，**0 表示"运行干净"
还是"我们看不到"**。真正意味着"看不到"的 `0`，会明确说明这一点。
[详情](docs/CONTEXT_BLOWOUT.md)

**这套埋点的成本是多少？**

| 路径 | 给你的智能体增加的开销 | 默认开启？ |
|---|---|---|
| 会话文件尾随读取（全部 30 种运行时） | **0**。独立进程，你的智能体中没有任何 ClawMetry 代码 | 是 |
| HTTP 拦截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 调用 **+0.44 毫秒**，相当于一次 5 秒调用的 0.009% | 否 |
| 前置工具钩子门（热缓存） | 每次受控工具调用 **+44 毫秒**，高于 36 毫秒的解释器基线 | 否 |
| 执行代理（enforcement proxy） | 每次 LLM 调用 **+9.7 毫秒** | 否 |

守护进程宿主开销：**每秒 2,762 个事件**的摄取速度，磁盘上每事件 **710 字节**
（每 10 万事件 67.7 MB），繁忙安装环境下持续占用 **约 12% 的单核**。
最后这个数字超出了我们自己设定的 5%-10% 预算，因此它作为一个
需要追查的问题被公开发布，而不是隐藏不提。

在 Apple M2 Pro 上使用 `benchmarks/overhead.py` 测得。该测试框架为每种情况
运行独立进程，交替执行顺序，并且**当多轮结果符号不一致时拒绝给出数字**。
你可以在自己的机器上花一分钟运行它：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每条路径都经过测量，包括钩子门和执行代理，
并且该测试框架在 CI 中于 Linux、macOS 和 Windows 上运行。有两个结果值得了解：
执行代理在 Windows 上的开销约为 Linux 上的七倍，而守护进程目前
持续占用约 12% 的单核，超出了我们自己设定的 5%-10% 预算。原始 JSON 数据、
测量方法，以及尚未测量的部分都在
[docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定价

| 套餐 | 涵盖内容 | 价格 |
|---|---|---|
| **免费版** | OpenClaw + NVIDIA NemoClaw + Goose，完整仪表盘，仅本地 | $0 |
| **入门版** | 上述所有其他运行时、机群视图、云同步 | 每节点每月 $9 |
| **专业版（Pro）** | 入门版 + 控制与评估能力：审批、工具风险策略、评估（evals）、异常检测、成本优化器、OTel 导出、防篡改审计日志 | 每节点每月 $19 |

年付套餐、企业版及当前价格详见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管的授权密钥
无需云端即可使用（`clawmetry license`）。免费与付费的确切划分
见 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地会话文件和日志。**除非你运行 `clawmetry connect`，
否则没有任何会话数据会离开你的机器**——不包括提示词、回复、工具参数、
文件内容或日志行。当你确实连接时，快照会使用一个永不离开你机器的密钥
进行端到端加密，并在你的浏览器中解密。如果某个节点没有密钥，
上传会被跳过，而不是以明文发送，任何服务器响应都无法关闭这一保护。

在你连接之前，默认会运行两件事，均可关闭，且都不携带会话数据：
一次匿名安装 ping 和针对 PyPI 的版本检查。默认安装还会为启动横幅
查询一次你的公共 IP。每个目的地、它携带的内容以及如何关闭它，
都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；自托管、重新指向以及
完全离线（air-gapped）的安装不会发出任何可选的对外调用。

解密发生在你的浏览器中，运行的是我们提供给你的代码。这原本只是一个承诺；
现在你可以自行核实。所有涉及你密钥的代码都在一个可读的文件中，
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)，
它随 wheel 包一起分发，并原样提供，并附有子资源完整性（Subresource
Integrity）哈希固定。要确认浏览器运行的正是我们发布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

这无法证明什么：我们提供加载该文件的页面，所以我们同样可以提供
一个不同的页面。完整性哈希能保护你免受 CDN 被攻破的影响，
但无法保护你免受供应商本身的行为影响。你所获得的是：任何替换都必须是
蓄意的、在页面源码中可见的，并且与任何人都能从 PyPI 获取到的构件不同。
自托管或仅本地运行，则完全消除了这种依赖。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或者使用一行命令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+，且同一台机器上
至少有一个智能体运行时。Docker 使用说明见 [docs/DOCKER.md](docs/DOCKER.md)。

或者让智能体替你完成安装。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能会教 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode
安装 ClawMetry、汇报机器上的智能体正在做什么和花费多少，
根据请求停止某个会话，并将高风险工具调用挂起等待审批：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取的内容，以及如何添加一个新运行时 |
| [上下文溢出](docs/CONTEXT_BLOWOUT.md) | 按提供商划分的窗口大小、压缩与溢出的区别、按运行时的覆盖情况 |
| [开销](docs/OVERHEAD.md) | 埋点带来的成本，经过实测，并提供可复现的测试框架 |
| [权益（Entitlements）](docs/ENTITLEMENTS.md) | 免费与付费对比、套餐矩阵、授权 CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前拦截、风险评分、手机端审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任意目的地，从任意来源摄取 OTLP |
| [接入你自己的智能体](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 的端到端示例，附可运行代码 |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自己搭建的智能体做成本归因 |
| [聊天频道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 配置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理；从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名安装及桌面端打开 ping，以及如何关闭它们 |

## 截图

以下每一个数字都来自一台真实机器，只读获取，未做任何预置数据。

**它会告诉你哪里出了问题，而不只是发生了什么。**
顶部两条异常横幅：花费达到日均的 7 倍，以及一次 4.2 倍的成本突增。
下方，667 个最近会话中有 324 个带有浪费信号，并按原因逐项列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它会告诉你钱都花在哪里，在每一个时间窗口内。**
今天 $252.47，本周 $513.15，本月 $1,312.92，每一项都附带其背后的 token 数
以及你的订阅已经覆盖了多少。下方，约 $1,128/月被列为可回收，
约 $17,256/月已通过缓存复用节省下来。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它会绘制一条消息如何变成一个答案的过程。**
实时流程图：你、消息抵达的频道、网关、正在应答的模型，
以及它调用的每一个工具。节点会在工作流经它们时点亮。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**机器上的每一个智能体，一张表全览。**
它在运行什么、过去 24 小时和整个生命周期的花费、
最后一次出现的时间、归属于谁，以及是否有订阅覆盖账单。
这里共有 14 个智能体，3 个会话正在工作，13 个处于空闲。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它会逐个工具地展示一轮对话的时间和金钱去向。**
一次真实会话中的一轮：11 个工具，耗时 11.2 分钟，花费 $1.16。
每一次 Bash 调用和模型调用在时间线上都有自己的条形图，
因此运行了 4.1 分钟的命令和运行了 226 毫秒的命令一眼就能区分开。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它评判的是工作质量，而不仅仅是花费。**
本周评级为 A：54 个任务顺利完成，2 个存在问题的任务花费了 $48.57，
而那些活动量太少、无法评判的运行不会被计入评级中的"胜利"。
每一个存在问题的运行都链接到它的追踪记录。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它会展示上下文窗口为何不断被填满。**
最新一轮使用了 1M token 窗口中的 715K，峰值利用率 83.3%，
4 次压缩全部是主动触发而非因溢出被迫触发，并展示其背后每一轮的利用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**检测无需你做任何配置即可运行。**
内置检测器安装后即默认开启：智能体沉默、遥测数据流中断、
成本突增、token 突增、错误率上升、错误突增、
预算阈值、威胁特征匹配、安全工具发现、安全态势变化。
你自己的规则可以在此基础上选择性叠加。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**拦截高风险调用是可选启用的，且默认关闭发货。**
递归删除、强制推送、sudo、密钥、包安装以及对外调用，
每一项都有一条可以单独开启的规则。在你开启之前，ClawMetry 只观察，
不改变任何东西。一旦开启，匹配的调用会在此处（或你的手机上）
等待批准或拒绝。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多按运行时划分的截图：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 获得的认可

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
