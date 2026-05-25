<!-- i18n-src:56ff57310588 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を可視化する。** [OpenClaw](https://github.com/openclaw/openclaw) AI エージェントのためのリアルタイム可観測性。

> 🌐 **他の言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

コマンド一つ。設定不要。すべてを自動検出します。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開いて、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## できること

- **Flow** — チャネル、ブレイン、ツールを通してメッセージが行き交う様子をリアルタイムで示すアニメーション図
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳によるトークンとコストの追跡
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行、所要時間を含むスケジュール済みジョブ
- **Logs** — 色分けされたリアルタイムのログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブル UI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検出。Slack、Discord、PagerDuty、Telegram、Email へルーティング
- **Approvals** — 破壊的な削除、強制プッシュ、DB の変更、sudo、パッケージのインストール、ネットワーク呼び出しをワンクリックの承認の背後でゲート

## スクリーンショット

### 🧠 Brain — エージェントイベントのライブストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッション概要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムのツール呼び出しフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデルとセッション別のコスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースのファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — 状態と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Email への Webhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツール呼び出しを手動承認の背後でゲート。ポリシーに裏付けられた保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## インストール

**ワンライナー (推奨):**
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

v2 React アプリは `frontend/` にあり、v2 を有効にして Flask
サーバーを起動すると `/v2` で配信されます。

開発時はターミナルを 2 つ使います:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` を開きます。Vite が `/api` リクエストを
`http://localhost:8900` にプロキシするため、React アプリは追加の CORS 設定なしで
ローカルの Flask サーバーと通信できます。

Python パッケージに同梱されるバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番用バンドルは `clawmetry/static/v2/dist/` に書き出されます。

## ランタイム / エージェントの互換性

ClawMetry は OpenClaw だけでなく、多くの AI エージェントランタイムを観測します。OpenClaw 以外の各ランタイムには、そのネイティブなセッション形式を ClawMetry の統一されたシェイプに変換する専用のリーダーアダプターが付属します。デーモンはそれらを同じ DuckDB ストアとクラウドスナップショットに取り込み、ランタイムでタグ付けします。複数のランタイムが存在する場合、Session リプレイタブに **ランタイムスイッチャー** が表示されます。完全なマトリックスとランタイム追加のガイドは [`docs/compatibility.md`](docs/compatibility.md) を、OpenClaw ファミリーの入門は [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) を参照してください。

| ランタイム / エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | Native | リファレンスランタイム、自動検出 |
| **PicoClaw** | Beta アダプター | フラットな `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | Beta アダプター | セッションごとの SQLite (`data/v2-sessions`)。トランスクリプトとメッセージ数。 |
| **Hermes** | Beta アダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | Beta アダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出しと思考、トークン使用量。 |
| **Codex** | Beta アダプター | ロールアウト JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | Beta アダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | Beta アダプター | プロジェクトごとの `.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | Beta アダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |

「Beta アダプター」とは、ClawMetry がそのランタイムの実際のオンディスク形式に対するリーダーを同梱しており、それぞれが実機の実インストールに対して構築・検証されている (`tests/fixtures/runtimes/<rt>/` を参照) ことを意味します。アダプターは読み取り専用で、それぞれそのランタイムが実際に保存する内容について正直です (例: PicoClaw/NanoClaw/Cursor はトークンコストをディスクに書き込みません)。1 つのノードで複数のランタイムが動作している場合、ランタイムスイッチャーがセッションビューを 1 つに絞り込み、すっきりとした詳細分析を可能にします。

## OpenTelemetry — ベンダー中立、トレースをどこへでも送信

ClawMetry は **GenAI セマンティック規約** を使って **OpenTelemetry** を双方向で話すため、エージェントのトレースが 1 つのツールにロックインされることはありません。

すべてのセッション (LLM 呼び出し、ツール、サブエージェント、トークン、コスト) を OTLP/HTTP の GenAI スパンとして、任意のコレクター (Datadog、Grafana、Honeycomb、または自前の OTel Collector) に **エクスポート** します:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔はオプションの環境変数です:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**取り込み** — 組み込みの OTLP レシーバーは、他のあらゆるものからのトレースとメトリクスを `/v1/traces` と `/v1/metrics` で受け付けます (protobuf の取り込みには `pip install clawmetry[otel]`)。

設定不要でローカルファーストの ClawMetry ダッシュボードと、チームがすでに運用している任意のバックエンドへのデータ、その両方が手に入ります。ロックインもなく、インストールすべき 2 つ目のエージェントもありません。

## 設定

ほとんどの人は設定を必要としません。ClawMetry はワークスペース、ログ、セッション、cron を自動検出します。

カスタマイズが必要な場合は:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

すべてのオプション: `clawmetry --help`

## サポートされているチャネル

ClawMetry は、あなたが設定したすべての OpenClaw チャネルのライブアクティビティを表示します。`openclaw.json` で実際にセットアップされているチャネルのみが Flow 図に表示され、未設定のものは自動的に非表示になります。

Flow 内の任意のチャネルノードをクリックすると、受信/送信メッセージ数を含むライブのチャットバブルビューが表示されます。

| チャネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | メッセージ、統計、10 秒ごとの更新 |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` を直接読み取り |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) 経由 |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli 経由 |
| 🟣 **Discord** | ✅ Full | ✅ | ギルド + チャネル検出 |
| 🟪 **Slack** | ✅ Full | ✅ | ワークスペース + チャネル検出 |
| 🌐 **Webchat** | ✅ Full | ✅ | 組み込みの Web UI セッション |
| 📡 **IRC** | ✅ Full | ✅ | ターミナル風のバブル UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API 経由の iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API Webhook 経由 |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams ボットプラグイン経由 |
| 🔷 **Mattermost** | ✅ Full | ✅ | セルフホストのチームチャット |
| 🟩 **Matrix** | ✅ Full | ✅ | 分散型、E2EE サポート |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | 分散型 NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC 接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket イベントサブスクリプション |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **自動検出:** ClawMetry は `~/.openclaw/openclaw.json` を読み取り、実際に設定したチャネルのみをレンダリングします。手動セットアップは不要です。

## Docker デプロイ

ClawMetry をコンテナで実行したいですか? 問題ありません! 🐳

**Docker でのクイックスタート:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **注:** Docker で実行する際は、ClawMetry がセットアップを自動検出できるよう、OpenClaw のワークスペースとログディレクトリを必ずマウントしてください。

## 必要要件

- Python 3.8+
- Flask (pip で自動的にインストールされます)
- 同じマシン上で動作している OpenClaw (または Docker 用のマウントされたボリューム)
- Linux または macOS

## NemoClaw / OpenShell サポート

ClawMetry は [NemoClaw](https://github.com/NVIDIA/NemoClaw) を自動検出します。これは、サンドボックス化された OpenShell コンテナ内でエージェントを実行する、OpenClaw 向けの NVIDIA のエンタープライズセキュリティラッパーです。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の `~/.openclaw/` にあっても、OpenShell コンテナ内にあっても、自動的に検出します。

### 仕組み

ClawMetry は 2 つの方法で NemoClaw を検出します:

1. **バイナリ検出** — `nemoclaw` CLI の有無を確認し、`nemoclaw status` を実行してサンドボックス情報を取得します
2. **コンテナ検出** — 実行中の Docker コンテナを `openshell`、`nemoclaw`、または `ghcr.io/nvidia/` イメージについてスキャンし、ボリュームマウントまたは `docker cp` 経由でセッションを読み取ります

NemoClaw コンテナから同期されたセッションファイルは、クラウドダッシュボードで `runtime=nemoclaw` と `container_id` のメタデータでタグ付けされるため、標準の OpenClaw セッションと一目で区別できます。

### 推奨セットアップ: ホスト上で同期デーモンを実行

最良の体験のためには、ClawMetry の同期デーモンを (サンドボックス内ではなく) **ホストマシン** で実行してください。これにより NemoClaw のネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中の任意の OpenShell コンテナ内のセッションを自動的に見つけます。

### オプション: 明示的なサンドボックス名

自動検出がうまくいかない場合は、ClawMetry を正しいサンドボックスに向けてください:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内で実行する (上級者向け)

どうしても同期デーモンを OpenShell サンドボックス **内** で実行する必要がある場合は、ClawMetry の取り込み API に到達できるよう、次の egress ルールを NemoClaw のネットワークポリシーに追加してください:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

次のコマンドで適用します:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ポートとエンドポイント

| エンドポイント | ポート | プロトコル | 必須 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | はい (同期デーモン → クラウド) |
| `localhost:8900` | 8900 | HTTP | はい (ローカルダッシュボード UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | コンテナセッションの検出用 |

同期デーモンは `ingest.clawmetry.com` への外向きの HTTPS 呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSH トンネル、リバースプロキシ、Docker については **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** を参照してください。

## テスト

このプロジェクトは BrowserStack でテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetry は、新しいマシンで初めて `clawmetry` CLI を実行したときに、
`https://app.clawmetry.com/api/install` へ匿名の「初回実行」ping を
1 回だけ送信します。これはインストール数のカウント (OSS プロジェクトで
私たちが持つ唯一のマーケティング指標) と、ユーザーがどのエージェント
フレームワークをインストールしているかを把握するために使います。

**インストールごとに POST はちょうど 1 回**で、次の内容を含みます:

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` に保存されるランダムな UUID | 重複排除用。あなたのメールや api_key とは結び付きません |
| `version` | `0.12.167` | どのバージョンが世に出回っているか |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位 |
| `python` | `3.11.15` | Python バージョンのサポートマトリックス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと統合すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールと CI のノイズを分ける |

**送信しないもの**: IP (クラウドはサーバー側でリクエストから国コードを
導出し、その後 IP を破棄します)、ホスト名、ユーザー名、ワークスペース
パス、ファイルの内容、あなたの api_key、メール、その他あらゆる PII や
ワークスペース固有の情報。ワイヤー上のペイロードは
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) で監査できます。

**オプトアウト** (次のいずれか 1 つで永続的に無効化されます):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ここでのネットワーク障害が `clawmetry` の実行をブロックすることは
決してありません。この ping は 3 秒タイムアウトのデーモンスレッド上で
撃ちっぱなしで実行されます。

## Star History

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
  <strong>🦞 See your agent think</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
