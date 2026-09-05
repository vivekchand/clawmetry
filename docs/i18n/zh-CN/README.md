<!-- i18n-src:88be2deff5d5 -->
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

**看见你的智能体在想什么。** 面向 **30 种 AI 智能体运行时**的实时可观测性方案：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 26 种。一个仪表盘，覆盖你的整个智能体机队。

> 🌐 **其他语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置：它会找到你机器上已有的智能体运行时，以只读方式读取它们，不改变它们的任何运行方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 支持 30 种智能体运行时

**开源应用中免费提供：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付费计划中提供：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每种运行时使用同一个仪表盘。同时运行多个运行时，页面顶部的切换器会把每个标签页重新限定到其中一个。

用某个 SDK 自己搭建了智能体？拦截器同样会追踪它的 LLM 调用。参见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**：每个智能体做了什么，逐轮记录，并可回放
- **成本与令牌**：按运行时、模型、会话和天数统计，附带异常标记
- **流程图**：消息在渠道、模型和工具之间流动的实时图示
- **Brain**：实时呈现推理与工具调用事件流
- **上下文爆量**：按提供方精确计算窗口利用率、区分压缩与强制溢出，并附带每个运行时"看不到什么"的地图（[原理](docs/CONTEXT_BLOWOUT.md)）
- **记忆与技能**：每个运行时实际加载的文件与技能
- **健康与日志**：磁盘、内存、错误率、速率限制、实时日志流
- **告警**：预算上限、错误激增、智能体离线，可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **审批**：在风险工具调用*执行前*暂停，并可在手机上完成审批（[原理](docs/APPROVALS.md)）

## 上下文爆量，以及监控本身的代价

在信任任何智能体对比工具之前，有两个问题值得先弄清楚。

**它如何应对跨运行时的上下文窗口爆量？**

利用率百分比的可信度，取决于它的分母是否诚实。ClawMetry 按提供方从[一张你可以阅读并提交 PR 的表](clawmetry/context_windows.py)中确定窗口大小，覆盖 Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不会用某一家厂商的尺子去衡量全部 30 种运行时。这一点很重要：一个 300K 的 GPT-5 轮次如果用 Anthropic 的 200K 去衡量,会显示">100%，已爆量"，但实际上只是 GPT-5 自身 400K 窗口的 75%。同一把尺子也会把一个真正溢出的 130K DeepSeek 轮次,掩盖成看似舒适的 65%。

每个窗口值都附带其来源：`model_table`、`explicit_marker`、`observed_floor`，或者在我们不认识该模型时诚实地标为 `default`。一个建立在猜测之上的仪表,绝不会以和查表得来的数值同等的权威性呈现。

ClawMetry 只能在部分运行时上看到压缩事件。因此 `GET /api/context-coverage` 会针对每个运行时报告,一个 0 到底代表"干净运行完成"还是"我们看不到"。真正代表"看不到"的 0 会明确说明这一点。[完整说明](docs/CONTEXT_BLOWOUT.md)

**这套埋点本身的开销是多少？**

| 路径 | 加到你的智能体上的开销 | 是否默认开启？ |
|---|---|---|
| 会话文件追踪(全部 30 种运行时) | **0**。独立进程，你的智能体中不含任何 ClawMetry 代码 | 开启 |
| HTTP 拦截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 调用 **+0.44 毫秒**，相当于一次 5 秒调用的 0.009% | 关闭 |
| 工具调用前的钩子门（热缓存） | 每次受控工具调用 **+44 毫秒**，基于 36 毫秒的解释器基线之上 | 关闭 |
| 强制执行代理 | 每次 LLM 调用 **+9.7 毫秒** | 关闭 |

守护进程主机开销：摄取速率 **每秒 2,762 个事件**，磁盘上**每个事件 710 字节**（每 10 万个事件占用 67.7 MB），繁忙安装环境下持续占用**约 12% 的单核 CPU**。最后这个数字超出了我们自己设定的 5-10% 预算，因此我们把它作为一个待解决的 bug 公开出来，而不是藏起来。

