<!-- i18n-src:8f42d460a973 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**あなたのエージェントの思考を見る。** **14種類のAIエージェントランタイム**向けのリアルタイムオブザーバビリティ: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類。エージェントフリート全体をひとつのダッシュボードで。

> 🌐 **この文書の他言語版:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [もっと見る →](docs/i18n/)

コマンドひとつ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClaw向けのオブザーバビリティとして始まりましたが、現在は**エージェントフリート全体**をひとつのダッシュボードで計測し、マシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClawとNemoClawはオープンソースアプリ内で無料です。それ以外のランタイムはClawmetry Cloud、またはセルフホストのProライセンスで利用可能になります。ヘッダーからランタイムを切り替えると、コスト・トークン・ツール・トレースなど各タブがそのランタイムにスコープし直されます。無料/有料の正確な区分、ティアマトリクス、`/api/entitlement`の形式、`clawmetry license` CLIについては**[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**を参照してください。

## 得られるもの

- **Flow** — チャンネル、ブレイン、ツール間を流れるメッセージを表示するライブアニメーション図
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コストトラッキング
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行時刻、実行時間を含むスケジュールジョブ
- **Logs** — 色分けされたリアルタイムログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、Emailへのルーティング
- **Approvals** — 破壊的な削除、force push、DB変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリック承認の背後でゲート

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッションサマリー
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムツールコールフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデル・セッション別のコスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — ポスチャーと監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Email へのWebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクの高いツールコールを手動承認の背後でゲート。ポリシーに基づく保護ルール
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

v2のReactアプリは`frontend/`にあり、v2が有効な状態でFlaskサーバーを起動すると`/v2`で配信されます。

開発中はターミナルを2つ使用してください。

```bash
# ターミナル1: FlaskのAPI/サーバーを :8900 で起動
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ターミナル2: Viteの開発サーバーを :5173 で起動
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` を開いてください。Viteが`/api`リクエストを`http://localhost:8900`にプロキシするため、Reactアプリは追加のCORS設定なしにローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番ビルドは`clawmetry/static/v2/dist/`に出力されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムには専用のリーダーアダプターが用意されており、そのランタイム固有のセッション形式をClawMetryの統一された形式に変換します。デーモンはそれらを同じDuckDBストア + クラウドスナップショットに取り込み、ランタイムでタグ付けします。複数のランタイムが存在する場合、Session replayタブに**ランタイム切り替え機能**が表示されます。完全なマトリクスとランタイム追加ガイドについては[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門については[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな`providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。トランスクリプト、モデル、ツールコール。 |
| **NanoClaw** | ベータアダプター | セッションごとのSQLite（`data/v2-sessions`）。トランスクリプト + メッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツールコール + 思考過程、トークン使用量。 |
| **Codex** | ベータアダプター | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの`.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツールコール、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツールコール、トークン + コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Pi** | ベータアダプター | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツールコール、トークン + コスト。 |
| **Deep Agents** | ベータアダプター | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツールコール、トークン + コスト。 |

「ベータアダプター」とは、ClawMetryがそのランタイムの実際のディスク上フォーマット用のリーダーを提供していることを意味し、それぞれが実機の実インストールに対して構築・検証されています（`tests/fixtures/runtimes/<rt>/`参照）。アダプターはすべて読み取り専用で、それぞれ自分のランタイムが実際にディスクに保存している内容について正直です（例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません）。1つのノードで複数のランタイムが動作している場合、ランタイム切り替え機能がセッションビューをひとつに絞り込み、クリーンな深掘りを可能にします。

## 任意のSDKエージェントを追跡 — アウトループでのコスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。しかし、OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の`httpx`ループの上に構築したあなた自身の**本番エージェント**は、それを行いません。ClawMetryの設定不要なインターセプターは、`httpx`/`requests`をモンキーパッチすることで、そのLLM呼び出し（コスト、トークン、レイテンシ、エラー）をそれでも捕捉します。

```python
import clawmetry.track            # インターセプターを有効化
clawmetry.track.set_source("support-agent")   # このプロダクトに名前を付ける

# ...エージェントは通常通り動作し、すべてのLLM呼び出しが追跡・帰属されます。
```

`set_source()`（または`CLAWMETRY_SOURCE=support-agent`環境変数）は各呼び出しに**名前付きソース**でタグ付けするため、実行しているすべてのプロダクトがOverviewの**🔌 アウトループソース**カードにおいて、独立した一級のコスト帰属可能な行として表示されます。エージェントごとの呼び出し数、プロバイダー、レイテンシ、エラー率です。ソースを設定していない場合でも呼び出しは追跡され続けます。カードが非表示になるだけです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターが供給しているのと同じデータ層（DuckDB → クラウドスナップショット）なので、アウトループソースも他のすべてと同様にE2E暗号化されてクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラル、トレースをどこへでも送信

ClawMetryは**GenAIセマンティック規約**を用いて双方向で**OpenTelemetry**を話すため、エージェントのトレースが特定のツールにロックインされることはありません。

すべてのセッション（LLM呼び出し、ツール、サブエージェント、トークン、コスト）を、任意のコレクター（Datadog、Grafana、Honeycomb、または自前のOTel Collector）にOTLP/HTTP GenAIスパンとして**エクスポート**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 同等の指定:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔はオプションの環境変数です。

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 追加のHTTPヘッダー
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒単位（デフォルト60）
```

**取り込み** — 組み込みのOTLPレシーバーは、`/v1/traces`と`/v1/metrics`で他の任意のソースからのトレースとメトリクスを受け付けます（protobuf取り込みには`pip install clawmetry[otel]`）。

設定不要でローカルファーストなClawMetryダッシュボードと、チームがすでに使っているバックエンドへのデータの両方が手に入ります。ロックインなし、追加のエージェントのインストールも不要です。

## 設定

ほとんどの人には設定は不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合:

```bash
clawmetry --port 9000              # カスタムポート（デフォルト: 8900）
clawmetry --host 127.0.0.1         # localhostのみにバインド
clawmetry --workspace ~/mybot      # カスタムワークスペースパス
clawmetry --name "Alice"           # Flow可視化に表示される名前
```

全オプション: `clawmetry --help`

## 対応チャンネル

ClawMetryは、設定済みのすべてのOpenClawチャンネルについてライブアクティビティを表示します。`openclaw.json`で実際に設定されているチャンネルのみがFlow図に表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャンネルノードをクリックすると、送受信メッセージ数を含むライブチャットバブルビューが表示されます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒ごとの更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db`を直接読み込み |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web（Baileys）経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド + チャンネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース + チャンネル検出 |
| 🌐 **Webchat** | ✅ フル対応 | ✅ | 組み込みWeb UIセッション |
| 📡 **IRC** | ✅ フル対応 | ✅ | ターミナル風バブルUI |
| 🍏 **BlueBubbles** | ✅ フル対応 | ✅ | BlueBubbles REST API経由のiMessage |
| 🔵 **Google Chat** | ✅ フル対応 | ✅ | Chat API Webhook経由 |
| 🟣 **MS Teams** | ✅ フル対応 | ✅ | Teams botプラグイン経由 |
| 🔷 **Mattermost** | ✅ フル対応 | ✅ | セルフホストのチームチャット |
| 🟩 **Matrix** | ✅ フル対応 | ✅ | 分散型、E2EE対応 |
| 🟢 **LINE** | ✅ フル対応 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ フル対応 | ✅ | 分散型NIP-04 DM |
| 🟣 **Twitch** | ✅ フル対応 | ✅ | IRC接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ フル対応 | ✅ | WebSocketイベントサブスクリプション |
| 🔵 **Zalo** | ✅ フル対応 | ✅ | Zalo Bot API |

> **自動検出:** ClawMetryは`~/.openclaw/openclaw.json`を読み取り、実際に設定されているチャンネルのみを描画します。手動設定は不要です。

## Dockerデプロイ

ClawMetryをコンテナで実行したいですか？問題ありません 🐳

**Dockerでのクイックスタート:**

```bash
# イメージをビルド
docker build -t clawmetry .

# デフォルト設定で実行
docker run -p 8900:8900 clawmetry

# もしくはエージェントのデータディレクトリをマウント（例: OpenClawの ~/.openclaw）
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

> **注:** Docker上で実行する場合、ClawMetryがセットアップを自動検出できるよう、エージェントのデータ + ログディレクトリ（例: `~/.openclaw`、`~/.claude`、`~/.codex`）をマウントしてください。

## 動作要件

- Python 3.8+
- Flask（pip経由で自動インストール）
- 同一マシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents のいずれか（Dockerの場合はマウントされたボリューム）
- LinuxまたはmacOS

## NemoClaw / OpenShell対応

ClawMetryは、サンドボックス化されたOpenShellコンテナ内でエージェントを実行するNVIDIAのエンタープライズセキュリティラッパーである[NemoClaw](https://github.com/NVIDIA/NemoClaw)を自動検出します。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の`~/.openclaw/`にあるか、OpenShellコンテナ内にあるかに関わらず自動的に発見します。

### 仕組み

ClawMetryは2つの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの有無を確認し、`nemoclaw status`を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを`openshell`、`nemoclaw`、`ghcr.io/nvidia/`イメージについてスキャンし、ボリュームマウントまたは`docker cp`経由でセッションを読み取る

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボードで`runtime=nemoclaw`と`container_id`のメタデータがタグ付けされるため、標準のOpenClawセッションと一目で区別できます。

### 推奨セットアップ: ホスト上での同期デーモン実行

最良の体験のために、ClawMetryの同期デーモンは（サンドボックス内ではなく）**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# ホスト上（サンドボックスの外）で
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中のOpenShellコンテナ内のセッションを自動的に見つけます。

### オプション: サンドボックス名を明示的に指定

自動検出が機能しない場合は、正しいサンドボックスをClawMetryに指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行（上級者向け）

同期デーモンをOpenShellサンドボックスの**内部**で実行しなければならない場合、ClawMetryの取り込みAPIに到達できるよう、NemoClawのネットワークポリシーに以下のegressルールを追加してください。

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

同期デーモンは`ingest.clawmetry.com`へのアウトバウンドHTTPS呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[クラウドテストガイド](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリー

ClawMetryは、新しいマシンで`clawmetry` CLIを初めて実行した際に、単発の匿名「初回実行」pingを`https://app.clawmetry.com/api/install`に送信します。これはインストール数をカウントするため（OSSプロジェクトとして持つ唯一のマーケティング指標です）、そしてユーザーがどのエージェントフレームワークをインストールしているかを把握するために使用します。

**インストールごとに正確に1回のPOST**が送信され、以下を含みます。

| フィールド | 例 | 目的 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`に保存されるランダムなUUID | 重複排除用。あなたのメールアドレスやapi_keyとは紐付いていません |
| `version` | `0.12.167` | 実際に使われているバージョンの把握 |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先度判断 |
| `python` | `3.11.15` | Pythonバージョンサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと連携すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの区別 |

**送信しない内容**: IPアドレス（クラウド側でリクエストからサーバーサイドで国コードを導出し、その後IPは破棄されます）、ホスト名、ユーザー名、ワークスペースパス、ファイルの内容、あなたのapi_key、メールアドレス、その他のPIIやワークスペース固有の情報は一切送信しません。通信ペイロードは[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で監査可能です。

**オプトアウト**（以下のいずれか1つで恒久的に無効化されます）:

```bash
export CLAWMETRY_NO_TELEMETRY=1                # シェルごと
export DO_NOT_TRACK=1                          # W3Cのクロスツール標準
touch ~/.clawmetry/notelemetry                 # 永続的なファイルマーカー
```

ネットワーク障害が発生しても`clawmetry`の実行がブロックされることはありません。このpingはデーモンスレッド上でfire-and-forget方式で送信され、タイムアウトは3秒です。

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
  <strong>🦞 あなたのエージェントの思考を見る</strong><br>
  <sub>開発者 <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> エコシステムの一部</sub>
</p>
