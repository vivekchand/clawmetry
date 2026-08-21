<!-- i18n-src:6795052055e2 -->
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

**看見您的 agent 如何思考。** 為 **26 種 AI agent 執行環境**提供即時可觀測性：[OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex 及其他 22 種。一個儀表板統管您整個 agent 艦隊。

> 🌐 **以下語言版本：** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [更多 →](docs/i18n/)

一行指令。零設定。自動偵測所有內容。

```bash
pip install clawmetry && clawmetry
```

在 **http://localhost:8900** 開啟。零設定：它會找到您已經擁有的 agent 執行環境，以唯讀方式讀取它們，不會改變它們的運作方式。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 支援 26 種 agent 執行環境

**開源應用中免費：** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**付費方案：** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

每種執行環境都使用相同的儀表板。同時執行多個時,標頭切換器會將每個分頁重新對應到其中一個執行環境。

自行以 SDK 打造了自己的 agent？攔截器同樣會追蹤它的 LLM 呼叫。詳見 [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)。

## 您將獲得什麼

- **工作階段與逐字稿**：每個 agent 逐輪執行了什麼,並可重播
- **成本與 token**：按執行環境、模型、工作階段與日期統計,並附異常標記
- **Flow**：訊息在頻道、模型與工具間流動的即時圖表
- **Brain**：即時呈現的推理與工具呼叫事件串流
- **Memory 與 skills**：每個執行環境實際載入的檔案與 skills
- **健康狀態與日誌**：磁碟、記憶體、錯誤率、速率限制、即時日誌串流
- **警示**：預算上限、錯誤激增、agent 離線,可路由至 Slack、Discord、PagerDuty、Telegram、Email
- **審批**：在風險工具呼叫*執行前*先暫停,並可從手機核准 ([操作方式](docs/APPROVALS.md))

## 定價

| 方案 | 涵蓋內容 | 價格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose,完整儀表板,僅限本機 | $0 |
| **Starter** | 上述以外的所有執行環境、艦隊檢視、雲端同步 | 每節點每月 $9 |
| **Pro** | Starter + 治理功能：審批、工具風險政策、評估、異常偵測、成本優化器、OTel 匯出 | 每節點每月 $19 |

年繳方案、Enterprise 與最新價格請見
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**。自架授權金鑰
無需雲端即可運作 (`clawmetry license`)。免費/付費的確切劃分請見
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)。

## 您的資料留在您的機器上

ClawMetry 讀取本機的工作階段檔案與日誌。除非您執行
`clawmetry connect`，否則沒有任何資料會離開您的機器。即使執行了該指令,
快照也會以絕不離開您機器的金鑰進行端對端加密,並在您的瀏覽器中解密。

## 安裝

```bash
pip install clawmetry     # then: clawmetry
```

或使用一行指令：`curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

需要 macOS、Linux 或 Windows 上的 Python 3.8 以上版本,以及同一台機器上
至少一個 agent 執行環境。Docker 說明請見 [docs/DOCKER.md](docs/DOCKER.md)。

## 文件

| | |
|---|---|
| [執行環境相容性](docs/compatibility.md) | 每個轉接器讀取什麼,以及如何新增執行環境 |
| [權益 (Entitlements)](docs/ENTITLEMENTS.md) | 免費與付費差異、方案矩陣、授權 CLI |
| [審批與政策](docs/APPROVALS.md) | 執行前把關、風險評分、手機審批 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | 將追蹤資料匯出至任何地方,並從任何來源接收 OTLP |
| [SDK 追蹤](docs/SDK_TRACKING.md) | 為您自行打造的 agent 提供成本歸屬 |
| [聊天頻道](docs/CHANNELS.md) | Flow 中顯示的聊天轉接器 |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | 沙盒化的 NVIDIA NemoClaw 設定 |
| [Docker](docs/DOCKER.md) | 映像檔、compose、磁碟區掛載 |
| [架構](ARCHITECTURE.md) · [開發](docs/DEVELOPMENT.md) | 內部運作原理;從原始碼執行 |
| [遙測](docs/TELEMETRY.md) | 匿名的安裝與桌面開啟回報,以及如何關閉它們 |

## 截圖

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**：token、工作階段、健康狀態 | **Brain**：即時 agent 事件串流 |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **成本**：依模型與工作階段統計 | **Approvals**：把關風險工具呼叫 |

更多依執行環境分類的截圖：[docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

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
