<!-- i18n-src:48548997be76 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を可視化。** **12種類のAIエージェントランタイム**にリアルタイムオブザーバビリティを提供します: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codexほか8種類。エージェントフリート全体を一つのダッシュボードで管理できます。

> 🌐 **他の言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

コマンド一つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** が開けば完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12種類のエージェントランタイムに対応

ClawMetry はもともとOpenClaw向けのオブザーバビリティツールとして始まりましたが、現在はマシン上の各ランタイムを自動検出し、**エージェントフリート全体**を一つのダッシュボードで計測できます。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw と NemoClaw はオープンソース版で無料利用できます。その他のランタイムは ClawMetry Cloud またはセルフホスト型 Pro ライセンスで有効になります。ヘッダーからランタイムを切り替えると、コスト・トークン・ツール・トレースなどすべてのタブがそのランタイム向けに絞り込まれます。

## 主な機能

- **Flow** — チャンネル、ブレイン、ツールをメッセージが流れる様子をライブアニメーションで表示
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日別・週別・月別のトークンとコストのトラッキング
- **Sessions** — モデル・トークン・最終アクティビティを含むアクティブエージェントセッション一覧
- **Crons** — ステータス・次回実行時刻・実行時間を含むスケジュールジョブ
- **Logs** — カラーコードによるリアルタイムログストリーミング
- **Memory** — SOUL.md・MEMORY.md・AGENTS.md・日次メモの閲覧
- **Transcripts** — チャットバブルUIでセッション履歴を閲覧
- **Alerts** — 予算上限・エラー率トリガー・エージェントオフライン検知、Slack・Discord・PagerDuty・Telegram・メールへの通知
- **Approvals** — 破壊的な削除・強制プッシュ・DB変更・sudo・パッケージインストール・ネットワーク呼び出しをワンクリック承認で保護

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッションサマリー
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムツールコールフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデルとセッション別のコスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — セキュリティポスチャと監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限・エラー率トリガー・Slack / Discord / PagerDuty / メールへのWebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツール呼び出しを手動承認で保護。ポリシーによる保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## インストール

**ワンライナー（推奨）:**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**ソースから:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 フロントエンド開発

v2 React アプリは `frontend/` に配置されており、v2 を有効にして Flask サーバーを起動すると `/v2` で提供されます。

開発中は2つのターミナルを使用します。

```bash
# ターミナル1: Flask API/サーバー（:8900）
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ターミナル2: Vite 開発サーバー（:5173）
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` を開いてください。Vite は `/api` リクエストを `http://localhost:8900` にプロキシするため、React アプリは追加の CORS 設定なしにローカルの Flask サーバーと通信できます。

Python パッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番バンドルは `clawmetry/static/v2/dist/` に出力されます。

## ランタイム / エージェント互換性

ClawMetry は OpenClaw だけでなく、多くの AI エージェントランタイムを監視します。OpenClaw 以外の各ランタイムには専用のリーダーアダプターが付属しており、そのランタイム固有のセッション形式を ClawMetry の統一されたデータ形式に変換します。デーモンはそれらを同じ DuckDB ストアとクラウドスナップショットにランタイムタグ付きで取り込み、セッションリプレイタブには複数のランタイムが存在する場合に**ランタイム切り替え**が表示されます。完全な互換性マトリクスとランタイム追加ガイドは [`docs/compatibility.md`](docs/compatibility.md) を、OpenClaw ファミリーの概要は [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) をご覧ください。

| ランタイム / エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | ベータアダプター | セッションごとの SQLite (`data/v2-sessions`)。トランスクリプトとメッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出し+思考、トークン使用量。 |
| **Codex** | ベータアダプター | ロールアウト JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザートランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの `.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |

「ベータアダプター」とは、ClawMetry がそのランタイムの実際のディスク上フォーマット向けのリーダーを提供していることを意味し、それぞれ実際のマシン上の実際のインストールに対してビルド・検証されています（`tests/fixtures/runtimes/<rt>/` 参照）。アダプターは読み取り専用です。各アダプターはランタイムが実際にディスクに保存する内容について正直です（例: PicoClaw/NanoClaw/Cursor はトークンコストをディスクに書き込まない）。複数のランタイムが1つのノードで動作している場合、ランタイム切り替えによってセッションビューを1つに絞り込み、詳細な分析が可能です。

## 任意の SDK エージェントを追跡する — アウトループコスト帰属

上記のランタイムはすべてセッションをディスクに書き込みます。OpenAI Agents SDK・LangChain・Vercel AI SDK・LlamaIndex・E2B・あるいは単純な `httpx` ループで構築した**本番エージェント**はディスクに書き込みません。ClawMetry のゼロコンフィグインターセプターは、`httpx`/`requests` をモンキーパッチすることで、そのエージェントの LLM 呼び出し（コスト、トークン、レイテンシ、エラー）を取得します。

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`（または `CLAWMETRY_SOURCE=support-agent` 環境変数）は各呼び出しに**名前付きソース**タグを付与するため、実行している各プロダクトが、ダッシュボードの Overview にある **🔌 Out-loop sources** カードにコスト帰属可能な独立した行として表示されます。エージェントごとの呼び出し数・プロバイダー・レイテンシ・エラー率が確認できます。ソースを設定しない場合でも呼び出しは記録されますが、カードは非表示のままです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターが使用するのと同じデータレイヤー（DuckDB → クラウドスナップショット）を使用するため、アウトループソースも他のすべてと同様にエンドツーエンド暗号化でクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダー中立、トレースをどこにでも送信

