<!-- i18n-src:0e34918f8f2e -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考が見える。** **14種類のAIエージェントランタイム**にリアルタイムで対応した可観測性ツールです: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類。エージェントフリート全体を1つのダッシュボードで確認できます。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [他の言語 →](docs/i18n/)

コマンド1つ、設定不要。すべて自動検出します。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClawの可観測性ツールとして始まり、現在では**エージェントフリート全体**を1つのダッシュボードで計測し、お使いのマシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClawとNemoClawはオープンソースアプリで無料です。その他のランタイムはClawMetry Cloudまたはセルフホスト型のProライセンスで利用可能になります。ヘッダーからランタイムを切り替えると、コスト、トークン、ツール、トレースなど各タブがそのランタイムのスコープに再表示されます。正確な無料/有料の区分、ティア表、`/api/entitlement`の形式、`clawmetry license` CLIについては**[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**を参照してください。

## 提供機能

- **Flow** — チャンネル、ブレイン、ツールを通過するメッセージの流れをリアルタイムでアニメーション表示
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コストトラッキング
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行、実行時間を含むスケジュールジョブ
- **Logs** — カラーコード付きのリアルタイムログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、Emailへのルーティング
- **Approvals** — 破壊的な削除、force push、DB変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリック承認の背後でゲート

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッション概要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムツールコールフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデル・セッション別コスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — セキュリティ状況と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Emailへのwebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツールコールを手動承認の背後でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Codeの実行前ブロッキング** — 1つのコマンドで、一致するツールコールを実行*前*に一時停止し、あなたの判断を待つPreToolUseフックをインストールします（[クラウドプッシュ通知](https://app.clawmetry.com/push)を有効にしていれば、スマートフォンからワンタップで対応可能）。

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒否（deny）はその1回のツールコールだけをブロックします。エージェントはセッションを維持したまま、別のアプローチを試すことができます。スマートフォンで承認するとClaude Code自体の権限プロンプトはスキップされます（すでに回答済みのため）。一致しないツールのオーバーヘッドは約40msで、Claude Codeの通常の権限フローにそのまま引き継がれます。Claude Code自体があなたの対応待ちになっている場合（`permission_prompt` / `idle_prompt` 通知）にもスマートフォンにプッシュ通知が届きます。

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

開発時はターミナルを2つ使用してください。

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

`http://localhost:5173/v2/` を開いてください。Viteが`/api`リクエストを`http://localhost:8900`にプロキシするため、Reactアプリは追加のCORS設定なしでローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番用バンドルは`clawmetry/static/v2/dist/`に書き出されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測できます。OpenClaw以外の各ランタイムには専用のリーダーアダプターが用意されており、そのランタイム固有のセッション形式をClawMetryの統一されたシェイプに変換します。デーモンはこれらをランタイムでタグ付けした上で同じDuckDBストア+クラウドスナップショットに取り込み、複数のランタイムが存在する場合はSession replayタブに**ランタイムスイッチャー**が表示されます。完全なマトリクスとランタイム追加ガイドは[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門編は[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

[Perplexityのnumbat](https://github.com/perplexityai/numbat)エージェントセキュリティツールを使用していますか？ClawMetryはその調査結果と実施判断をそのまま取り込むことができます。詳細は[`docs/NUMBAT.md`](docs/NUMBAT.md)を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな`providers.Message` JSONL（`~/.picoclaw/workspace/sessions`）。トランスクリプト、モデル、ツールコール。 |
| **NanoClaw** | ベータアダプター | セッションごとのSQLite（`data/v2-sessions`）。トランスクリプト+メッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツールコール+思考過程、トークン使用量。 |
| **Codex** | ベータアダプター | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの`.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツールコール、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツールコール、トークン+コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Pi** | ベータアダプター | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツールコール、トークン+コスト。 |
| **Deep Agents** | ベータアダプター | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツールコール、トークン+コスト。 |
| **n8n** | ベータアダプター | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録している場合はモデル+トークン。 |
| **Antigravity** | ベータアダプター | `~/.gemini/<flavor>/brain/`配下のBrain JSONL。会話、ツールステップ、思考過程、生成ごとのGeminiトークン内訳+コスト、バックグラウンド生成の消費量。 |
| **GitHub Copilot** | ベータアダプター | Copilot CLIの`events.jsonl`（`~/.copilot/session-state/`配下）+ 呼び出しごとの使用量台帳である`session-store.db`。会話、ツールコール、モデルルーティング、キャッシュを考慮したトークン内訳、ベンダー請求のAIクレジットコスト。 |

「ベータアダプター」とは、ClawMetryがそのランタイムの実際のディスク上フォーマット用リーダーを提供していることを意味し、それぞれ実機での実際のインストールに対して構築・検証済みです（`tests/fixtures/runtimes/<rt>/`を参照）。アダプターは読み取り専用であり、それぞれが自身のランタイムが実際に保存しているデータについて正直です（例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません）。1つのノードで複数のランタイムが動作している場合、ランタイムスイッチャーによりセッションビューを1つに絞り込んで、クリーンに深掘りできます。

## 任意のSDKエージェントをトラッキング — ループ外のコスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。しかし、あなた自身が構築した**本番エージェント**（OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の`httpx`ループの上に構築したもの）はそうではありません。ClawMetryのゼロコンフィグ・インターセプターは、`httpx`/`requests`をモンキーパッチすることで、そうしたエージェントのLLM呼び出し（コスト、トークン、レイテンシ、エラー）もそのまま取得します。

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`（または`CLAWMETRY_SOURCE=support-agent`環境変数）は各呼び出しに**名前付きソース**としてタグを付けるため、あなたが運用する各プロダクトは、ダッシュボードのOverviewにある**🔌 Out-loop sources**カードにおいて、それぞれ独立したコスト帰属可能な項目として表示されます。エージェントごとの呼び出し数、プロバイダー、レイテンシ、エラー率が確認できます。ソースが設定されていない場合でも呼び出しは引き続きトラッキングされますが、このカードは非表示のままになります。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターが供給するのと同じデータレイヤー（DuckDB → クラウドスナップショット）であるため、Out-loopソースも他のすべてのデータと同様にE2E暗号化された状態でクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラルに、トレースをどこへでも送信

ClawMetryは**GenAIセマンティックコンベンション**を用いて、双方向で**OpenTelemetry**を話します。そのため、あなたのエージェントトレースが特定のツールにロックインされることはありません。

**エクスポート** — 各セッション（LLM呼び出し、ツール、サブエージェント、トークン、コスト）を、任意のコレクター（Datadog、Grafana、Honeycomb、あるいは独自のOTel Collector）にOTLP/HTTP GenAIスパンとして出力できます。

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔は任意の環境変数です。

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**インジェスト** — 組み込みのOTLPレシーバーは、`/v1/traces`および`/v1/metrics`で他のあらゆるソースからのトレースとメトリクスを受け付けます（protobuf取り込みには`pip install clawmetry[otel]`が必要です）。

ゼロコンフィグでローカルファーストなClawMetryダッシュボードと、あなたのチームがすでに運用しているバックエンドの両方でデータを扱えます。ロックインもなく、2つ目のエージェントをインストールする必要もありません。

## 設定

ほとんどのユーザーは設定不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合は以下のとおりです。

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

すべてのオプション: `clawmetry --help`

## 対応チャンネル

ClawMetryは、設定済みのすべてのOpenClawチャンネルについてライブアクティビティを表示します。`openclaw.json`で実際に設定されているチャンネルのみがFlow図に表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャンネルノードをクリックすると、受信/送信メッセージ数付きのライブチャットバブルビューが表示されます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db`を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web（Baileys）経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド+チャンネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース+チャンネル検出 |
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

> **自動検出:** ClawMetryは`~/.openclaw/openclaw.json`を読み取り、実際に設定されているチャンネルのみを表示します。手動設定は不要です。

## Dockerデプロイ

コンテナでClawMetryを実行したいですか？問題ありません 🐳

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

> **注:** Dockerで実行する場合は、ClawMetryが自動的にセットアップを検出できるよう、エージェントのデータ+ログディレクトリ（例: `~/.openclaw`、`~/.claude`、`~/.codex`）をマウントしてください。

## 動作要件

- Python 3.8以上
- Flask（pip経由で自動インストール）
- 同一マシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity、GitHub Copilotのいずれか（Dockerの場合はマウントされたボリューム）
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは[NemoClaw](https://github.com/NVIDIA/NemoClaw)（サンドボックス化されたOpenShellコンテナ内でエージェントを実行する、OpenClaw向けNVIDIAのエンタープライズセキュリティラッパー）を自動的に検出します。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の`~/.openclaw/`にあるか、OpenShellコンテナ内にあるかに関わらず自動検出します。

### 動作の仕組み

ClawMetryは2つの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの有無を確認し、`nemoclaw status`を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを`openshell`、`nemoclaw`、`ghcr.io/nvidia/`イメージについてスキャンし、ボリュームマウントまたは`docker cp`経由でセッションを読み取り

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボード上で`runtime=nemoclaw`と`container_id`メタデータがタグ付けされるため、標準的なOpenClawセッションと一目で区別できます。

### 推奨セットアップ: ホスト側での同期デーモン

最良の体験のためには、ClawMetryの同期デーモンを（サンドボックスの内側ではなく）**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中のあらゆるOpenShellコンテナ内のセッションを自動的に検出します。

### 任意設定: 明示的なサンドボックス名

自動検出がうまく機能しない場合は、正しいサンドボックスをClawMetryに指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行（上級者向け）

同期デーモンをOpenShellサンドボックスの**内側**で実行する必要がある場合は、ClawMetryのingest APIに到達できるよう、NemoClawのネットワークポリシーに以下のegressルールを追加してください。

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

以下で適用します。

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

## テレメトリ

ClawMetryは`https://app.clawmetry.com/api/install`に匿名のインストールライフサイクル通知を送信します。新しいマシンで`clawmetry` CLIを初めて実行した際に1回の`install`通知、新バージョンへのアップグレード後の初回実行時に1回の`update`通知、ダッシュボード内オンボーディングの選択を完了した際に1回の`onboarded`通知です。これは、実際のインストール数をカウントするため（生のPyPIダウンロード数は約98%がミラー、CI、自動更新の再ダウンロードです）、また実際に使われているエージェントフレームワークとバージョンを把握するために使用されます。

**ライフサイクルイベント・バージョンごとに最大1回のPOST**で、以下を含みます。

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`に保存されるランダムUUID | 重複排除。Cloud syncを明示的に接続するまでは匿名（その後は認証済みデーモンのハートビートがこれを運び、このインストールをあなたのアカウントに紐付けます） |
| `event` | `install` / `update` / `onboarded` | 新規インストールか既存インストールのアップグレードか |
| `version` | `0.12.167` | 実際に使われているバージョン |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位 |
| `python` | `3.11.15` | Pythonバージョンのサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと連携すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズを区別 |

**送信しないもの**: IP（クラウド側でリクエストからサーバーサイドで国コードを導出した後、IPは破棄されます）、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤーペイロードは[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で監査可能です。

**オプトアウト**（以下のいずれか1つで恒久的に無効化されます）:

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ネットワーク障害が発生しても`clawmetry`の実行がブロックされることはありません。この通知はデーモンスレッド上でfire-and-forget方式、タイムアウト3秒で送信されます。

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
