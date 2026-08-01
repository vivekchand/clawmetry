<!-- i18n-src:191e9094d7fa -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**あなたのエージェントの思考を見る。** **14種類のAIエージェントランタイム**向けのリアルタイム観測ツールです: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類。あなたのエージェントフリート全体を1つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [もっと見る →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClawの観測ツールとして始まりましたが、現在では**あなたのエージェントフリート全体**を1つのダッシュボードで計測し、マシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClawとNemoClawはオープンソースアプリ内で無料です。その他のランタイムはClawMetry Cloudまたはセルフホスト型のProライセンスで利用可能になります。ヘッダーからランタイムを切り替えると、コスト、トークン、ツール、トレースなどすべてのタブがそのランタイムに合わせて再スコープされます。正確な無料/有料の区分、ティア表、`/api/entitlement`の形式、`clawmetry license` CLIについては**[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**を参照してください。

## 得られるもの

- **Flow** — チャネル、ブレイン、ツールを通じてメッセージが流れる様子を示すライブアニメーション図
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コストトラッキング
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行、実行時間を含むスケジュールジョブ
- **Logs** — カラーコード化されたリアルタイムログストリーミング
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

### 🔐 Security — セキュリティ態勢と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Emailへのwebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツールコールを手動承認の背後でゲート。ポリシーに基づいた保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Codeの実行前ブロッキング** — 1つのコマンドで、一致するツールコールを実行**前**に一時停止し、あなたの判断を待つPreToolUseフックをインストールできます([クラウドプッシュ通知](https://app.clawmetry.com/push)を有効にすれば、スマートフォンから1タップで対応可能です):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

deny(拒否)はそのツールコール1件だけをブロックします。エージェントはセッションを維持したまま別のアプローチを試すことができます。スマートフォンで承認すると、Claude Code自体の許可プロンプトはスキップされます(あなたはすでに回答済みのため)。Claude Code自体があなたの判断待ちの場合も、スマートフォンにプッシュ通知が届きます(`permission_prompt` / `idle_prompt` 通知)。

## インストール

**ワンライナー(推奨):**
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

v2 Reactアプリは`frontend/`にあり、Flaskサーバーがv2を有効にして起動されると`/v2`で配信されます。

開発時は2つのターミナルを使用してください:

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

`http://localhost:5173/v2/` を開いてください。Viteは`/api`リクエストを`http://localhost:8900`にプロキシするため、追加のCORS設定なしでReactアプリがローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番用バンドルは`clawmetry/static/v2/dist/`に出力されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムは、そのランタイム固有のセッション形式をClawMetryの統一形式に変換する専用のリーダーアダプターを備えています。デーモンはそれらを同じDuckDBストア + クラウドスナップショットに取り込み、ランタイムでタグ付けし、複数のランタイムが存在する場合、Session replayタブに**ランタイムスイッチャー**が表示されます。完全な対応表とランタイム追加ガイドは[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門については[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

[Perplexityのnumbat](https://github.com/perplexityai/numbat)エージェントセキュリティツールを使用していますか?ClawMetryはその検出結果と実施判断をそのまま取り込みます。詳しくは[`docs/NUMBAT.md`](docs/NUMBAT.md)を参照してください。

| ランタイム/エージェント | ステータス | メモ |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな`providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツールコール。 |
| **NanoClaw** | ベータアダプター | セッションごとのSQLite(`data/v2-sessions`)。トランスクリプト + メッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツールコール + 思考、トークン使用量。 |
| **Codex** | ベータアダプター | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの`.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツールコール、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツールコール、トークン + コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Pi** | ベータアダプター | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツールコール、トークン + コスト。 |
| **Deep Agents** | ベータアダプター | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツールコール、トークン + コスト。 |
| **n8n** | ベータアダプター | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録している場合のモデル + トークン。 |
| **Antigravity** | ベータアダプター | `~/.gemini/<flavor>/brain/`配下のBrain JSONL。会話、ツールステップ、思考、生成ごとのGeminiトークン内訳 + コスト、バックグラウンド生成の消費。 |

「ベータアダプター」とは、そのランタイムが実際にディスク上に保存する形式に対して、実機の実際のインストールに基づいて構築・検証されたリーダーをClawMetryが提供していることを意味します(`tests/fixtures/runtimes/<rt>/`を参照)。アダプターは読み取り専用であり、それぞれ自身のランタイムが実際に何を保存しているかについて正直です(例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません)。1つのノードで複数のランタイムが稼働している場合、ランタイムスイッチャーによってセッションビューを1つに絞り込み、クリーンに深堀りできます。

## 任意のSDKエージェントをトラッキング — アウトループのコスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。あなたが構築した**本番エージェント**、つまりOpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の`httpx`ループの上に構築されたものはそうではありません。ClawMetryのゼロコンフィグインターセプターは、`httpx`/`requests`をモンキーパッチすることで、そうしたエージェントのLLM呼び出し(コスト、トークン、レイテンシ、エラー)を引き続き取得します:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(または`CLAWMETRY_SOURCE=support-agent`環境変数)は各呼び出しに**名前付きソース**をタグ付けするため、実行している各プロダクトはダッシュボードのOverviewにある**🔌 Out-loop sources**カードにおいて、独立したコスト帰属可能な項目として表示されます。エージェントごとの呼び出し数、プロバイダー、レイテンシ、エラー率が確認できます。ソースを設定していない場合でも呼び出しは引き続きトラッキングされ、カードが非表示になるだけです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターが供給しているのと同じデータレイヤー(DuckDB → クラウドスナップショット)なので、アウトループソースも他のすべてのデータと同様にE2E暗号化されたままクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラル、トレースをどこへでも送信

ClawMetryは**GenAIセマンティック規約**を用いて双方向に**OpenTelemetry**を話すため、あなたのエージェントトレースが1つのツールにロックインされることはありません。

各セッション(LLM呼び出し、ツール、サブエージェント、トークン、コスト)を、任意のコレクター(Datadog、Grafana、Honeycomb、または自前のOTel Collector)へOTLP/HTTPのGenAIスパンとして**エクスポート**します:

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

**取り込み** — 組み込みのOTLPレシーバーは、`/v1/traces`および`/v1/metrics`で他の任意のソースからトレースとメトリクスを受け付けます(protobuf取り込みには`pip install clawmetry[otel]`が必要です)。

ゼロコンフィグでローカルファーストなClawMetryダッシュボードと、あなたのチームがすでに運用しているバックエンドの両方でデータを扱えます。ロックインもなく、2つ目のエージェントをインストールする必要もありません。

## 設定

ほとんどの方は設定不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

すべてのオプション: `clawmetry --help`

## 対応チャネル

ClawMetryは、設定済みのすべてのOpenClawチャネルのライブアクティビティを表示します。あなたの`openclaw.json`で実際に設定されているチャネルのみがFlowダイアグラムに表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャネルノードをクリックすると、受信/送信メッセージ数付きのライブチャットバブルビューが表示されます。

| チャネル | ステータス | ライブポップアップ | メモ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒ごとの更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db`を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web(Baileys)経由 |
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

> **自動検出:** ClawMetryはあなたの`~/.openclaw/openclaw.json`を読み取り、実際に設定されているチャネルのみを表示します。手動設定は不要です。

## Dockerデプロイ

ClawMetryをコンテナ内で実行したいですか?問題ありません🐳

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

> **注意:** Docker内で実行する場合、ClawMetryがあなたのセットアップを自動検出できるよう、エージェントのデータ + ログディレクトリ(例: `~/.openclaw`、`~/.claude`、`~/.codex`)をマウントしてください。

## 必要要件

- Python 3.8以上
- Flask(pip経由で自動インストール)
- 同じマシン上で稼働するAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity(Dockerの場合はマウントされたボリューム)
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは[NemoClaw](https://github.com/NVIDIA/NemoClaw)(サンドボックス化されたOpenShellコンテナ内でエージェントを実行する、OpenClaw向けNVIDIAのエンタープライズセキュリティラッパー)を自動検出します。

ほとんどの場合、追加設定は不要です。同期デーモンは、セッションファイルがホスト上の`~/.openclaw/`にあるか、OpenShellコンテナ内にあるかにかかわらず自動的に検出します。

### 仕組み

ClawMetryは次の2通りの方法でNemoClawを検出します:

1. **バイナリ検出** — `nemoclaw` CLIの有無を確認し、`nemoclaw status`を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを`openshell`、`nemoclaw`、`ghcr.io/nvidia/`イメージについてスキャンし、ボリュームマウントまたは`docker cp`経由でセッションを読み取り

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボード上で`runtime=nemoclaw`と`container_id`メタデータがタグ付けされるため、標準的なOpenClawセッションと一目で区別できます。

### 推奨セットアップ: 同期デーモンをHOSTで実行

最良の体験のために、ClawMetryの同期デーモンは(サンドボックス内ではなく)**ホストマシン**上で実行してください。これにより、NemoClawのネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中の任意のOpenShellコンテナ内のセッションを自動的に検出します。

### オプション: サンドボックス名の明示指定

自動検出がうまく機能しない場合は、正しいサンドボックスをClawMetryに指定してください:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内で実行する場合(上級者向け)

同期デーモンをOpenShellサンドボックス**内**で実行する必要がある場合は、ClawMetry ingest APIに到達できるよう、NemoClawのネットワークポリシーに以下のegressルールを追加してください:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

適用するには:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### ポートとエンドポイント

| エンドポイント | ポート | プロトコル | 必須 |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | はい(同期デーモン → クラウド) |
| `localhost:8900` | 8900 | HTTP | はい(ローカルダッシュボードUI) |
| Dockerソケット(`/var/run/docker.sock`) | — | Unixソケット | コンテナのセッション検出用 |

同期デーモンは`ingest.clawmetry.com`への送信HTTPS呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetryは`https://app.clawmetry.com/api/install`へ匿名のインストールライフサイクルpingを送信します。新しいマシンで初めて`clawmetry` CLIを実行した際の`install` ping、新バージョンへアップグレード後の初回実行時の`update` ping、ダッシュボード内オンボーディングの選択を完了した際の`onboarded` pingの3種類です。これは実際のインストール数をカウントするため(生のPyPIダウンロード数は約98%がミラー、CI、自動更新の再ダウンロードです)、また実際にどのエージェントフレームワークとバージョンが使われているかを把握するために使用しています。

**ライフサイクルイベント・バージョンごとに最大1回のPOST**で、以下を含みます:

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`に保存されるランダムUUID | 重複排除。Cloud syncを明示的に接続するまでは匿名(その後、認証済みデーモンのハートビートがこれを運び、このインストールをあなたのアカウントに紐付けます) |
| `event` | `install` / `update` / `onboarded` | 新規インストールか既存のアップグレードか |
| `version` | `0.12.167` | 実際に使われているバージョン |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位 |
| `python` | `3.11.15` | Pythonバージョンのサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次に統合すべきエージェント |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの区別 |

**送信しないもの**: IP(クラウド側でリクエストからサーバーサイドで国コードを導出した後、IPは破棄されます)、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤーペイロードは[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で監査可能です。

**オプトアウト**(以下のいずれか1つで永続的に無効化できます):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
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
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