ClawMetry は **GenAI セマンティック規約**を使用した **OpenTelemetry** を双方向でサポートしているため、エージェントトレースが特定のツールに縛られることはありません。

すべてのセッション（LLM 呼び出し、ツール、サブエージェント、トークン、コスト）を OTLP/HTTP GenAI スパンとして任意のコレクター（Datadog、Grafana、Honeycomb、または独自の OTel Collector）に**エクスポート**します。

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔はオプションの環境変数で設定できます。

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**インジェスト** — 組み込みの OTLP レシーバーは `/v1/traces` および `/v1/metrics` で他のあらゆるソースからのトレースとメトリクスを受け付けます（プロトバッファインジェストには `pip install clawmetry[otel]` が必要）。

ゼロコンフィグでローカルファーストの ClawMetry ダッシュボード**と**チームがすでに使用しているバックエンドの両方にデータを送ることができます。ロックインなし、追加エージェントのインストール不要。

## 設定

ほとんどのユーザーは設定不要です。ClawMetry はワークスペース、ログ、セッション、cron を自動検出します。

カスタマイズが必要な場合:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

すべてのオプション: `clawmetry --help`

## 対応チャンネル

ClawMetry は設定済みのすべての OpenClaw チャンネルのライブアクティビティを表示します。Flow ダイアグラムには `openclaw.json` で実際に設定されているチャンネルのみが表示され、未設定のものは自動的に非表示になります。

Flow 内の任意のチャンネルノードをクリックすると、送受信メッセージ数を含むライブチャットバブルビューが表示されます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ 完全対応 | ✅ | メッセージ、統計、10秒更新 |
| 💬 **iMessage** | ✅ 完全対応 | ✅ | `~/Library/Messages/chat.db` を直接読み取り |
| 💚 **WhatsApp** | ✅ 完全対応 | ✅ | WhatsApp Web (Baileys) 経由 |
| 🔵 **Signal** | ✅ 完全対応 | ✅ | signal-cli 経由 |
| 🟣 **Discord** | ✅ 完全対応 | ✅ | ギルドとチャンネルの自動検出 |
| 🟪 **Slack** | ✅ 完全対応 | ✅ | ワークスペースとチャンネルの自動検出 |
| 🌐 **Webchat** | ✅ 完全対応 | ✅ | 組み込みウェブUIセッション |
| 📡 **IRC** | ✅ 完全対応 | ✅ | ターミナル風バブルUI |
| 🍏 **BlueBubbles** | ✅ 完全対応 | ✅ | BlueBubbles REST API 経由の iMessage |
| 🔵 **Google Chat** | ✅ 完全対応 | ✅ | Chat API Webhook 経由 |
| 🟣 **MS Teams** | ✅ 完全対応 | ✅ | Teams ボットプラグイン経由 |
| 🔷 **Mattermost** | ✅ 完全対応 | ✅ | セルフホスト型チームチャット |
| 🟩 **Matrix** | ✅ 完全対応 | ✅ | 分散型、E2EE サポート |
| 🟢 **LINE** | ✅ 完全対応 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ 完全対応 | ✅ | 分散型 NIP-04 DM |
| 🟣 **Twitch** | ✅ 完全対応 | ✅ | IRC 接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ 完全対応 | ✅ | WebSocket イベントサブスクリプション |
| 🔵 **Zalo** | ✅ 完全対応 | ✅ | Zalo Bot API |

> **自動検出:** ClawMetry は `~/.openclaw/openclaw.json` を読み取り、実際に設定されているチャンネルのみをレンダリングします。手動設定は不要です。

