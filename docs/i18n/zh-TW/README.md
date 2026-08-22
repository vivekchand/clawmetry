<!-- i18n-src:c111f32e69a5 -->
> 繁體中文 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**看見你的 agent 如何思考。** 針對 **26 種 AI agent runtime** 的即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex，以及另外 22 種。一個儀表板,涵蓋你整個 agent 艦隊。

> 🌐 **以其他語言閱讀：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令,零設定,自動偵測一切。

```bash
pip install clawmetry && clawmetry
```

會在 **http://localhost:8900** 開啟。零設定：它會找到你已經安裝的 agent runtime,以唯讀方式讀取它們,不會改變它們的運作方式。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 26 種 agent runtime

**開源應用程式中免費提供：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

每種 runtime 都使用相同的儀表板。同時執行多個 runtime 時,頂部的切換器會將每個分頁重新聚焦到其中之一。

用 SDK 自行打造了 agent?攔截器 (interceptor) 一樣能追蹤它的 LLM 呼叫。詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 你能獲得什麼

- **工作階段與逐字稿**：每個 agent 逐輪做了什麼,並可重播
- **成本與 token**：依 runtime、模型、工作階段與日期統計,並標示異常
- **Flow**：訊息在頻道、模型與工具之間流動的即時圖表
- **Brain**：推理與工具呼叫的事件串流,即時呈現
- **記憶與技能**：每個 runtime 實際載入的檔案與技能
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤高峰、agent 離線,可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **審核 (Approvals)**：在有風險的工具呼叫執行*之前*暫停,並可從你的手機批准（[說明](docs/APPROVALS.md)）

## 定價

| 方案 | 涵蓋內容 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整儀表板,僅限本機 | $0 |
| **Starter** | 上述以外的所有 runtime、艦隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 治理功能：審核、工具風險政策、評估、異常偵測、成本最佳化工具、OTel 匯出 | 每節點每月 $19 |

年繳方案、企業版與目前的價格請見
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰
不需雲端即可運作（`clawmetry license`）。免費/付費的確切劃分請見
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 你的資料留在你的機器上

ClawMetry 讀取本機的工作階段檔案與日誌。除非你執行 `clawmetry connect`,
否則沒有任何資料離開你的機器。即使執行了該指令,快照也會以端對端加密,
使用一把永不離開你機器的金鑰,並在你的瀏覽器中解密。

## 安裝

```bash
pip install clawmetry     # then: clawmetry
```

或使用一行指令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8+,以及同一台機器上至少一種
agent runtime。Docker 說明請見：[docs/DOCKER.md](docs/DOCKER.md)。

## 文件

| | |
|---|---|
| [Runtime 相容性](docs/compatibility.md) | 每個轉接器讀取什麼,以及如何新增 runtime |
| [授權方案 (Entitlements)](docs/ENTITLEMENTS.md) | 免費 vs 付費、方案矩陣、授權 CLI |
| [審核與政策](docs/APPROVALS.md) | 執行前把關、風險評分、手機審核 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤匯出至任何地方,從任何來源接收 OTLP |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為你自行打造的 agent 進行成本歸因 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙箱化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、磁碟區掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理;從原始碼執行 |
| [遙測](docs/TELEMETRY.md) | 匿名安裝與開啟桌面應用的回傳訊號,以及如何關閉 |

## 截圖

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**：token、工作階段、健康狀態 | **Brain**：即時 agent 事件串流 |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **成本**：依模型與工作階段 | **審核**：把關有風險的工具呼叫 |

更多依 runtime 分類的截圖：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## Star 歷史

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## 授權條款

MIT · 由 [@vivekchand](https://github.com/vivekchand) 打造 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
