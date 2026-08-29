<!-- i18n-src:d21bea5161e0 -->
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

**看见你的智能体在想什么。** 面向 **30 种 AI 智能体运行时**的实时可观测性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及另外 26 种。一个面板管理你的整支智能体舰队。

> 🌐 **阅读其他语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置：它会找到你机器上已有的智能体运行时，以只读方式读取它们,不会改变它们的运行方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 支持 30 种智能体运行时

**开源应用中免费提供：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付费方案中提供：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每种运行时都使用同一套面板。同时运行多个时,顶部的切换器会把每个标签页重新聚焦到其中一个上。

用 SDK 自己搭建了智能体,而不是用现成运行时?拦截器同样会追踪它的 LLM 调用。参见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**：每个智能体逐轮做了什么,支持回放
- **成本与 Token**：按运行时、模型、会话和天数统计,带异常标记
- **流程图（Flow）**：消息在渠道、模型和工具之间流动的实时图
- **思维（Brain）**：推理与工具调用事件流,实时呈现
- **上下文爆量（Context blowout）**：按提供商正确计算的窗口利用率、压缩 vs 强制溢出的区分,以及每种运行时“我们看不到什么”的地图（[原理](docs/CONTEXT_BLOWOUT.md)）
- **记忆与技能**：每个运行时实际加载过的文件和技能
- **健康与日志**：磁盘、内存、错误率、速率限制、实时日志流
- **告警**：预算上限、错误突增、智能体离线,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **审批**：在有风险的工具调用*执行前*暂停,并可在手机上批准（[原理](docs/APPROVALS.md)）

## 上下文爆量,以及监控本身的代价

在你信任任何智能体对比工具之前,这两个问题值得先弄清楚。

**它如何在不同运行时之间处理上下文窗口爆量？**

利用率百分比的可信度,取决于它的分母是否诚实。ClawMetry 按提供商从[一张你可以阅读并提交 PR 的表](clawmetry/context_windows.py)中确定窗口大小,涵盖 Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不会用某一家供应商的标尺去衡量全部 26 种运行时。这很重要：一个 300K 的 GPT-5 轮次如果拿 Anthropic 的 200K 去打分,会显示“>100%,已爆量”,但实际上它只用了 GPT-5 自身 400K 窗口的 75%。同一把标尺也会把一个真正溢出的 130K DeepSeek 轮次,掩盖成看似舒适的 65%。

每个窗口值都带有其来源标注：`model_table`、`explicit_marker`、`observed_floor`,或者在我们不知道模型时诚实标注为 `default`。基于猜测构建的仪表盘,永远不该以和基于查表构建的仪表盘同等的权威性呈现。

ClawMetry 只能在部分运行时上看到压缩（compaction）事件。因此 `GET /api/context-coverage` 会针对每种运行时报告：**一个 0 究竟意味着“干净地跑完了”,还是“我们看不见”**。真正意味着“看不见”的 0 会如实说明。[完整细节](docs/CONTEXT_BLOWOUT.md)

**这套监控本身的开销是多少？**

| 路径 | 加到你的智能体上的开销 | 默认开启？ |
|---|---|---|
| 会话文件尾随读取（全部 30 种运行时） | **0**。独立进程,你的智能体中不含任何 ClawMetry 代码 | 开启 |
| HTTP 拦截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 调用 **+0.44 毫秒**,相当于一次 5 秒调用的 0.009% | 关闭 |
| 工具前置钩子闸门（热缓存） | 每次受控工具调用 **+44 毫秒**,基于 36 毫秒的解释器底线之上 | 关闭 |
| 强制执行代理 | 每次 LLM 调用 **+9.7 毫秒** | 关闭 |

守护进程主机开销：摄取 **2,762 事件/秒**,磁盘上**每事件 710 字节**（每 10 万事件 67.7 MB）,在繁忙安装上持续占用**约 12% 的单核**。最后这个数字超出了我们自己设定的 5-10% 预算,因此我们把它作为一个待解决的问题公开出来,而不是隐藏不提。

