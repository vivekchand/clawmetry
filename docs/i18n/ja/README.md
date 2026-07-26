<!-- i18n-src:bab48eec552f -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**あなたのエージェントの思考を見る。** **14種類のAIエージェントランタイム**に対応したリアルタイム可観測性: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類。エージェントフリート全体を1つのダッシュボードで。

> 🌐 **多言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [他の言語 →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClawの可観測性ツールとして始まりましたが、今では**エージェントフリート全体**を1つのダッシュボードで計測し、マシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClawとNemoClawはオープンソースアプリで無料利用でき、その他のランタイムはClawMetry Cloudまたはセルフホストの Pro ライセンスで有効になります。ヘッダーからランタイムを切り替えると、コスト・トークン・ツール・トレースなどすべてのタブがそのランタイムにスコープし直されます。正確な無料/有料の区分、ティア表、`/api/entitlement` の形状、`clawmetry license` CLI については **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** を参照してください。

## 主な機能

- **Flow** — チャネル、ブレイン、ツールを経由してメッセージが流れる様子をライブアニメーションで表示
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コストトラッキング
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行、実行時間付きのスケジュールジョブ
- **Logs** — カラーコード付きのリアルタイムログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、Emailへのルーティング
- **Approvals** — 破壊的な削除、フォースプッシュ、DB変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリック承認の背後でゲート

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッションサマリー
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムのツール呼び出しフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデル・セッション別のコスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — セキュリティ態勢と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Emailへのwebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツール呼び出しを手動承認の背後でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Codeの実行前ブロッキング** コマンド1つで、対象のツール呼び出しを実行*前*に一時停止し、あなたの判断を待つPreToolUseフックがインストールされます([クラウドプッシュ通知](https://app.clawmetry.com/push)を有効にしておけば、スマホからワンタップで対応可能です)。

```bash
clawmetry hooks install     # ~/.claude/settings.json に書き込む（冪等）
clawmetry hooks status      # 何が組み込まれているか、何個のポリシーが有効か
clawmetry hooks uninstall   # ClawMetryのエントリのみを削除
```

deny(拒否)はその1回のツール呼び出しのみをブロックします。エージェントはセッションを維持したまま別のアプローチを試せます。スマホでの承認はClaude Code自身の権限プロンプトをスキップします(すでに回答済みのため)。マッチしないツールは約40msのコストで、Claude Codeの通常の権限フローにそのまま渡ります。Claude Code自身があなたの対応を待っているときも(`permission_prompt` / `idle_prompt` 通知)、スマホにプッシュ通知が届きます。

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

## v2フロントエンド開発

v2のReactアプリは `frontend/` にあり、v2が有効な状態でFlaskサーバーを起動すると `/v2` で配信されます。

開発時はターミナルを2つ使用します。

```bash
# ターミナル1: Flask API/サーバーを :8900 で起動
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ターミナル2: Vite開発サーバーを :5173 で起動
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` を開いてください。Viteが `/api` へのリクエストを `http://localhost:8900` にプロキシするため、追加のCORS設定なしでReactアプリがローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱されるバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番ビルドは `clawmetry/static/v2/dist/` に出力されます。

## ランタイム/エージェントの互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムには専用のリーダーアダプタが用意されており、そのランタイム固有のセッション形式をClawMetryの統一された形状に変換します。デーモンはこれらを同じDuckDBストア + クラウドスナップショットに取り込み、ランタイムでタグ付けします。また、複数のランタイムが存在する場合、Session replayタブに**ランタイム切り替え**が表示されます。完全なマトリクスとランタイム追加ガイドは [`docs/compatibility.md`](docs/compatibility.md) を、OpenClawファミリーの入門は [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプタ | フラットな `providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | ベータアダプタ | セッションごとのSQLite（`data/v2-sessions`）。トランスクリプト + メッセージ数。 |
| **Hermes** | ベータアダプタ | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプタ | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出し + thinking、トークン使用量。 |
| **Codex** | ベータアダプタ | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | ベータアダプタ | SQLite `state.vscdb`。チャット/コンポーザートランスクリプト、モデル。 |
| **Aider** | ベータアダプタ | プロジェクトごとの `.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプタ | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |
| **opencode** | ベータアダプタ | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **Qwen Code** | ベータアダプタ | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Pi** | ベータアダプタ | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **Deep Agents** | ベータアダプタ | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |

「ベータアダプタ」とは、ClawMetryがそのランタイムの実際のディスク上フォーマット用のリーダーを提供していることを意味し、それぞれ実マシン上の実際のインストールに対してビルド・検証されています（`tests/fixtures/runtimes/<rt>/` を参照）。アダプタは読み取り専用であり、それぞれが自分のランタイムが実際に保存しているものについて正直です（例えばPicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません）。複数のランタイムが1つのノードで動作している場合、ランタイム切り替えでセッションビューを1つに絞り込み、クリーンに深掘りできます。

## 任意のSDKエージェントを追跡 — アウトループのコスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。しかし、あなた自身が構築した**本番エージェント**、つまりOpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは単純な `httpx` ループの上に作ったものは、そうではありません。ClawMetryのゼロコンフィグ インターセプタは、`httpx`/`requests` をモンキーパッチすることで、そのLLM呼び出し（コスト、トークン、レイテンシ、エラー）を引き続き捕捉します。

```python
import clawmetry.track            # インターセプタを有効化
clawmetry.track.set_source("support-agent")   # このプロダクトに名前を付ける

# ...エージェントは通常どおり動作し、すべてのLLM呼び出しが追跡・帰属されます。
```

`set_source()`（または `CLAWMETRY_SOURCE=support-agent` 環境変数）は各呼び出しに**名前付きソース**でタグ付けするため、実行しているすべてのプロダクトがダッシュボードのOverviewにある**🔌 Out-loop sources**カードに、それぞれ独立したコスト帰属可能な行として表示されます — エージェントごとの呼び出し数、プロバイダ、レイテンシ、エラー率。ソースを設定しない場合でも呼び出しは追跡されますが、このカードは非表示のままです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプタと同じデータ層（DuckDB → クラウドスナップショット）を使用しているため、アウトループのソースも他のすべてのデータと同様にクラウドダッシュボードへ同期され、E2E暗号化されます。

## OpenTelemetry — ベンダーニュートラルに、どこへでもトレースを送信

ClawMetryは**GenAIセマンティック規約**を使い、双方向で**OpenTelemetry**を話します。そのため、あなたのエージェントのトレースが1つのツールにロックインされることはありません。

すべてのセッション（LLM呼び出し、ツール、サブエージェント、トークン、コスト）を、OTLP/HTTP GenAIスパンとして任意のコレクタ（Datadog、Grafana、Honeycomb、または自前のOTel Collector）に**エクスポート**できます。

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 同等の指定方法:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔はオプションの環境変数です。

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 追加のHTTPヘッダー
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒単位（デフォルト60）
```

**取り込み** — 組み込みのOTLPレシーバは、`/v1/traces` と `/v1/metrics` で他のあらゆるソースからのトレースとメトリクスを受け付けます（protobuf取り込みには `pip install clawmetry[otel]`）。

ゼロコンフィグでローカルファーストなClawMetryダッシュボード**と**、チームがすでに運用しているバックエンドへのデータ送信を両立できます。ロックインなし、2つ目のエージェントをインストールする必要もありません。

## 設定

ほとんどの人は設定不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合は次のとおりです。

```bash
clawmetry --port 9000              # カスタムポート（デフォルト: 8900）
clawmetry --host 127.0.0.1         # localhostのみにバインド
clawmetry --workspace ~/mybot      # カスタムワークスペースパス
clawmetry --name "Alice"           # Flow可視化に表示する名前
```

すべてのオプション: `clawmetry --help`

## 対応チャネル

ClawMetryは、設定済みのOpenClawチャネルすべてについてライブアクティビティを表示します。`openclaw.json` で実際に設定されているチャネルのみがFlowダイアグラムに表示され、未設定のチャネルは自動的に非表示になります。

Flow内の任意のチャネルノードをクリックすると、受信/送信メッセージ数付きのライブチャットバブルビューが表示されます。

| チャネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db` を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web（Baileys）経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド + チャネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース + チャネル検出 |
| 🌐 **Webchat** | ✅ フル対応 | ✅ | 組み込みWeb UIセッション |
| 📡 **IRC** | ✅ フル対応 | ✅ | ターミナル風バブルUI |
| 🍏 **BlueBubbles** | ✅ フル対応 | ✅ | BlueBubbles REST API経由のiMessage |
| 🔵 **Google Chat** | ✅ フル対応 | ✅ | Chat API webhook経由 |
| 🟣 **MS Teams** | ✅ フル対応 | ✅ | Teams botプラグイン経由 |
| 🔷 **Mattermost** | ✅ フル対応 | ✅ | セルフホスト型チームチャット |
| 🟩 **Matrix** | ✅ フル対応 | ✅ | 分散型、E2EE対応 |
| 🟢 **LINE** | ✅ フル対応 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ フル対応 | ✅ | 分散型NIP-04 DM |
| 🟣 **Twitch** | ✅ フル対応 | ✅ | IRC接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ フル対応 | ✅ | WebSocketイベント購読 |
| 🔵 **Zalo** | ✅ フル対応 | ✅ | Zalo Bot API |

> **自動検出:** ClawMetryは `~/.openclaw/openclaw.json` を読み取り、実際に設定されているチャネルのみを描画します。手動設定は不要です。

## Dockerデプロイ

ClawMetryをコンテナで実行したいですか？問題ありません 🐳

**Dockerでのクイックスタート:**

```bash
# イメージをビルド
docker build -t clawmetry .

# デフォルト設定で実行
docker run -p 8900:8900 clawmetry

# またはエージェントのデータディレクトリをマウント（例: OpenClawの ~/.openclaw）
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Composeの例:**

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

> **注:** Docker上で実行する場合は、エージェントのデータ + ログディレクトリ（例: `~/.openclaw`、`~/.claude`、`~/.codex`）をマウントして、ClawMetryがセットアップを自動検出できるようにしてください。

## 動作要件

- Python 3.8以上
- Flask（pip経由で自動インストール）
- 同じマシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agentsのいずれか（またはDocker用にマウントされたボリューム）
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは、OpenClawをサンドボックス化されたOpenShellコンテナ内で実行するNVIDIAのエンタープライズセキュリティラッパーである [NemoClaw](https://github.com/NVIDIA/NemoClaw) を自動検出します。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の `~/.openclaw/` にあるか、OpenShellコンテナ内にあるかにかかわらず自動的に発見します。

### 仕組み

ClawMetryは2つの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの存在を確認し、`nemoclaw status` を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを `openshell`、`nemoclaw`、`ghcr.io/nvidia/` イメージについてスキャンし、ボリュームマウントまたは `docker cp` 経由でセッションを読み取る

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボード上で `runtime=nemoclaw` と `container_id` メタデータがタグ付けされるため、標準的なOpenClawセッションと一目で区別できます。

### 推奨セットアップ: ホスト上での同期デーモン

最良の体験のために、ClawMetryの同期デーモンは（サンドボックス内ではなく）**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# ホスト上で（サンドボックスの外側）
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中のOpenShellコンテナ内のセッションを自動的に見つけます。

### オプション: サンドボックス名の明示指定

自動検出がうまくいかない場合は、ClawMetryに正しいサンドボックスを指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行（上級者向け）

同期デーモンをOpenShellサンドボックスの**内部**で実行する必要がある場合は、ClawMetryのingest APIに到達できるよう、NemoClawのネットワークポリシーに次のegressルールを追加してください。

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

適用方法:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ポートとエンドポイント

| エンドポイント | ポート | プロトコル | 必須 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | はい（同期デーモン → クラウド） |
| `localhost:8900` | 8900 | HTTP | はい（ローカルダッシュボードUI） |
| Dockerソケット（`/var/run/docker.sock`） | — | Unixソケット | コンテナセッション検出用 |

同期デーモンは `ingest.clawmetry.com` へのアウトバウンドHTTPS呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては **[クラウドテストガイド](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetryは、新しいマシンで `clawmetry` CLIを初めて実行したときに、匿名の「初回実行」pingを1回だけ `https://app.clawmetry.com/api/install` に送信します。これはインストール数をカウントするため（OSSプロジェクトとして持っている唯一のマーケティング指標です）、そしてユーザーがどのエージェントフレームワークをインストールしているかを知るために使用します。

**インストールごとにちょうど1回のPOST**が送信され、以下を含みます。

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` に保存されたランダムUUID | 重複排除用。あなたのメールやapi_keyには紐付きません |
| `version` | `0.12.167` | どのバージョンが実際に使われているか |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先度 |
| `python` | `3.11.15` | Pythonバージョンサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと連携すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの区別 |

**送信しないもの**: IPアドレス（クラウド側がリクエストからサーバーサイドで国コードを導出した後、IPは破棄します）、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤー上のペイロードは [`clawmetry/telemetry.py`](clawmetry/telemetry.py) で監査可能です。

**オプトアウト**（以下のいずれか1つで永続的に無効化されます）:

```bash
export CLAWMETRY_NO_TELEMETRY=1                # シェルごと
export DO_NOT_TRACK=1                          # W3Cのクロスツール標準
touch ~/.clawmetry/notelemetry                 # 永続的なファイルマーカー
```

ネットワーク障害があっても `clawmetry` の実行がブロックされることはありません。このpingはデーモンスレッド上でfire-and-forget方式で送信され、タイムアウトは3秒です。

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
  <strong>🦞 See your agent think</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
