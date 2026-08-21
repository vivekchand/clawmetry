<!-- i18n-src:dc34072b2955 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を可視化。** **23種類のAIエージェントランタイム**に対応したリアルタイム観測ダッシュボード: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、他19種。エージェントフリート全体を1つのダッシュボードで。

> 🌐 **他の言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [さらに見る →](docs/i18n/)

1つのコマンド。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で起動します。設定は不要です。すでにお使いのエージェントランタイムを自動的に見つけ出し、読み取り専用でアクセスし、動作には一切手を加えません。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23種類のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**有料プラン:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

どのランタイムでも同じダッシュボードが使えます。複数を同時に実行すれば、ヘッダーのスイッチャーで各タブの対象を切り替えられます。

SDKを使って独自のエージェントを構築していますか?インターセプターがそのLLM呼び出しも追跡します。詳しくは[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)をご覧ください。

## できること

- **セッションとトランスクリプト**: 各エージェントが何をしたかをターンごとに、リプレイ付きで確認
- **コストとトークン**: ランタイム、モデル、セッション、日単位で集計し、異常検知フラグ付き
- **フロー**: チャンネル、モデル、ツールを行き交うメッセージのリアルタイム図解
- **ブレイン**: 発生した瞬間の推論とツール呼び出しのイベントストリーム
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインを検知し、Slack、Discord、PagerDuty、Telegram、Emailへ通知
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認([詳細](docs/APPROVALS.md))

## 料金

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **無料** | OpenClaw + NVIDIA NemoClaw、フルダッシュボード、ローカルのみ | $0 |
| **スターター** | 上記以外の全ランタイム、フリートビュー、クラウド同期 | ノードあたり月額$9 |
| **Pro** | スターター + ガバナンス機能: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート | ノードあたり月額$19 |

年間プラン、Enterprise、最新の料金は
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** をご覧ください。セルフホストのライセンスキー
(`clawmetry license`)はクラウドなしでも動作します。無料/有料の詳細な区分は
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)に記載されています。

## データはお使いのマシンに留まります

ClawMetryはローカルのセッションファイルとログを読み取ります。`clawmetry connect`
を実行しない限り、データが外部に送信されることはありません。実行した場合でも、
スナップショットはお使いのマシンから外に出ない鍵でエンドツーエンド暗号化され、
ブラウザ側で復号されます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、Windowsで動作するPython 3.8以上、および同じマシン上に少なくとも1つの
エージェントランタイムが必要です。Dockerでの手順は[docs/DOCKER.md](docs/DOCKER.md)をご覧ください。

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが読み取る内容と、ランタイムの追加方法 |
| [エンタイトルメント](docs/ENTITLEMENTS.md) | 無料版と有料版の違い、ティア一覧、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォン承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | どこへでもトレースをエクスポートし、どこからでもOTLPを取り込む |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自作エージェントのコスト帰属 |
| [チャットチャンネル](docs/CHANNELS.md) | フローに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行方法 |
| [テレメトリー](docs/TELEMETRY.md) | 匿名のインストール/デスクトップ起動時のping、およびその無効化方法 |

## スクリーンショット

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **概要**: トークン、セッション、ヘルス | **ブレイン**: ライブエージェントイベントストリーム |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **コスト**: モデル別・セッション別 | **承認**: リスクのあるツール呼び出しをゲート |

ランタイムごとの詳細: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## スター履歴

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · Built by [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