在 Apple M2 Pro 上使用 `benchmarks/overhead.py` 测得。该测试框架在独立进程中运行每种条件,交替其顺序,并且**在多轮结果符号不一致时拒绝给出数字**。你可以在自己的机器上用一分钟跑一遍：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每条路径都经过测量,包括钩子闸门和强制执行代理,该测试框架在 CI 中于 Linux、macOS 和 Windows 上运行。有两个结果值得留意：代理在 Windows 上的开销约为 Linux 的七倍,而守护进程目前持续占用约 12% 的单核,超出了我们自己设定的 5-10% 预算。原始 JSON 数据、方法说明,以及尚未测量的部分,都在 [docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定价

| 方案 | 涵盖内容 | 价格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整面板,仅本地 | $0 |
| **Starter** | 上述之外的所有运行时、舰队视图、云同步 | 每节点每月 $9 |
| **Pro** | Starter + 控制与评估：审批、工具风险策略、评估（evals）、异常检测、成本优化器、OTel 导出、防篡改审计日志 | 每节点每月 $19 |

年付方案、企业版及当前价格详见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管的许可证密钥无需云端即可使用（`clawmetry license`）。免费与付费的具体划分见
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地会话文件和日志。**除非你运行 `clawmetry connect`,否则不会有任何会话数据离开你的设备**——不包括提示词、回复、工具参数、文件内容或日志行。当你确实连接了云端,快照会使用一把永不离开你机器的密钥进行端到端加密,并在你的浏览器中解密。如果某个节点没有密钥,上传会被跳过而不是以明文发送,任何服务器响应都无法关闭这一保护。

在你连接之前,默认会运行两项内容,均为默认开启但可选择关闭,且都不携带任何会话数据：一次匿名安装 ping,以及针对 PyPI 的版本检查。默认安装还会查询一次你的公网 IP,用于启动横幅的显示。每一个目标地址、它携带的信息以及如何关闭它,都列在
[docs/EGRESS.md](docs/EGRESS.md) 中；自托管、改指向或隔离网络的安装完全不会产生任何主动的对外调用。

解密发生在你的浏览器中,使用我们提供给你的代码。这曾经只是一句承诺,现在变成了你可以自行核实的事实。所有触碰你密钥的代码都在一个可读的文件里，[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),它随 wheel 包一起发布,原样提供,并用子资源完整性（Subresource Integrity）哈希做了锁定。要确认浏览器运行的是我们发布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

这无法证明的是：加载该文件的页面本身也是我们提供的,所以理论上我们可以提供另一个不同的页面。完整性哈希能保护你免受被攻陷的 CDN 侵害,但无法防御来自厂商本身的替换。你获得的保障是：任何替换行为都必须是刻意为之的、在页面源码中可见的,并且与 PyPI 上任何人都能获取到的构件不同。选择自托管或仅本地运行,则彻底消除了这种依赖。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或者使用一行命令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台机器上至少一种智能体运行时。Docker 安装说明见 [docs/DOCKER.md](docs/DOCKER.md)。

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取哪些内容,以及如何新增一种运行时 |
| [上下文爆量](docs/CONTEXT_BLOWOUT.md) | 按提供商划分的窗口大小、压缩 vs 溢出、各运行时的覆盖情况 |
| [开销](docs/OVERHEAD.md) | 监控本身的实测开销,以及复现该测试的框架 |
| [权限（Entitlements）](docs/ENTITLEMENTS.md) | 免费与付费对比、分级表、license CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前拦截、风险评分、手机审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将 trace 导出到任意目的地,从任意来源接入 OTLP |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自己搭建的智能体做成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 配置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理；从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名安装与打开桌面端时的 ping,以及如何关闭它们 |

## 截图

以下每一个数字都来自一台真实机器,只读获取,没有任何人为构造的数据。

**它会告诉你哪里出了问题,而不只是发生了什么。**
顶部两条异常横幅：支出达到日均的 7 倍,以及一次 4.2 倍的成本突增。下方是 667 个近期会话中的 324 个带有浪费信号,并按原因逐一列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它会展示每一个时间窗口里钱花到了哪里。**
今天 $252.47,本周 $513.15,本月 $1,312.92,各自附带背后的 token 数,以及其中有多少已被你的订阅覆盖。下方是约 $1,128/月被列为可优化的部分,以及缓存复用已经节省的 $17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它会画出一条消息是如何变成一个答案的。**
实时流程图：你、消息到达的渠道、网关、正在作答的模型,以及它调用过的每一个工具。节点会随着工作的流转而点亮。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**机器上的每一个智能体,都在一张表里。**
它运行的是什么、过去 24 小时和整个生命周期的成本、最后一次活跃时间、归属于谁,以及是否有订阅在覆盖账单。这里有 14 个智能体,3 个会话正在工作,13 个处于静默。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它会逐个工具展示一轮对话的时间和花费去向。**
一个真实会话的一轮：11.2 分钟内调用了 11 个工具,花费 $1.16。每次 Bash 调用和模型调用都在时间线上有自己的一条柱状图,因此一眼就能分辨出哪个命令跑了 4.1 分钟,哪个只用了 226 毫秒。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它评判的是工作质量,而不只是花费。**
本周的评级是 A：54 个任务顺利完成,2 个问题较多的任务花费了 $48.57,而活动量太少、无法判断的运行则被排除在评级之外,而不是被算作成功。每一个问题任务都链接到对应的追踪记录。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它会展示上下文窗口为什么一直在被填满。**
最近一轮用掉了 1M token 窗口中的 715K,峰值利用率 83.3%,4 次压缩全部是主动触发,而非因溢出被迫触发,以及此前每一轮的利用率详情。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**检测无需你做任何配置即可运行。**
内置检测器从安装起就已开启：智能体静默、遥测数据流中断、成本突增、token 突增、错误率上升、错误突增、预算阈值、威胁特征匹配、安全工具发现、安全态势变化。你自己的规则可以在此基础上按需附加。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**拦截高风险调用是可选开启的功能,且默认关闭出厂。**
递归删除、强制推送、sudo、密钥凭据、包安装以及外发调用,各自都有一条你可以开启的规则。在你开启之前,ClawMetry 只是观察,不会改变任何行为。一旦开启某条规则,匹配到的调用会在此处（或你的手机上）等待批准或拒绝。

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
