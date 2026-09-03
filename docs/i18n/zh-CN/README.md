<!-- i18n-src:9767c8001c9c -->
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

**看见你的 Agent 在想什么。** 针对 **30 种 AI Agent 运行时**的实时可观测性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 以及另外 26 种。一个仪表盘,管理你整个 Agent 团队。

> 🌐 **多语言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置:它会找到你机器上已有的 Agent 运行时,以只读方式读取它们,不会改变它们的任何运行方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 支持 30 种 Agent 运行时

**开源应用中免费:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付费计划中包含:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每个运行时都使用同一个仪表盘。同时运行多个时,顶部的切换器会让每个标签页重新聚焦到其中一个运行时上。

自己用某个 SDK 搭建了 Agent?拦截器同样会追踪它的 LLM 调用。详见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**:每个 Agent 逐轮做了什么,支持回放
- **成本与 Token**:按运行时、模型、会话和天数统计,并带有异常标记
- **Flow**:消息在渠道、模型和工具之间流动的实时图
- **Brain**:推理与工具调用的事件流,实时呈现
- **上下文爆量(Context blowout)**:按提供商精确计算的窗口利用率、压缩(compaction)与被迫溢出的对比,以及每个运行时"我们看不到什么"的地图([原理](docs/CONTEXT_BLOWOUT.md))
- **记忆与技能(Memory & skills)**:每个运行时实际加载过的文件与技能
- **健康状况与日志**:磁盘、内存、错误率、速率限制、实时日志流
- **告警**:预算上限、错误激增、Agent 离线,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **审批**:在有风险的工具调用*执行前*暂停,并可在手机上审批([原理](docs/APPROVALS.md))

## 上下文爆量,以及观测本身的成本

在信任任何 Agent 对比工具之前,值得先弄清楚这两个问题。

**它如何处理跨运行时的上下文窗口爆量?**

利用率百分比的可信度,取决于它的分母是否诚实。ClawMetry 会根据[一张你可以查阅并提交 PR 的表格](clawmetry/context_windows.py)按提供商计算窗口大小,覆盖 Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不会用同一家厂商的尺子去衡量全部 26 种运行时。这一点很关键:一次 30 万 token 的 GPT-5 对话轮次,如果按 Anthropic 的 20 万上限来算,会读成">100%,已爆量",但实际上它只用了 GPT-5 40 万上限的 75%。同一把尺子也会把一个真正溢出的 13 万 token DeepSeek 轮次,粉饰成一个舒适的 65%。

每个窗口都附带其来源:`model_table`、`explicit_marker`、`observed_floor`,或者在我们不认识该模型时给出一个诚实的 `default`。基于猜测搭建的仪表盘,不应该和基于查表搭建的仪表盘一样理直气壮。

ClawMetry 只能在部分运行时上看到压缩(compaction)事件。因此 `GET /api/context-coverage` 会针对每个运行时报告,一个 **0 到底意味着"运行干净"还是"我们看不见"**。如果一个 `0` 实际上意味着看不见,它就会明说。[完整细节](docs/CONTEXT_BLOWOUT.md)

**这套观测本身的成本是多少?**

| 路径 | 加给你 Agent 的开销 | 是否默认开启? |
|---|---|---|
| 会话文件 tailing(全部 30 种运行时) | **0**。独立进程,你的 Agent 中不含任何 ClawMetry 代码 | 开 |
| HTTP 拦截器(`CLAWMETRY_INTERCEPT=1`) | 每次 LLM 调用 **+0.44 毫秒**,占一次 5 秒调用的 0.009% | 关 |
| 工具前置 Hook 门控(热缓存) | 每次受控工具调用 **+44 毫秒**,基于 36 毫秒的解释器基线 | 关 |
| 强制执行代理(Enforcement proxy) | 每次 LLM 调用 **+9.7 毫秒** | 关 |

守护进程宿主开销:摄取速度 **2,762 events/秒**,磁盘上每条事件 **710 字节**(每 10 万事件 67.7 MB),在繁忙安装环境下持续占用 **约 12% 的单核**。最后这个数字超出了我们自己设定的 5-10% 预算,因此我们把它作为一个待解决的 bug 公开发布,而不是隐藏起来。

