<!-- i18n-src:c111f32e69a5 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を見よう。** **26種類のAIエージェントランタイム**向けのリアルタイム可観測性: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codexほか22種類。エージェント群全体を1つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [その他 →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定は不要です。すでにお使いのエージェントランタイムを自動的に見つけ、読み取り専用でアクセスし、動作には一切変更を加えません。

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 26種類のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで利用可能:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数のランタイムを同時に動かしても、ヘッダーのスイッチャーで各タブの表示対象を切り替えられます。

SDKで独自にエージェントを構築した場合も、インターセプターがそのLLM呼び出しを追跡します。詳しくは[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)をご覧ください。

## できること

- **セッションとトランスクリプト**: 各エージェントが行ったことをターンごとに、リプレイ付きで確認
- **コストとトークン**: ランタイム、モデル、セッション、日単位で、異常検知フラグ付き
- **フロー**: チャネル・モデル・ツール間を流れるメッセージのライブ図
- **ブレイン**: 発生と同時に流れる推論とツール呼び出しのイベントストリーム
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインをSlack、Discord、PagerDuty、Telegram、Emailへ通知
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認 ([詳細](docs/APPROVALS.md))

## 料金プラン

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外の全ランタイム、フリート表示、クラウド同期 | ノードあたり月額$9 |
| **Pro** | Starter + ガバナンス機能: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート | ノードあたり月額$19 |

年間プラン、Enterpriseおよび最新の価格は
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** に掲載しています。セルフホストのライセンス
キーはクラウドなしでも動作します（`clawmetry license`）。無料/有料の詳細な区分は
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)をご覧ください。

## データはあなたのマシンに留まります

ClawMetryはローカルのセッションファイルとログを読み取ります。`clawmetry connect`を
実行しない限り、データが外部に出ることはありません。実行した場合でも、
スナップショットはあなたのマシンから外に出ることのない鍵でエンドツーエンド暗号化され、
ブラウザ内で復号されます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

または、ワンライナーで: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、WindowsでPython 3.8以上が必要で、同じマシン上に少なくとも1つの
エージェントランタイムが必要です。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが何を読み取るか、ランタイムの追加方法 |
| [権利設定 (Entitlements)](docs/ENTITLEMENTS.md) | 無料 vs 有料、ティアマトリクス、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォン承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | トレースをどこへでもエクスポート、あらゆる場所からOTLPを取り込み |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自作エージェントのコスト帰属 |
| [チャットチャネル](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行方法 |
| [テレメトリー](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動時のping、そしてその無効化方法 |

## スクリーンショット

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: トークン、セッション、ヘルス | **エージェント** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: モデルおよびセッション別 | **Approvals**: リスクのあるツール呼び出しをゲート |

ランタイム別のさらに多くの画像: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## スター履歴

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · [@vivekchand](https://github.com/vivekchand) 作 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