在 Apple M2 Pro 上使用 `benchmarks/overhead.py` 测得。该测试工具在独立进程中运行每种条件，交替执行顺序，并且**在多轮结果符号不一致时拒绝给出数字**。你可以在自己的机器上花一分钟运行它：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每条路径都经过测量，包括钩子门和强制执行代理，测试工具在 CI 中的 Linux、macOS 和 Windows 上都会运行。有两个结果值得了解：代理在 Windows 上的开销大约是 Linux 上的七倍，且守护进程目前持续占用约 12% 的单核，超出了我们自己设定的 5-10% 预算。原始 JSON 数据、测量方法，以及尚未测量的部分，都在 [docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定价

| 计划 | 覆盖范围 | 价格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose，完整仪表盘，仅本地 | $0 |
| **Starter** | 以上之外的所有其他运行时、机队视图、云同步 | 每节点每月 $9 |
| **Pro** | Starter 的全部功能 + 控制与评估：审批、工具风险策略、评估、异常检测、成本优化器、OTel 导出、防篡改审计日志 | 每节点每月 $19 |

年付计划、企业版及最新价格详见 **[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管的许可证密钥无需云端即可使用（`clawmetry license`）。免费与付费功能的精确划分见 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地的会话文件和日志。**除非你运行 `clawmetry connect`，否则没有任何会话数据会离开你的机器**——不包括提示词、回复、工具参数、文件内容或日志行。当你确实连接时，快照会使用一个永不离开你机器的密钥进行端到端加密，并在你的浏览器中解密。如果某个节点没有密钥，上传会被跳过，而不是明文发送，而且没有任何服务器响应能够关闭这一保护。

在你连接之前，默认会运行两件事，都可以选择关闭，且都不携带任何会话数据：一次匿名的安装 ping 和一次针对 PyPI 的版本检查。默认安装还会查询一次你的公网 IP，用于启动横幅中的一行信息。每个目的地、它携带的内容以及如何关闭它，都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；自托管、重定向和气隙（air-gapped）安装完全不会发出任何非必要的出站调用。

解密发生在你的浏览器里，运行的是我们提供给你的代码。这一点过去只是一个承诺；现在你可以自己核实。所有涉及你的密钥的代码都在一个可读的文件里，[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)，它随 wheel 一起打包发布，并原样提供，同时附带子资源完整性（Subresource Integrity）哈希固定。要确认浏览器运行的确实是我们发布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

这无法证明的是：我们同时也在提供加载该文件的页面，所以理论上我们可以提供一个不同的页面。完整性哈希能保护你免受 CDN 被攻破的影响,但无法防范来自厂商本身的问题。你能获得的是，任何替换都必须是刻意为之、在页面源码中可见，并且和任何人都能从 PyPI 上下载到的构件不同。选择自托管或仅在本地运行,能彻底消除这种依赖。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或者用一条命令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8 及以上版本，以及同一台机器上至少一个智能体运行时。Docker 安装说明见：[docs/DOCKER.md](docs/DOCKER.md)。

或者让智能体帮你完成安装。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) 技能可以教 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode 安装 ClawMetry，报告机器上各个智能体正在做什么、花了多少钱，按需停止某个会话，并将风险工具调用挂起等待审批：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取什么，以及如何添加一个运行时 |
| [上下文爆量](docs/CONTEXT_BLOWOUT.md) | 按提供方划分的窗口大小、压缩与溢出的区分、各运行时的覆盖情况 |
| [开销](docs/OVERHEAD.md) | 埋点的实测开销，以及用于复现的测试工具 |
| [权益](docs/ENTITLEMENTS.md) | 免费与付费对比、层级矩阵、许可证 CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前门控、风险评分、手机审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任意位置，从任意来源摄取 OTLP |
| [接入你自己的智能体](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 的端到端示例，含可运行代码 |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自己搭建的智能体进行成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 环境搭建 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理；从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名的安装与桌面端打开 ping，以及如何关闭它们 |

## 截图

以下每一个数字都来自一台真实机器，只读采集，没有任何预先构造的数据。

**它会告诉你哪里出了问题，而不只是发生了什么。**
页面顶部有两条异常横幅：支出达到日均水平的 7 倍，以及一次 4.2 倍的成本激增。下方，667 个最近会话中有 324 个带有浪费信号，并按原因逐项列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它展示钱花在了哪里，覆盖每一个时间窗口。**
今天 $252.47，本周 $513.15，本月 $1,312.92，各自附带背后的令牌用量，以及你的订阅已经覆盖了其中多少。下方，约 $1,128/月被列为可回收成本，而缓存复用已经节省了约 $17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它描绘出一条消息是如何变成一个答案的。**
实时流程图：你、消息到达的渠道、网关、正在作答的模型，以及它调用的每一个工具。节点会随着工作在其中流动而亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**机器上的每一个智能体，一张表全部呈现。**
它运行什么、过去 24 小时和整个生命周期的花费、最后一次活跃时间、归属人，以及是否有订阅在覆盖账单。这里有 14 个智能体，3 个会话正在工作，13 个处于空闲。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它逐个工具展示一轮对话的时间和金钱花在了哪里。**
一次真实会话中的一轮：11 个工具，耗时 11.2 分钟，花费 $1.16。每一次 Bash 调用和模型调用都在时间轴上有自己的条形，因此运行了 4.1 分钟的命令和只运行了 226 毫秒的命令一眼就能区分开。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它评判的是工作成果,而不仅仅是花费。**
本周评级为 A：54 个任务干净完成,2 个粗糙的任务花费了 $48.57,而活动量太少、无法判断质量的运行会被排除在评级之外，而不是被算作成功。每一个粗糙的运行都链接到其追踪记录。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它展示了上下文窗口为什么不断被占满。**
最新一轮占用了 100 万令牌窗口中的 71.5 万，峰值利用率 83.3%，4 次压缩全部是主动触发,而非因溢出而触发，以及其背后每一轮的利用率数据。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**检测无需你做任何配置即可运行。**
内置检测器从安装那一刻起就已开启：智能体沉默、遥测数据流中断、成本激增、令牌突增、错误率上升、错误激增、预算阈值、威胁特征匹配、安全工具发现、安全态势变化。你自己的规则是可选的补充。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**挂起风险调用是可选启用的功能，且默认不生效。**
递归删除、强制推送、sudo、密钥泄露、软件包安装和出站调用,各自都有一条可以开启的规则。在你开启之前，ClawMetry 只是观察，不会改变任何事情。一旦开启，匹配的调用会在这里（或你的手机上）等待批准或拒绝。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多按运行时划分的截图：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
