<!-- i18n-src:c422fb7dd0da -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を見える化。** **20種類のAIエージェントランタイム**に対応したリアルタイム可観測性: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他16種類。エージェント群全体を1つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [さらに見る →](docs/i18n/)

コマンド一つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20種類のエージェントランタイムに対応

ClawMetryはOpenClaw向けの可観測性ツールとして始まり、今では**エージェント群全体**を1つのダッシュボードで計測し、マシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClawとNemoClawはオープンソース版アプリで無料利用でき、その他のランタイムはClawMetry Cloudまたはセルフホスト版のProライセンスで利用可能になります。ヘッダーからランタイムを切り替えると、コスト・トークン・ツール・トレースなど各タブがそのランタイムの範囲に再スコープされます。正確な無料/有料の区分、ティア比較表、`/api/entitlement`の形式、`clawmetry license` CLIについては**[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**を参照してください。

## 提供される機能

- **Flow** — チャンネル、ブレイン、ツールを流れるメッセージをリアルタイムのアニメーション図で表示
- **Overview** — ヘルスチェック、アクティビティのヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コスト追跡
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行、実行時間を含むスケジュールジョブ
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

### 🔐 Security — セキュリティ体制と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Emailへのwebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツールコールを手動承認の背後でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Codeの実行前ブロッキング** — 1つのコマンドで、該当するツールコールを実行*前*に一時停止し、あなたの判断を待つPreToolUseフックがインストールされます([クラウドのプッシュ通知](https://app.clawmetry.com/push)を有効にすればスマートフォンからワンタップで対応可能):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒否(deny)はその1つのツールコールのみをブロックします。エージェントはセッションを維持したまま別のアプローチを試すことができます。スマートフォンでの承認はClaude Code自体の権限プロンプトをスキップします(すでに回答済みのため)。マッチしないツールは約40msのコストで、Claude Codeの通常の権限フローにフォールスルーします。Claude Code自体があなたの応答を待っている場合(`permission_prompt` / `idle_prompt`通知)にもスマートフォンにプッシュ通知が届きます。

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

v2 Reactアプリは`frontend/`にあり、v2を有効にしてFlaskサーバーを起動すると`/v2`で配信されます。

開発中はターミナルを2つ使用します。

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

`http://localhost:5173/v2/`を開きます。Viteは`/api`リクエストを`http://localhost:8900`にプロキシするため、Reactアプリは追加のCORS設定なしでローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番用バンドルは`clawmetry/static/v2/dist/`に書き出されます。

## ランタイム/エージェントの互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを可観測化します。OpenClaw以外の各ランタイムは、ネイティブのセッション形式をClawMetryの統一形式に変換する専用のリーダーアダプターを備えています。デーモンはこれらを同じDuckDBストア+クラウドスナップショットに取り込み、ランタイムでタグ付けします。Session replayタブは、複数のランタイムが存在する場合に**ランタイム切り替え機能**を表示します。完全な対応表とランタイム追加ガイドについては[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門については[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

[Perplexityのnumbat](https://github.com/perplexityai/numbat)エージェントセキュリティツールを実行していますか?ClawMetryはその検出結果と実施判定をそのまま取り込みます。詳細は[`docs/NUMBAT.md`](docs/NUMBAT.md)を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな`providers.Message`のJSONL(`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツールコール。 |
| **NanoClaw** | ベータアダプター | セッションごとのSQLite(`data/v2-sessions`)。トランスクリプト+メッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツールコール+thinking、トークン使用量。 |
| **Codex** | ベータアダプター | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの`.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツールコール、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツールコール、トークン+コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツールコール、トークン使用量。 |
| **Pi** | ベータアダプター | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツールコール、トークン+コスト。 |
| **Deep Agents** | ベータアダプター | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツールコール、トークン+コスト。 |
| **n8n** | ベータアダプター | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録している場合のモデル+トークン。 |
| **Antigravity** | ベータアダプター | `~/.gemini/<flavor>/brain/`配下のBrain JSONL。会話、ツールステップ、thinking、生成ごとのGeminiトークン分割+コスト、バックグラウンド生成の消費。 |
| **GitHub Copilot** | ベータアダプター | Copilot CLIの`events.jsonl`(`~/.copilot/session-state/`配下)+`session-store.db`(呼び出しごとの使用量台帳)。会話、ツールコール、モデルルーティング、キャッシュを考慮したトークン分割、ベンダー請求のAIクレジットコスト。 |
| **Grok** | ベータアダプター | xAI Grok Build CLI(`~/.grok/bin/grok`配下のRustバイナリ): グローバルイベントログ`~/.grok/logs/unified.jsonl`+セッションごとの`~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`。会話、ターンごとのトークン分割、モデルルーティング、および`~/.grok/upload_queue/`にステージングされるCLIの送信リポジトリペイロード(マシンから何が送信されたかを確認可能)。 |

「ベータアダプター」とは、ClawMetryがそのランタイムの実際のディスク上フォーマットに対応するリーダーを提供しており、それぞれが実マシンでの実インストールに対してビルド・検証済み(`tests/fixtures/runtimes/<rt>/`を参照)であることを意味します。アダプターは読み取り専用で、それぞれが自身のランタイムが実際に何をディスクに保存しているかについて正直です(例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません)。1つのノードで複数のランタイムが動作している場合、ランタイム切り替え機能によりセッションビューを1つに絞ってクリーンに深掘りできます。

## 任意のSDKエージェントを追跡 — アウトループ・コスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。あなた自身の**プロダクションエージェント**、つまりOpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の`httpx`ループで構築したものは、そうではありません。ClawMetryのゼロ設定インターセプターは、`httpx`/`requests`をモンキーパッチすることで、そうしたエージェントのLLM呼び出し(コスト、トークン、レイテンシ、エラー)を引き続き捕捉します。

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(または`CLAWMETRY_SOURCE=support-agent`環境変数)は各呼び出しに**名前付きソース**をタグ付けするため、実行するすべてのプロダクトがダッシュボードのOverviewにある**🔌 Out-loop sources**カードにファーストクラスかつコスト帰属可能な行として表示されます。エージェントごとの呼び出し数、プロバイダー、レイテンシ、エラー率がわかります。ソースを設定しない場合でも呼び出しは追跡され続けますが、そのカードは非表示のままになります。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターと同じデータ層(DuckDB → クラウドスナップショット)にフィードされるため、アウトループソースも他のデータと同様にE2E暗号化されてクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラル、トレースをどこへでも送信

ClawMetryは**GenAIセマンティック規約**を用いて双方向で**OpenTelemetry**を話すため、エージェントのトレースが1つのツールにロックインされることはありません。

各セッション(LLM呼び出し、ツール、サブエージェント、トークン、コスト)をOTLP/HTTPのGenAIスパンとして、任意のコレクター(Datadog、Grafana、Honeycomb、あるいは自前のOTel Collector)に**エクスポート**:

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

**取り込み** — 組み込みのOTLPレシーバーは、`/v1/traces`、`/v1/logs`、`/v1/metrics`で他の任意のソースからのトレース、ログ、メトリクスを受け付けます。OpenTelemetryで計装された任意のアプリをここに向けてください。

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSONのトレースとログは、素の`pip install clawmetry`だけで動作し、追加パッケージは不要です。Protobuf取り込み(およびOTLP/JSONメトリクス)には`pip install clawmetry[otel]`が必要です。独自の`service.name`を設定したアプリは、ランタイム切り替え機能上で独自のエージェントとして、そのコストとトークンとともに表示されます。

ゼロ設定・ローカルファーストなClawMetryダッシュボードと、チームがすでに運用しているどんなバックエンドにもデータを送れる自由の両方が手に入ります。ロックインなし、第二のエージェントのインストールも不要です。

## 設定

ほとんどの人には設定は不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

すべてのオプション: `clawmetry --help`

## 対応チャンネル

ClawMetryは設定済みのすべてのOpenClawチャンネルについてライブアクティビティを表示します。`openclaw.json`で実際に設定されているチャンネルのみがFlowダイアグラムに表示され、未設定のチャンネルは自動的に非表示になります。

Flow内の任意のチャンネルノードをクリックすると、受信/送信メッセージ数とともにライブのチャットバブルビューが表示されます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db`を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web(Baileys)経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド+チャンネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース+チャンネル検出 |
| 🌐 **Webchat** | ✅ フル対応 | ✅ | 組み込みWeb UIセッション |
| 📡 **IRC** | ✅ フル対応 | ✅ | ターミナル風バブルUI |
| 🍏 **BlueBubbles** | ✅ フル対応 | ✅ | BlueBubbles REST API経由のiMessage |
| 🔵 **Google Chat** | ✅ フル対応 | ✅ | Chat API Webhook経由 |
| 🟣 **MS Teams** | ✅ フル対応 | ✅ | Teamsボットプラグイン経由 |
| 🔷 **Mattermost** | ✅ フル対応 | ✅ | セルフホスト型チームチャット |
| 🟩 **Matrix** | ✅ フル対応 | ✅ | 分散型、E2EE対応 |
| 🟢 **LINE** | ✅ フル対応 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ フル対応 | ✅ | 分散型NIP-04 DM |
| 🟣 **Twitch** | ✅ フル対応 | ✅ | IRC接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ フル対応 | ✅ | WebSocketイベントサブスクリプション |
| 🔵 **Zalo** | ✅ フル対応 | ✅ | Zalo Bot API |

> **自動検出:** ClawMetryは`~/.openclaw/openclaw.json`を読み取り、実際に設定されているチャンネルのみをレンダリングします。手動設定は不要です。

## Dockerデプロイ

コンテナでClawMetryを実行したいですか?問題ありません 🐳

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

> **注意:** Dockerで実行する場合、ClawMetryがセットアップを自動検出できるように、エージェントのデータディレクトリとログディレクトリ(例: `~/.openclaw`、`~/.claude`、`~/.codex`)をマウントしてください。

## 動作要件

- Python 3.8以上
- Flask(pip経由で自動インストール)
- 同一マシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity、GitHub Copilot、Grok、またはQM(Dockerの場合はマウントされたボリュームでも可)
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは[NemoClaw](https://github.com/NVIDIA/NemoClaw)(サンドボックス化されたOpenShellコンテナ内でエージェントを実行する、NVIDIAのエンタープライズ向けOpenClawセキュリティラッパー)を自動的に検出します。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の`~/.openclaw/`にあるか、OpenShellコンテナ内にあるかに関わらず自動的に検出します。

### 動作の仕組み

ClawMetryは2つの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの有無を確認し、`nemoclaw status`を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを`openshell`、`nemoclaw`、`ghcr.io/nvidia/`イメージについてスキャンし、ボリュームマウントまたは`docker cp`経由でセッションを読み取り

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボード上で`runtime=nemoclaw`と`container_id`メタデータがタグ付けされるため、標準的なOpenClawセッションとひと目で区別できます。

### 推奨セットアップ: ホスト上での同期デーモン実行

最良の体験のためには、ClawMetryの同期デーモンをサンドボックスの内部ではなく**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中のOpenShellコンテナ内のセッションを自動的に検出します。

### オプション: サンドボックス名の明示指定

自動検出が機能しない場合は、ClawMetryに正しいサンドボックスを指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行(上級者向け)

同期デーモンをOpenShellサンドボックスの**内部**で実行する必要がある場合は、ClawMetryのingest APIに到達できるように、NemoClawネットワークポリシーに以下のegressルールを追加してください。

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
| `ingest.clawmetry.com` | 443 | HTTPS | 必須(同期デーモン → クラウド) |
| `localhost:8900` | 8900 | HTTP | 必須(ローカルダッシュボードUI) |
| Dockerソケット(`/var/run/docker.sock`) | — | Unixソケット | コンテナのセッション検出用 |

同期デーモンは`ingest.clawmetry.com`への送信HTTPS呼び出しのみを行います。受信ポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリー

ClawMetryは、新しいマシンで初めて`clawmetry` CLIを実行した際の`install`ピング1回、新バージョンへのアップグレード後の初回実行時の`update`ピング1回、ダッシュボード内オンボーディングの選択を完了した際の`onboarded`ピング1回という、匿名のインストールライフサイクルのpingを`https://app.clawmetry.com/api/install`に送信します。これは実際のインストール数をカウントするため(生のPyPIダウンロード数の約98%はミラー、CI、自動更新の再ダウンロードです)、そしてどのエージェントフレームワークとバージョンが実際に使われているかを把握するために使用しています。

**ライフサイクルイベント・バージョンごとに最大1回のPOST**で、以下を含みます。

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`に保存されるランダムUUID | 重複排除。Cloud syncを明示的に接続するまでは匿名(接続後は認証済みのデーモンハートビートがこれを運び、このインストールをあなたのアカウントに紐付けます) |
| `event` | `install` / `update` / `onboarded` | 新規インストールか既存のアップグレードか |
| `version` | `0.12.167` | どのバージョンが実際に使われているか |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォーム対応の優先順位 |
| `python` | `3.11.15` | Pythonバージョン対応マトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと連携すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIのノイズを区別 |

**送信しない情報**: IP(クラウドはリクエストからサーバー側で国コードを導出した後、IPを破棄します)、ホスト名、ユーザー名、ワークスペースのパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤー上のペイロードは[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で監査可能です。

**オプトアウト**(以下のいずれか1つで永久に無効化されます):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ネットワーク障害がこれによって`clawmetry`の実行をブロックすることはありません。このpingはデーモンスレッド上でfire-and-forgetかつタイムアウト3秒です。

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
  <strong>🦞 エージェントの思考を見える化</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