## Docker デプロイメント

ClawMetry をコンテナで実行したい場合も問題ありません！ 🐳

**Docker クイックスタート:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose の例:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **注意:** Docker で実行する場合は、ClawMetry がセットアップを自動検出できるよう、エージェントのデータディレクトリとログディレクトリ（例: `~/.openclaw`、`~/.claude`、`~/.codex`）をマウントしてください。

## 動作要件

- Python 3.8 以上
- Flask（pip 経由で自動インストール）
- 同一マシン上の AI エージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、または PicoClaw（Docker の場合はマウントされたボリューム）
- Linux または macOS

## NemoClaw / OpenShell サポート

ClawMetry は [NemoClaw](https://github.com/NVIDIA/NemoClaw) を自動検出します。NemoClaw は NVIDIA のエンタープライズセキュリティラッパーで、サンドボックス化された OpenShell コンテナ内でエージェントを実行します。

ほとんどの場合、追加設定は不要です。sync デーモンはセッションファイルがホスト上の `~/.openclaw/` にあっても、OpenShell コンテナ内にあっても自動的に検出します。

### 仕組み

ClawMetry は2つの方法で NemoClaw を検出します。

1. **バイナリ検出** — `nemoclaw` CLI を確認し、`nemoclaw status` を実行してサンドボックス情報を取得
2. **コンテナ検出** — `openshell`、`nemoclaw`、または `ghcr.io/nvidia/` イメージの実行中の Docker コンテナをスキャンし、ボリュームマウントまたは `docker cp` でセッションを読み取る

NemoClaw コンテナから同期されたセッションファイルはクラウドダッシュボードで `runtime=nemoclaw` と `container_id` メタデータのタグが付けられ、標準的な OpenClaw セッションと一目で区別できます。

### 推奨セットアップ: ホスト上での sync デーモン実行

最良のエクスペリエンスのために、sync デーモンはサンドボックス内ではなく**ホストマシン上**で実行することをお勧めします。これにより NemoClaw のネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync デーモンは実行中の OpenShell コンテナ内のセッションを自動的に検出します。

### オプション: 明示的なサンドボックス名の指定

自動検出がうまくいかない場合は、適切なサンドボックスを ClawMetry に指定します。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行（上級者向け）

OpenShell サンドボックス**内**で sync デーモンを実行する必要がある場合は、ClawMetry のインジェスト API に到達できるよう、NemoClaw ネットワークポリシーに以下のエグレスルールを追加してください。

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

以下のコマンドで適用します。

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ポートとエンドポイント

| エンドポイント | ポート | プロトコル | 必須 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | 必須（sync デーモン → クラウド） |
| `localhost:8900` | 8900 | HTTP | 必須（ローカルダッシュボード UI） |
| Docker ソケット (`/var/run/docker.sock`) | — | Unix ソケット | コンテナセッション検出に必要 |

sync デーモンは `ingest.clawmetry.com` への HTTPS アウトバウンド呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイメント

SSH トンネル、リバースプロキシ、Docker については **[クラウドテストガイド](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** をご覧ください。

## テスト

このプロジェクトは BrowserStack でテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetry は新しいマシンで初めて `clawmetry` CLI を実行した際に、`https://app.clawmetry.com/api/install` へ匿名の「初回実行」pingを1回送信します。これはインストール数のカウント（OSS プロジェクトで持っている唯一のマーケティング指標）と、ユーザーがインストールしているエージェントフレームワークの把握に使用されます。

**1回のインストールにつき1回の POST のみ**、以下の内容を含みます。

| フィールド | 例 | 目的 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` に保存されたランダム UUID | 重複排除。メールや api_key とは紐付けられない |
| `version` | `0.12.167` | 実際に使われているバージョンの把握 |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先度 |
| `python` | `3.11.15` | Python バージョンサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次に統合すべきエージェントの把握 |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールと CI のノイズを区別 |

**送信しないもの**: IP（クラウドはリクエストからサーバー側で国コードを導出した後、IP を破棄します）、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、api_key、メールアドレス、個人情報またはワークスペース固有の情報。送信ペイロードは [`clawmetry/telemetry.py`](clawmetry/telemetry.py) で監査可能です。

**オプトアウト**（いずれか1つで永続的に無効化されます）:

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ここでのネットワーク障害が `clawmetry` の実行をブロックすることはありません。ping は3秒のタイムアウトを持つデーモンスレッドでファイアアンドフォーゲット方式で実行されます。

## スター履歴

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT

---

<p align="center">
  <strong>🦞 エージェントの思考を可視化</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
