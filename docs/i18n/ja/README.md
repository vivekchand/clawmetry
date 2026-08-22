<!-- i18n-src:6795052055e2 -->
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

**あなたのエージェントの思考を見る。** **26種類のAIエージェントランタイム**に対応したリアルタイム可観測性: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex ほか22種類。エージェントフリート全体を一つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

コマンド一つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定不要で、既にお使いのエージェントランタイムを見つけ、読み取り専用でアクセスし、動作には一切手を加えません。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26種類のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで対応:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

どのランタイムでも同じダッシュボードが使えます。複数を同時に実行しても、ヘッダーのスイッチャーで各タブの対象を切り替えられます。

SDKで自作したエージェントをお使いですか? インターセプターがそのLLM呼び出しも追跡します。詳しくは [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) をご覧ください。

## 得られるもの

- **セッションとトランスクリプト**: 各エージェントが何をしたか、ターンごとにリプレイ付きで確認
- **コストとトークン**: ランタイム、モデル、セッション、日ごとに、異常検知フラグ付きで
- **フロー**: チャネル、モデル、ツール間を流れるメッセージのライブ図
- **ブレイン**: 推論とツール呼び出しのイベントストリームをリアルタイムで
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインを、Slack、Discord、PagerDuty、Telegram、Emailに通知
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認 ([詳細](docs/APPROVALS.md))

## 料金

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外の全ランタイム、フリートビュー、クラウド同期 | ノードあたり月額$9 |
| **Pro** | Starter + ガバナンス: 承認、ツールリスクポリシー、評価、異常検知、コスト最適化、OTelエクスポート | ノードあたり月額$19 |

年間プラン、Enterprise、最新の料金は
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** をご覧ください。セルフホスト型のライセンス
キーはクラウドなしでも利用できます (`clawmetry license`)。無料/有料の詳細な区分は
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) に記載されています。

## データはあなたのマシンに留まります

ClawMetryはローカルのセッションファイルとログを読み取ります。`clawmetry connect` を実行しない限り、
何もあなたのマシンから外に出ません。実行した場合でも、スナップショットは
あなたのマシンから出ることのない鍵でエンドツーエンド暗号化され、ブラウザ内で復号されます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、Windows上のPython 3.8以上と、同じマシン上で動作する
エージェントランタイムが少なくとも1つ必要です。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが何を読み取るか、ランタイムの追加方法 |
| [Entitlements](docs/ENTITLEMENTS.md) | 無料 vs 有料、ティアマトリクス、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォン承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | トレースをどこにでもエクスポート、どこからでもOTLPを取り込み |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自作エージェントのコスト帰属 |
| [チャットチャネル](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動時のping、無効化する方法 |

## スクリーンショット

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: トークン、セッション、ヘルス | **Brain**: ライブエージェントイベントストリーム |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: モデルとセッション別 | **Approvals**: リスクのあるツール呼び出しをゲート |

ランタイムごとの詳細: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · [@vivekchand](https://github.com/vivekchand) が開発 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
