<!-- i18n-src:8252f6b1d31d -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を可視化。** **14種類のAIエージェントランタイム**をリアルタイムで観測: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類。あなたのエージェントフリート全体を1つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [もっと見る →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClawの観測ツールとして始まり、今では**エージェントフリート全体**をあなたのマシン上で自動検出し、1つのダッシュボードで計測します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClawとNemoClawはオープンソースアプリで無料です。それ以外のランタイムはClawMetry Cloud、またはセルフホストのProライセンスで有効になります。ヘッダーからランタイムを切り替えると、コスト・トークン・ツール・トレースなどすべてのタブがそのランタイムにスコープし直されます。正確な無料/有料の区分、ティア表、`/api/entitlement`のシェイプ、`clawmetry license` CLIについては**[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**を参照してください。

## できること

- **Flow** — チャンネル、ブレイン、ツールを行き来するメッセージの流れをリアルタイムでアニメーション表示
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コストトラッキング
- **Sessions** — モデル、トークン、最終活動時刻を含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行、所要時間を含むスケジュールジョブ
- **Logs** — 色分けされたリアルタイムログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、Emailへルーティング
- **Approvals** — 破壊的な削除、force push、DB変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリック承認の背後でゲート

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッションサマリー
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムツール呼び出しフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデル・セッション別コスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ポスチャーと監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Email へのウェブフック
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクの高いツール呼び出しを手動承認の背後でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Codeの実行前ブロック** — コマンド1つで、マッチしたツール呼び出しを実行**前**に一時停止し、あなたの判断を待つPreToolUseフックをインストールします（[クラウドプッシュ通知](https://app.clawmetry.com/push)を有効にすればスマートフォンからワンタップで対応可能）。

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

denyはその1回のツール呼び出しだけをブロックします。エージェントはセッションを維持したまま別のアプローチを試せます。スマートフォンで承認すると、Claude Code自体の権限確認プロンプトはスキップされます（あなたはすでに回答済みのため）。Claude Code自身があなたの判断待ちになったときも、スマートフォンにプッシュ通知が届きます（`permission_prompt` / `idle_prompt` 通知）。

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

v2 Reactアプリは`frontend/`にあり、v2を有効にしてFlaskサーバーを起動すると`/v2`で配信されます。

開発時は2つのターミナルを使用してください。

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

`http://localhost:5173/v2/`を開いてください。Viteが`/api`リクエストを`http://localhost:8900`にプロキシするため、Reactアプリは追加のCORS設定なしでローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには次のようにします。

```bash
cd frontend
npm run build
```

本番用バンドルは`clawmetry/static/v2/dist/`に書き出されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムには専用のリーダーアダプターが用意されており、そのランタイム固有のセッション形式をClawMetryの統一フォーマットに変換します。デーモンはそれらを同じDuckDBストア + クラウドスナップショットに取り込み、ランタイムでタグ付けし、複数のランタイムが存在する場合はSession replayタブに**ランタイムスイッチャー**が表示されます。全体のマトリクスとランタイム追加ガイドについては[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門については[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな`providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | ベータアダプター | セッションごとのSQLite（`data/v2-sessions`）。トランスクリプト + メッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出し + thinking、トークン使用量。 |
| **Codex** | ベータアダプター | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの`.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Pi** | ベータアダプター | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **Deep Agents** | ベータアダプター | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **n8n** | ベータアダプター | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録している範囲でのモデル + トークン。 |

「ベータアダプター」とは、ClawMetryがそのランタイムの実際のディスク上フォーマット用のリーダーを同梱していることを意味し、それぞれ実機での実インストールに対して構築・検証済みです（`tests/fixtures/runtimes/<rt>/`を参照）。アダプターは読み取り専用で、それぞれが自分のランタイムが実際にディスクへ保存しているものについて正直です（例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません）。複数のランタイムが1つのノードで動作している場合、ランタイムスイッチャーはセッションビューを1つにスコープしてクリーンに深掘りできるようにします。

## あらゆるSDKエージェントを追跡 — アウトループのコスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。しかし、OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の`httpx`ループで構築したあなた自身の**本番エージェント**はそうしません。ClawMetryのゼロ設定インターセプターは`httpx`/`requests`をモンキーパッチすることで、そのLLM呼び出し（コスト、トークン、レイテンシ、エラー）を取得します。

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`（または`CLAWMETRY_SOURCE=support-agent`環境変数）は各呼び出しに**名前付きソース**でタグ付けするため、実行しているすべてのプロダクトがダッシュボードのOverviewにある**🔌 Out-loop sourcesカード**にファーストクラスのコスト帰属可能な行として表示されます。呼び出し数、プロバイダー、レイテンシ、エージェントごとのエラー率です。ソースが設定されていなくても呼び出しは追跡されます。その場合、このカードは非表示のままです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターが供給しているのと同じデータ層（DuckDB → クラウドスナップショット）なので、アウトループソースも他のあらゆるデータと同様にクラウドダッシュボードへE2E暗号化された状態で同期されます。

## OpenTelemetry — ベンダーニュートラル、トレースをどこへでも送信

ClawMetryは**GenAIセマンティック規約**を使い、双方向で**OpenTelemetry**を話します。そのため、あなたのエージェントトレースは特定のツールにロックインされません。

各セッション（LLM呼び出し、ツール、サブエージェント、トークン、コスト）をOTLP/HTTP GenAIスパンとして任意のコレクター（Datadog、Grafana、Honeycomb、または自前のOTel Collector）に**エクスポート**します。

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔はオプションの環境変数です。

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**取り込み** — 組み込みのOTLPレシーバーは、`/v1/traces`と`/v1/metrics`で他のあらゆるものからのトレースとメトリクスを受け付けます（protobuf取り込みには`pip install clawmetry[otel]`が必要）。

ゼロ設定・ローカルファーストのClawMetryダッシュボード**と**、あなたのチームがすでに運用しているバックエンドの両方にデータが届きます。ロックインなし、2つ目のエージェントを追加インストールする必要もありません。

## 設定

ほとんどの人には設定は不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合は次のようにします。

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

すべてのオプション: `clawmetry --help`

## 対応チャンネル

ClawMetryは、あなたが設定したすべてのOpenClawチャンネルのライブアクティビティを表示します。`openclaw.json`で実際に設定されているチャンネルのみがFlowダイアグラムに表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャンネルノードをクリックすると、送受信メッセージ数付きのライブチャットバブルビューを見ることができます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒ごとのリフレッシュ |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db`を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web（Baileys）経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド + チャンネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース + チャンネル検出 |
| 🌐 **Webchat** | ✅ フル対応 | ✅ | 組み込みWeb UIセッション |
| 📡 **IRC** | ✅ フル対応 | ✅ | ターミナル風バブルUI |
| 🍏 **BlueBubbles** | ✅ フル対応 | ✅ | BlueBubbles REST API経由のiMessage |
| 🔵 **Google Chat** | ✅ フル対応 | ✅ | Chat API Webhook経由 |
| 🟣 **MS Teams** | ✅ フル対応 | ✅ | Teamsボットプラグイン経由 |
| 🔷 **Mattermost** | ✅ フル対応 | ✅ | セルフホストのチームチャット |
| 🟩 **Matrix** | ✅ フル対応 | ✅ | 分散型、E2EE対応 |
| 🟢 **LINE** | ✅ フル対応 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ フル対応 | ✅ | 分散型 NIP-04 DM |
| 🟣 **Twitch** | ✅ フル対応 | ✅ | IRC接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ フル対応 | ✅ | WebSocketイベント購読 |
| 🔵 **Zalo** | ✅ フル対応 | ✅ | Zalo Bot API |

> **自動検出:** ClawMetryは`~/.openclaw/openclaw.json`を読み取り、実際に設定したチャンネルのみを表示します。手動設定は不要です。

## Dockerデプロイ

ClawMetryをコンテナで実行したいですか？問題ありません 🐳

**Dockerでのクイックスタート:**

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

> **注意:** Docker上で実行する場合、ClawMetryがあなたのセットアップを自動検出できるように、エージェントのデータ + ログディレクトリ（例: `~/.openclaw`、`~/.claude`、`~/.codex`）をマウントしてください。

## 必要条件

- Python 3.8+
- Flask（pip経由で自動インストール）
- 同じマシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n（またはDocker用のマウントボリューム）
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは[NemoClaw](https://github.com/NVIDIA/NemoClaw)（NVIDIAのエンタープライズセキュリティラッパーで、OpenShellコンテナ内でサンドボックス化されたエージェントを実行するOpenClaw向けツール）を自動検出します。

ほとんどの場合、追加設定は不要です。同期デーモンは、セッションファイルがホスト上の`~/.openclaw/`にあるか、OpenShellコンテナ内にあるかにかかわらず自動発見します。

### 仕組み

ClawMetryは2通りの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの存在を確認し、`nemoclaw status`を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを`openshell`、`nemoclaw`、`ghcr.io/nvidia/`イメージでスキャンし、ボリュームマウントまたは`docker cp`経由でセッションを読み取り

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボードで`runtime=nemoclaw`と`container_id`メタデータがタグ付けされるため、標準的なOpenClawセッションと一目で見分けられます。

### 推奨セットアップ: ホスト上の同期デーモン

最良の体験のためには、ClawMetryの同期デーモンを（サンドボックス内ではなく）**ホストマシン**で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中の任意のOpenShellコンテナ内のセッションを自動的に見つけます。

### オプション: サンドボックス名を明示する

自動検出がうまくいかない場合は、正しいサンドボックスをClawMetryに指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内で実行する（上級者向け）

同期デーモンをOpenShellサンドボックス**内**で実行する必要がある場合は、NemoClawネットワークポリシーに次のegressルールを追加し、ClawMetryのingest APIに到達できるようにしてください。

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
| Dockerソケット（`/var/run/docker.sock`） | — | Unixソケット | コンテナセッション発見用 |

同期デーモンは`ingest.clawmetry.com`への発信HTTPS通信のみを行います。受信ポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetryは`https://app.clawmetry.com/api/install`へ匿名のインストールライフサイクルPingを送信します。新しいマシンで`clawmetry` CLIを初めて実行したときの`install`ピング1回、新しいバージョンへアップグレードした後の最初の実行時の`update`ピング1回、ダッシュボード内のオンボーディング選択を完了したときの`onboarded`ピング1回です。これは、実際のインストール数を数えるため（生のPyPIダウンロード数の約98%はミラー、CI、自動更新の再ダウンロードです）、そしてどのエージェントフレームワークとバージョンが実際に使われているかを把握するために利用します。

**ライフサイクルイベント・バージョンごとに最大1回のPOST**で、次を含みます。

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`に保存されたランダムUUID | 重複排除。Cloud syncを明示的に接続するまでは匿名（その後は認証済みのデーモンハートビートがこのIDを運び、このインストールをあなたのアカウントに紐づけます） |
| `event` | `install` / `update` / `onboarded` | 新規インストールか既存のアップグレードかの判別 |
| `version` | `0.12.167` | どのバージョンが実際に使われているか |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位 |
| `python` | `3.11.15` | Pythonバージョンサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと連携すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの分離 |

**送信しないもの**: IP（クラウドはサーバー側でリクエストから国コードを導出した後、IPを破棄します）、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤーペイロードは[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で監査可能です。

**オプトアウト**（いずれか1つで永続的に無効化されます）:

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ここでのネットワーク障害が`clawmetry`の実行をブロックすることはありません。このPingはデーモンスレッド上でfire-and-forget方式、タイムアウト3秒で送信されます。

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