在一台 Apple M2 Pro 上使用 `benchmarks/overhead.py` 测得。测试框架在独立进程中运行每种情形,交替其顺序,并且**在多轮结果的正负号不一致时拒绝给出数字**。你可以在自己的机器上花一分钟运行它:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每条路径都经过实测,包括 Hook 门控和强制执行代理,该测试框架在 CI 中于 Linux、macOS 和 Windows 上运行。有两个结果值得了解:该代理在 Windows 上的开销大约是 Linux 上的七倍,而守护进程目前持续占用约 12% 的单核,超出了我们自己设定的 5-10% 预算。原始 JSON、测试方法,以及尚未测量的部分,都在 [docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定价

| 计划 | 覆盖范围 | 价格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整仪表盘,仅限本地 | $0 |
| **Starter** | 上述之外的全部其他运行时、团队(fleet)视图、云端同步 | 每节点每月 $9 |
| **Pro** | Starter + 控制与评估:审批、工具风险策略、评估(evals)、异常检测、成本优化器、OTel 导出、防篡改审计日志 | 每节点每月 $19 |

年付计划、企业版及最新价格详见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管的许可证密钥无需云端即可使用(`clawmetry license`)。免费/付费的具体划分见 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地会话文件和日志。**除非你运行了 `clawmetry connect`，否则任何会话数据都不会离开你的设备**——不会有提示词、回复、工具参数、文件内容或日志行外泄。当你确实连接后,快照会使用一把永不离开你机器的密钥进行端到端加密,并在你的浏览器中解密。如果某个节点没有密钥,上传会被跳过,而不是明文发送,任何服务器响应都无法关闭这一保护。

在你连接之前,默认已经会运行两件事,都可选择退出(opt-out),且都不携带任何会话数据:一次匿名的安装 ping,以及一次针对 PyPI 的版本检查。默认安装还会为启动横幅查询一次你的公网 IP。每个目标地址、它携带的内容以及如何关闭,都列在 [docs/EGRESS.md](docs/EGRESS.md) 中;自托管、重新定向或与外网隔离(air-gapped)的安装不会产生任何非必需的对外调用。

解密发生在你的浏览器中,使用的是我们提供给你的代码。这以前只是一个承诺;现在你可以自己核实。所有涉及你密钥的代码都集中在一个可读的文件里,[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),它随 wheel 包一起发布,原样提供服务,并使用 Subresource Integrity 哈希进行锁定。要确认浏览器运行的确实是我们发布的版本:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

这无法证明的是:我们负责提供加载该文件的页面,因此理论上我们可以提供另一个不同的页面。完整性哈希能保护你免受 CDN 被攻破的影响,但无法防范厂商本身的作恶。你获得的保障是:任何替换都必须是刻意为之、在页面源码中可见,并且与任何人都能从 PyPI 获取的构件不同。选择自托管或纯本地模式,可以彻底消除这种依赖。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或使用一键脚本:`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台机器上至少一个 Agent 运行时。Docker 说明见 [docs/DOCKER.md](docs/DOCKER.md)。

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器读取什么,以及如何添加新的运行时 |
| [上下文爆量](docs/CONTEXT_BLOWOUT.md) | 按提供商划分的窗口大小、压缩与溢出对比、各运行时覆盖情况 |
| [开销(Overhead)](docs/OVERHEAD.md) | 观测本身的实测开销,以及复现所用的测试框架 |
| [权益(Entitlements)](docs/ENTITLEMENTS.md) | 免费与付费对比、层级矩阵、license CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前门控、风险评分、手机审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任何地方,从任何来源摄取 OTLP |
| [接入你自己的 Agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 全流程,附可运行示例 |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自己搭建的 Agent 做成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 配置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理;从源码运行 |
| [遥测(Telemetry)](docs/TELEMETRY.md) | 匿名的安装及桌面打开 ping,以及如何关闭它们 |

## 截图

以下每一个数字都来自一台真实机器,只读获取,没有任何预置数据。

**它会告诉你哪里出了问题,而不只是发生了什么。**
顶部两条异常横幅:支出达到日均的 7 倍,以及一次 4.2 倍的成本激增。下方是最近 667 个会话中的 324 个带有浪费信号,并按原因逐项列出。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它会展示钱花在了哪里,覆盖每个时间窗口。**
今天 $252.47,本周 $513.15,本月 $1,312.92,每一项都附带背后的 token 数,以及订阅已经覆盖了多少。下方是约每月 $1,128 的可回收支出明细,以及缓存复用已经节省的每月 $17,256。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它会画出一条消息如何变成一个答案。**
实时流程图:你、消息到达的渠道、网关、正在作答的模型,以及它调用的每一个工具。节点会随着工作流经它们而点亮。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**机器上的每一个 Agent,都在同一张表里。**
它运行什么、过去 24 小时和生命周期内的成本、最后一次活跃时间、归属者,以及是否有订阅覆盖账单。此处显示 14 个 Agent,3 个会话正在工作,13 个空闲。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它会逐个工具展示一轮对话的时间和花费去向。**
一次真实会话中的一轮对话:11 个工具、耗时 11.2 分钟、花费 $1.16。每次 Bash 调用和模型调用都有自己的时间线柱状条,让耗时 4.1 分钟的命令和只用了 226 毫秒的命令一眼就能区分开。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它评价的是工作质量,而不仅仅是花费。**
本周评级为 A:54 个任务干净完成,2 个粗糙的任务花费了 $48.57,而活动量太少、无法判断的运行则被排除在评级之外,而不是被算作成功。每一个粗糙的运行都链接到它的追踪记录。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它会展示上下文窗口为何不断填满。**
最近一轮对话用掉了 100 万 token 窗口中的 71.5 万,峰值利用率 83.3%,4 次压缩(compaction)全部是主动触发,而非因溢出被迫触发,以及背后每一轮的利用率详情。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**检测无需你做任何配置即可运行。**
内置检测器从安装那一刻起就已开启:Agent 沉默、遥测数据流中断、成本激增、token 突发、错误率上升、错误激增、预算阈值、命中威胁特征、安全工具发现、安全态势变化。你自己的规则是可选的附加项。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**拦截有风险的调用是可选启用的,并且默认关闭出厂。**
递归删除、强制推送(force push)、sudo、密钥泄露、包安装以及对外调用,每一项都有可以打开的规则。在你打开之前,ClawMetry 只观察,不改变任何东西。一旦打开,匹配的调用会在此处(或你的手机上)等待批准或拒绝。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多按运行时划分的截图见:[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
