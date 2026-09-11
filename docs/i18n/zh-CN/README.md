<!-- i18n-src:12b97259721e -->
> 简体中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**一个智能体可以调用上百次工具却毫无进展。** ClawMetry
读取你的编码智能体本来就会写入的会话文件,把时间线、
工具调用,以及运行时所能提供的任何 token 和成本数据汇总到一个
视图里——这样你就能分辨出哪个长时间运行的任务是在正常推进,哪个已经卡住了。

支持 **31 种 AI 智能体运行时**——Claude Code、OpenAI Codex、Hermes、OpenClaw 及其他 27 种。一个仪表盘管理你整个智能体舰队。([完整列表](SUPPORTED_RUNTIMES.txt),由目录自动生成。)

> 🌐 **多语言版本:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一条命令。零配置。自动检测一切。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 打开。零配置:它会找到你机器上已有的
智能体运行时,以只读方式读取它们,不会改变它们的任何运行方式。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 安装前须知

| | |
|---|---|
| **它做什么** | 读取你的智能体本来就会写入的会话文件和日志。无需 SDK、无需改代码、无需在你的应用里做埋点。 |
| **你能看到什么** | 会话时间线、逐个工具的回放、token 和成本明细,以及轨迹信号(循环、重复失败)——按运行时区分。 |
| **哪些是免费的** | `pip install clawmetry` 可读取 **OpenClaw、NVIDIA NemoClaw 和 Goose**,无需账号、无需密钥、无需任何网络调用。其余 27 个——Claude Code、Codex、Cursor 等——由闭源的 `clawmetry-pro` 配套组件读取,该组件随 7 天试用或付费计划一同提供——确切的划分见 [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。 |
| **如何开始** | `pip install clawmetry && clawmetry`,然后打开 localhost:8900。这台机器上还没有智能体?`clawmetry --sample` 会用三个带标注的合成会话打开界面。 |
| **哪些数据会离开你的机器** | 除非你运行 `clawmetry connect`,否则不会有任何会话数据外传。默认情况下确实会运行两个功能,均可选择关闭,且都不携带会话内容:一个匿名安装 ping 和一个 PyPI 版本检查。每一个目的地都记录在 [docs/EGRESS.md](docs/EGRESS.md) 中,该文档基于抓包重建,而非仅凭代码注释。 |

在评判输出结果之前,有两个限制值得了解:不同运行时暴露的数据差异很大
(有些完全不公开成本——[对照表](docs/compatibility.md)
列出了每个运行时具体情况),而且"能观察到某个动作"不等于"能阻止它"
([哪些控制手段是真实有效的,按运行时区分](docs/APPROVALS.md))。


## 支持 31 种智能体运行时

**开源应用中免费提供:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付费计划:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每个运行时都能看到同一套仪表盘。同时运行多个运行时,顶部的切换器会把每个标签页重新聚焦到其中一个上。

用 SDK 自己搭建了智能体?拦截器同样能追踪它的 LLM 调用。
详见 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能获得什么

- **会话与转录**:每个智能体每一步做了什么,逐轮呈现,支持回放
- **成本与 token**:按运行时、模型、会话和天数拆分,附带异常标记
- **流程图**:消息在渠道、模型和工具之间流动的实时图示
- **Brain**:实时呈现的推理和工具调用事件流
- **上下文爆量**:按提供商精确计算的窗口利用率,区分压缩(compaction)与强制溢出,并按运行时给出一张我们*看不到*内容的地图([原理](docs/CONTEXT_BLOWOUT.md))
- **记忆与技能**:每个运行时实际加载过的文件和技能
- **健康状况与日志**:磁盘、内存、错误率、速率限制、实时日志流
- **告警**:预算上限、错误突增、智能体离线,可路由到 Slack、Discord、PagerDuty、Telegram、Email
- **审批**:在风险工具调用*执行前*暂停,并可在手机上批准([原理](docs/APPROVALS.md))

## 上下文爆量,以及监控的代价

在信任任何智能体对比工具之前,有两个问题值得先弄清楚。

**它如何处理跨运行时的上下文窗口爆量问题?**

利用率百分比的可信程度,取决于它的分母是否诚实。ClawMetry
根据[一张你可以查看并提 PR 的表格](clawmetry/context_windows.py)
按提供商精确计算窗口大小,覆盖 Anthropic、OpenAI、Google、xAI、
DeepSeek、Kimi、Qwen、Mistral、Llama 和 GLM。它不会用某一家供应商的
标尺去衡量全部 31 种运行时。这一点很重要:一次 300K 的 GPT-5 对话回合
如果拿 Anthropic 的 200K 去比对,会显示为">100%,已爆量",但实际上
它只占 GPT-5 400K 窗口的 75%。同一把标尺也会把一个真正溢出的
130K DeepSeek 回合掩盖成一个看似轻松的 65%。

每个窗口都附带其来源说明:`model_table`、`explicit_marker`、
`observed_floor`,或者在我们不认识该模型时诚实地标注 `default`。
一个基于猜测构建的仪表盘,不该与基于查表构建的仪表盘拥有同等的可信度。

ClawMetry 只能在部分运行时上看到压缩(compaction)事件。因此
`GET /api/context-coverage` 会针对每个运行时报告,一个"0"究竟意味着
**"运行干净"还是"我们看不到"**。真正意味着"看不到"的 0 会如实说明。
[详见](docs/CONTEXT_BLOWOUT.md)

**这套埋点本身的开销是多少?**

| 路径 | 给你的智能体增加的开销 | 默认开启? |
|---|---|---|
| 会话文件追踪(全部 31 种运行时) | **0**。独立进程,你的智能体中不包含任何 ClawMetry 代码 | 开启 |
| HTTP 拦截器(`CLAWMETRY_INTERCEPT=1`) | 每次 LLM 调用 **+0.44 毫秒**,相当于一次 5 秒调用的 0.009% | 关闭 |
| 预工具钩子门(热缓存) | 每次受控工具调用 **+44 毫秒**,基础解释器耗时为 36 毫秒 | 关闭 |
| 强制执行代理 | 每次 LLM 调用 **+9.7 毫秒** | 关闭 |

守护进程的主机开销:摄入速率 **2,762 事件/秒**,磁盘占用
**每事件 710 字节**(每 10 万事件 67.7 MB),在繁忙安装环境下持续占用
**约 12% 的单核 CPU**。最后这个数字已经超出了我们自己设定的 5%-10%
预算,因此我们把它作为一个待解决的问题发布出来,而不是隐瞒不提。

在 Apple M2 Pro 上使用 `benchmarks/overhead.py` 测得。该测试工具会在
独立进程中分别运行每种条件,交替它们的顺序,并且**在多轮结果符号
不一致时拒绝给出数字**。你可以在自己的机器上花一分钟跑一遍:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

每条路径都经过测量,包括钩子门和强制执行代理,该测试工具在 CI 中
分别在 Linux、macOS 和 Windows 上运行。有两个结果值得了解:该代理在
Windows 上的开销大约是 Linux 上的七倍,守护进程目前持续占用约 12%
的单核 CPU,超出了我们自己设定的 5%-10% 预算。原始 JSON 数据、测量
方法,以及尚未测量的部分都在 [docs/OVERHEAD.md](docs/OVERHEAD.md) 中。

## 定价

| 计划 | 涵盖内容 | 价格 |
|---|---|---|
| **免费版** | OpenClaw + NVIDIA NemoClaw + Goose,完整仪表盘,仅限本地 | $0 |
| **入门版** | 以上所有其他运行时,舰队视图,云端同步 | 每节点每月 $9 |
| **Pro 版** | 入门版 + 控制与评估:审批、工具风险策略、评估、异常检测、成本优化器、OTel 导出、防篡改审计日志 | 每节点每月 $19 |

年付计划、企业版及最新价格详见
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自托管的许可
密钥无需云端即可使用(`clawmetry license`)。免费与付费的详细划分见
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的数据留在你自己的机器上

ClawMetry 读取本地的会话文件和日志。**除非你运行 `clawmetry connect`,
否则没有任何会话数据会离开你的机器**——不包含提示词、回复、工具参数、
文件内容或日志行。当你连接后,快照会使用一个永远不会离开你机器的密钥
进行端到端加密,并在你的浏览器中解密。如果某个节点没有密钥,上传会被
跳过,而不是以明文发送,任何服务器端响应都无法关闭这一保护。

在你连接之前,默认就会运行两个功能,均可选择关闭,且都不携带会话
数据:一个匿名安装 ping 和一个针对 PyPI 的版本检查。默认安装还会为
启动横幅查询一次你的公网 IP。每个目的地、它携带什么内容以及如何关闭,
都列在 [docs/EGRESS.md](docs/EGRESS.md) 中;自托管、重定向或air-gapped(隔离网络)
的安装完全不会发出任何可选的对外调用。

解密发生在你的浏览器中,使用的是我们提供给你的代码。这原本只是一个
承诺;现在则是一件你可以自行核实的事情。所有涉及你密钥的代码都集中
在一个可读文件里,[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
它随 wheel 包一起发布,原样提供,并附带子资源完整性(Subresource
Integrity)哈希值加以固定。要确认浏览器运行的正是我们发布的版本:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

这个方法无法证明的是:加载这个文件的页面也是我们提供的,所以理论上
我们也可以提供一个不同的页面。完整性哈希保护你免受 CDN 被攻破的威胁,
而不是防范供应商本身。你所获得的保障是,任何替换行为都必须是刻意的、
在页面源代码中可见的,并且与任何人都能从 PyPI 获取的构件不同。选择
自托管或仅在本地运行则能完全消除这种依赖。

## 安装

```bash
pip install clawmetry     # 然后运行: clawmetry
```

或使用一键安装命令: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台机器上至少
一个智能体运行时。Docker 安装说明见 [docs/DOCKER.md](docs/DOCKER.md)。

或者让智能体帮你完成安装。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
技能可以教会 Claude Code、Codex、Cursor、Gemini CLI、Copilot 或 OpenCode
安装 ClawMetry、汇报机器上智能体正在做什么以及花费情况、按请求
停止某个会话,并为有风险的工具调用暂停等待批准:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## 文档

| | |
|---|---|
| [运行时兼容性](docs/compatibility.md) | 每个适配器能读取什么,以及如何添加一个新的运行时 |
| [上下文爆量](docs/CONTEXT_BLOWOUT.md) | 按提供商划分的窗口、压缩与溢出的区别、按运行时的覆盖情况 |
| [开销](docs/OVERHEAD.md) | 埋点的实际开销测量结果,以及可复现的测试工具 |
| [权益(Entitlements)](docs/ENTITLEMENTS.md) | 免费与付费对比、层级矩阵、许可证 CLI |
| [审批与策略](docs/APPROVALS.md) | 执行前拦截、风险评分、手机审批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 将追踪数据导出到任意位置,从任意来源摄入 OTLP |
| [接入你自己的智能体](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChain 全流程示例,附可运行代码 |
| [SDK 追踪](docs/SDK_TRACKING.md) | 为你自己搭建的智能体做成本归因 |
| [聊天渠道](docs/CHANNELS.md) | Flow 中展示的聊天适配器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 配置 |
| [Docker](docs/DOCKER.md) | 镜像、compose、卷挂载 |
| [架构](ARCHITECTURE.md) · [开发](docs/DEVELOPMENT.md) | 内部工作原理;从源码运行 |
| [遥测](docs/TELEMETRY.md) | 匿名安装及桌面端打开 ping,以及如何关闭它们 |

## 截图

以下每一个数字都来自一台真实的机器,只读获取,没有任何预置数据。

**它会告诉你哪里出了问题,而不只是发生了什么。**
顶部有两条异常横幅:支出达到日均值的 7 倍,以及一次 4.2 倍的成本
突增。下方是最近 667 个会话中有 324 个带有浪费信号,并按原因分类。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**它会告诉你钱花在了哪里,涵盖每一个时间窗口。**
今日 $252.47,本周 $513.15,本月 $1,312.92,每个数字都附带背后的
token 用量,以及你的订阅已经覆盖了多少。下方列出了约 $1,128/月的
可挽回支出,以及缓存复用已经节省的约 $17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**它会描绘一条消息是如何变成一个答案的。**
实时流程图:你、消息到达的渠道、网关、当前正在回答的模型,以及
它调用过的每一个工具。节点会随着工作在其间流动而亮起。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**机器上的每一个智能体,汇总在一张表里。**
它在运行什么、过去 24 小时和整个生命周期的花费、最后一次活跃时间、
归属者,以及是否有订阅覆盖账单。这里有 14 个智能体,3 个会话正在
工作,13 个处于静默状态。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**它会展示一轮对话的时间和金钱花在了哪里,精确到每个工具。**
一次真实会话中的一轮对话:11 个工具,耗时 11.2 分钟,花费 $1.16。
每一次 Bash 调用和模型调用都在时间线上拥有自己的条形,因此耗时 4.1
分钟的那次命令和耗时 226 毫秒的那次一眼就能分辨出来。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**它评估的是工作成果,而不只是花费。**
本周评级为 A:54 个任务顺利完成,2 个不太理想的任务花费了 $48.57,
而那些活动量太少、不足以评估的运行会被排除在评级之外,而不是被
计入成功案例。每个不理想的运行都链接到其追踪记录。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**它会展示上下文窗口为何不断被填满。**
最近一轮对话用掉了 1M token 窗口中的 715K,峰值利用率达 83.3%,
发生了 4 次压缩(compaction),且全部是主动触发而非因溢出触发,
背后每一轮对话的利用率都有据可查。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**检测功能无需任何配置即可运行。**
内置检测器从安装起就已开启:智能体静默、遥测数据流中断、成本突增、
token 突增、错误率上升、错误突增、预算阈值、威胁特征匹配、安全工具
发现、安全态势变化。你自己的规则是可选的附加项。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**拦截风险调用是可选开启的功能,且默认关闭出厂。**
递归删除、强制推送、sudo、密钥泄露、包安装以及对外调用,每一项都有
一个你可以启用的规则。在你启用之前,ClawMetry 只观察,不做任何改变。
一旦启用某项规则,匹配的调用就会在这里(或你的手机上)等待批准或拒绝。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

更多按运行时划分的截图见:[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
