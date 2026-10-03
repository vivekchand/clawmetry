<!-- i18n-src:c99ac0512cae -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**一个智能体可能进行上百次工具调用却毫无进展。** ClawMetry
读取你的编码智能体已经在写入的会话文件，将时间线、
工具调用，以及运行时所暴露的 token 和成本数据，整合到一个
视图中——这样你就能分辨一次正在推进的长时间运行，和一次卡住不动的长时间运行。

支持**33 种 AI 智能体运行时**——Claude Code、OpenAI Codex、Hermes、OpenClaw 及其他 29 种。为你整个智能体舰队提供一个仪表盘。（[完整列表](SUPPORTED_RUNTIMES.txt)，由目录自动生成。）

> 🌐 **本文档语言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置：它会找到你机器上已有的
智能体运行时，以只读方式读取它们，不会改变它们的任何运行方式。

![ClawMetry 仪表盘：一台机器上所有 AI 智能体运行时，附带每个智能体的 24 小时及累计成本](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安装前须知

| | |
|---|---|
| **它做什么** | 读取你的智能体已经在写入的会话文件和日志。没有 SDK，不需要改代码，不在你的应用中插入任何埋点。 |
| **你能看到什么** | 会话时间线、逐个工具调用的回放、token 与成本明细，以及轨迹信号（循环、重复失败）——按运行时划分。 |
| **哪些是免费的** | `pip install clawmetry` 可以读取 **OpenClaw、NVIDIA NemoClaw、Goose 和 Qwen Code**，无需账号、无需密钥、也不产生任何网络调用。其余 28 种——Claude Code、Codex、Cursor 等等——由闭源的 `clawmetry-pro` 配套组件读取，该组件随 7 天试用或付费计划一同提供——确切的划分见 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何开始** | `pip install clawmetry && clawmetry`，然后打开 localhost:8900。这台机器上还没有任何智能体？`clawmetry --sample` 会用三条带标注的合成会话打开仪表盘。 |
| **会有什么离开你的机器** | 除非你运行 `clawmetry connect`，否则不会有任何会话数据离开。默认情况下确实会运行两件事，均为可选退出，且都不携带会话内容：一次匿名安装 ping 和一次 PyPI 版本检查。每个目的地都记录在 [docs/EGRESS.md](docs/EGRESS.md) 中，该文档是基于抓包重建的，而不是靠读注释得来的。 |

在你评判输出结果之前，有两点限制值得了解：不同运行时暴露的数据
差异很大（有些根本不发布任何成本信息——[矩阵表](docs/compatibility.md)
会告诉你每个运行时具体如何），并且能观察到一个动作并不等于
能够阻止它（[每个运行时哪些控制是真实有效的](docs/APPROVALS.md)）。


## 支持 33 种智能体运行时

**在开源应用中免费：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**付费计划：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每种运行时都用同一套仪表盘。同时运行多个运行时时，顶部的
切换器会将每个标签页重新聚焦到其中一个运行时上。

自己用 SDK 搭建了智能体而不是用现成运行时？拦截器（interceptor）
同样会追踪它的 LLM 调用。详见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**：每个智能体做了什么，逐轮呈现，可回放
- **成本与 token**：按运行时、模型、会话和天数划分，附带异常标记
- **Flow（流程图）**：消息在渠道、模型和工具之间流动的实时示意图
- **Brain（大脑）**：推理与工具调用事件流，实时呈现
- **上下文爆满**：按服务商定制的窗口大小、压缩（compaction）与被迫溢出的区分，以及按运行时划分的"我们看不到什么"的地图（[原理](docs/CONTEXT_BLOWOUT.md)）
- **记忆与技能**：每个运行时实际加载的文件与技能
- **健康状况与日志**：磁盘、内存、错误率、速率限制、实时日志流
- **告警**：预算上限、错误突增、智能体离线，可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **审批**：在风险工具调用*执行前*先行暂停，并可在手机上审批（[原理](docs/APPROVALS.md)）

## 上下文爆满，以及监控的成本

在你信任任何智能体对比工具之前，值得先回答这两个问题。

**它如何处理跨运行时的上下文窗口爆满？**

利用率百分比的可信度，取决于它所除以的分母是否诚实。ClawMetry
会根据[一张你可以阅读并提交 PR 的表格](clawmetry/context_windows.py)
按服务商确定窗口大小，覆盖 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不会用某一家
供应商的尺子去衡量全部 33 种运行时。这很重要：一次 300K 的 GPT-5
对话轮如果拿 Anthropic 的 200K 去衡量，会显示">100%，已爆满"，
而实际上它只是 GPT-5 的 400K 窗口的 75%。同一把尺子也会把一次
确实已溢出的 130K DeepSeek 对话轮，掩盖成看似舒适的 65%。

每个窗口数值都附带其来源：`model_table`、`explicit_marker`、
`observed_floor`，或者在我们不知道模型时诚实地标为 `default`。
一个建立在猜测之上的仪表盘，不应该和一个建立在查表之上的仪表盘
显示出同等的权威性。

ClawMetry 只能在部分运行时上看到压缩（compaction）事件。因此
`GET /api/context-coverage` 会按运行时报告，**一个 0 到底意味着
"干净跑完"还是"我们看不见"**。真正意味着"看不见"的 0 会明确说明这一点。
[详情](docs/CONTEXT_BLOWOUT.md)

**这套监控埋点本身的成本是多少？**

| 路径 | 为你的智能体增加的开销 | 是否默认开启？ |
|---|---|---|
| 会话文件 tailing（全部 33 种运行时） | **0**。独立进程，你的智能体中不含任何 ClawMetry 代码 | 开启 |
| HTTP 拦截器（`CLAWMETRY_INTERCEPT=1`） | 每次 LLM 调用 **+0.44 毫秒**，相当于一次 5 秒调用的 0.009% | 关闭 |
| 工具执行前钩子门（Pre-tool hook gate，热缓存） | 每次受控工具调用 **+44 毫秒**，在 36 毫秒解释器基线之上 | 关闭 |
| 强制执行代理（Enforcement proxy） | 每次 LLM 调用 **+9.7 毫秒** | 关闭 |

守护进程主机成本：摄取速度 **2,762 事件/秒**，磁盘占用
**每事件 710 字节**（每 10 万事件 67.7 MB），繁忙安装环境下持续占用
**约 12% 的单核算力**。最后这个数字超出了我们自己设定的
5-10% 预算，因此我们将其作为一个需要追查的 bug 公开发布，而不是
从页面上隐去。

在 Apple M2 Pro 上用 `benchmarks/overhead.py` 测得。该测试框架会在
独立进程中运行每种条件，交替测试顺序，并且**当多轮结果在符号上不一致时
拒绝给出数字**。你可以在自己的机器上花一分钟运行它：

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每条路径都经过测量，包括钩子门和强制执行代理，且该测试框架在
Linux、macOS 和 Windows 上的 CI 中都会运行。两个值得了解的结果：
代理在 Windows 上的开销大约是 Linux 上的七倍，并且守护进程目前
持续占用约 12% 的单核，超出了我们自己设定的 5-10% 预算。原始 JSON
数据、方法说明，以及尚未测量的部分，都在
[docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定价

| 计划 | 覆盖范围 | 价格 |
|---|---|---|
| **Free（免费版）** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code，完整仪表盘，仅本地 | $0 |
| **Starter（入门版）** | 以上其余全部运行时，舰队视图，云同步 | 每节点每月 $9 |
| **Pro（专业版）** | Starter 的全部功能 + 控制与评估：审批、工具风险策略、评估（evals）、异常检测、成本优化器、OTel 导出、防篡改审计日志 | 每节点每月 $19 |

年付计划、企业版及最新价格见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管的许可证
密钥无需云端即可使用（`clawmetry license`）。免费/付费的具体划分见
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地的会话文件和日志。**除非你运行 `clawmetry connect`，
否则不会有任何会话数据离开你的机器**——不会上传提示词、回复、
工具参数、文件内容或日志行。当你确实连接时，快照会使用一把
永不离开你机器的密钥进行端到端加密，并在你的浏览器中解密。如果
某个节点没有密钥，上传会被跳过，而不是以明文发送，没有任何
服务器响应能够关闭这一保护。

在你连接之前，默认会运行两件事，均为可选退出，且都不携带会话数据：
一次匿名安装 ping 和一次针对 PyPI 的版本检查。默认安装还会为启动横幅
查询一次你的公网 IP。每个目的地、它携带的内容以及如何关闭它，
都列在 [docs/EGRESS.md](docs/EGRESS.md) 中；自托管、改向及离线（air-gapped）
安装完全不会发起任何可选的出站调用。

解密发生在你的浏览器中，使用我们提供给你的代码。这一点过去只是
一句承诺；现在它是可以被验证的。每一行涉及你密钥的代码都在同一个
可读文件中，[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)，
它随 wheel 包一起分发，原样提供服务，并以子资源完整性（Subresource
Integrity）哈希值进行校验。要确认浏览器运行的就是我们发布的版本：

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

这无法证明的是：我们提供加载该文件的页面，所以我们理论上可以
提供一个不同的页面。完整性哈希能保护你免受 CDN 被攻陷的影响，
但无法防范供应商本身的恶意行为。你所获得的保证是：任何替换都
必须是刻意为之的、在页面源码中可见的，并且与任何人都可以从
PyPI 获取到的构建产物不同。自托管或仅本地运行可以完全消除这种依赖。

## 安装

```bash
pip install clawmetry     # 然后运行：clawmetry
```

或者使用一行命令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+，以及同一台机器上
至少一个智能体运行时。Docker 使用说明见 [docs/DOCKER.md](docs/DOCKER.md)。

或者让智能体替你完成设置。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能可以教会 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode
安装 ClawMetry、报告机器上各智能体正在做什么以及花费如何、
按需停止某个会话，并将有风险的工具调用挂起等待审批：

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取什么，以及如何新增一个运行时 |
| [上下文爆满](docs/CONTEXT_BLOWOUT.md) | 按服务商划分的窗口大小、压缩与溢出的区别、按运行时划分的覆盖情况 |
| [开销](docs/OVERHEAD.md) | 埋点监控的实测成本，附带可复现的测试框架 |
| [权益（Entitlements）](docs/ENTITLEMENTS.md) | 免费与付费对比、分级矩阵、许可证 CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前门控、风险评分、手机审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任意位置，从任意来源摄取 OTLP |
| [接入你自己的智能体](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 全流程，附带可运行示例 |
| [SDK 追踪](docs/SDK_TRACKING.md) | 针对你自行构建的智能体的成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 设置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部运行原理；从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名安装与桌面端打开时的 ping，以及如何关闭它们 |

## 截图

以下每一个数字都来自一台真实机器，均为只读获取，没有任何预置数据。

**它会告诉你何时出了问题，而不仅仅是发生了什么。**
顶部两条异常横幅：花费达到日均的 7 倍，以及一次 4.2 倍的成本激增。
下方显示，最近 667 个会话中有 324 个携带浪费信号，并按原因逐一列出。

![概览：实时智能体工作中的花费异常与成本激增横幅](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它展示钱花在了哪里，覆盖每一个时间窗口。**
今天 $252.47，本周 $513.15，本月 $1,312.92，每项都附带背后的 token
数量，以及你的订阅已经覆盖了其中多少。下方显示，约 $1,128/月
被归类为可回收，以及缓存复用已经节省的 $17,256/月。

![成本：今日、本周与本月，附带效率评级与节省建议明细](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它描绘了一条消息如何变成一个答案。**
实时流程图：你本人、消息到达的渠道、网关、当前正在作答的模型，
以及它调用的每一个工具。节点会随着工作流经而被点亮。

![Flow：从你经由网关到模型及其工具的实时示意图](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**机器上的每一个智能体，汇总在一张表中。**
它运行什么、过去 24 小时及累计花费多少、最后一次活跃时间、
归属于谁，以及是否有订阅覆盖这笔账单。此处共 14 个智能体，
3 个会话正在工作，13 个处于静默状态。

![智能体：机器上每个运行时的成本、负责人、最后活跃时间及当前工作](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它逐个工具展示一轮对话的时间和花费去向。**
一次真实会话的一个对话轮：11 个工具，耗时 11.2 分钟，花费 $1.16。
每一次 Bash 调用和模型调用在时间线上都有自己的进度条，让耗时 4.1
分钟的命令和仅耗时 226 毫秒的命令一眼就能区分开。

![会话：时间线上的一个智能体对话轮，每个工具调用都有自己的耗时与该轮的成本](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它评估的是工作成果，而不仅仅是花费。**
本周评级为 A：54 个任务干净利落地完成，2 个较差的任务花费了 $48.57，
而活动量过少、无法评判的运行则被排除在评级之外，而不是被计入"成功"。
每个较差的运行都链接到其对应的 trace。

![质量：本周成绩单，附带较差的运行及其成本](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它展示上下文窗口为何不断被填满。**
最近一个对话轮使用了 1M token 窗口中的 715K，峰值利用率 83.3%，
4 次压缩全部是主动触发而非因溢出被迫触发，并附带其背后每个
对话轮的利用率。

![上下文使用情况：每轮的窗口利用率、压缩事件及回收的 token](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**检测无需你做任何配置即可运行。**
内置检测器自安装起即已开启：智能体陷入沉默、遥测数据流中断、
成本激增、token 突增、错误攀升、错误突增、预算阈值、威胁特征
匹配、安全工具发现、安全态势变化。你自己的规则是可选的附加项。

![告警：内置检测器加上可选的自定义规则](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**挂起风险调用是可选启用的，且默认关闭出厂。**
递归删除、强制推送、sudo、密钥泄露、包安装以及出站调用，
各自都有一条你可以开启的规则。在你开启之前，ClawMetry 只会观察，
不会改变任何东西。一旦开启某条规则，匹配到的调用会在此处
（或你的手机上）等待批准或拒绝。

![审批：针对风险工具调用的保护规则，在你启用之前全部关闭](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多按运行时划分的截图：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 荣誉

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
