<!-- i18n-src:9a05336fbdc1 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**あなたのエージェントの思考を見る。** **14種類のAIエージェントランタイム**をリアルタイムに観測: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、他10種。エージェントフリート全体を1つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [その他 →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClaw向けの観測ツールとして始まりましたが、現在は**エージェントフリート全体**を1つのダッシュボードで計測し、マシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClawとNemoClawはオープンソース版アプリで無料です。その他のランタイムはClawMetry Cloud、またはセルフホストのProライセンスで有効になります。ヘッダーからランタイムを切り替えると、コスト、トークン、ツール、トレースなど全タブがそのランタイムにスコープし直されます。無料/有料の正確な区分、ティア表、`/api/entitlement` の形式、`clawmetry license` CLIについては **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** をご覧ください。

## できること

- **Flow** — チャンネル、ブレイン、ツール間をメッセージが流れる様子を示すライブアニメーション図
- **Overview** — ヘルスチェック、アクティビティヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コストトラッキング
- **Sessions** — モデル、トークン、最終活動時刻を含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行時刻、所要時間を含むスケジュールジョブ
- **Logs** — 色分けされたリアルタイムログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、メールへのルーティング
- **Approvals** — 破壊的な削除、force push、DB変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリック承認の背後でゲート

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

### 🔐 Security — ポスチャーと監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / メールへのWebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツール呼び出しを手動承認の背後でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code向けの実行前ブロッキング** — 1つのコマンドで、一致するツール呼び出しを実行*前*に一時停止し、あなたの判断を待つPreToolUseフックがインストールされます([クラウドプッシュ通知](https://app.clawmetry.com/push)を有効にすればスマートフォンからワンタップで対応可能):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

拒否した場合はそのツール呼び出し1件のみがブロックされます。エージェントはセッションを維持したまま別のアプローチを試せます。スマートフォンでの承認はClaude Code自身の権限プロンプトをスキップします(すでに回答済みのため)。一致しないツールは約40msのコストで、Claude Codeの通常の権限フローにフォールスルーします。また、Claude Code自身があなたの判断を待っている場合(`permission_prompt` / `idle_prompt` 通知)にもスマートフォンにプッシュ通知が届きます。

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

v2 Reactアプリは `frontend/` にあり、Flaskサーバーがv2有効の状態で起動されると `/v2` で配信されます。

開発時はターミナルを2つ使用します。

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

`http://localhost:5173/v2/` を開きます。Viteが `/api` リクエストを `http://localhost:8900` にプロキシするため、Reactアプリは追加のCORS設定なしにローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番ビルドは `clawmetry/static/v2/dist/` に書き出されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多数のAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムは、そのネイティブなセッション形式をClawMetryの統一フォーマットに変換する専用のリーダーアダプターを備えています。デーモンはそれらをランタイムのタグ付きで同じDuckDBストア+クラウドスナップショットに取り込み、複数のランタイムが存在する場合はSession replayタブに**ランタイムスイッチャー**が表示されます。完全な対応表とランタイム追加ガイドは [`docs/compatibility.md`](docs/compatibility.md) を、OpenClawファミリーの入門は [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) をご覧ください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプター | フラットな `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | ベータアダプター | セッションごとのSQLite(`data/v2-sessions`)。トランスクリプト+メッセージ数。 |
| **Hermes** | ベータアダプター | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプター | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出し+思考過程、トークン使用量。 |
| **Codex** | ベータアダプター | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | ベータアダプター | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプター | プロジェクトごとの `.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプター | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |
| **opencode** | ベータアダプター | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **Qwen Code** | ベータアダプター | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Pi** | ベータアダプター | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **Deep Agents** | ベータアダプター | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **n8n** | ベータアダプター | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録するモデル+トークン。 |

「ベータアダプター」とは、ClawMetryがそのランタイムの実際のディスク上フォーマット向けのリーダーを提供していることを意味し、それぞれ実機での実際のインストールに対して構築・検証されています(`tests/fixtures/runtimes/<rt>/` を参照)。アダプターは読み取り専用であり、それぞれが自らのランタイムが実際にディスクに保存する内容について正直です(例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません)。複数のランタイムが1つのノード上で実行されている場合、ランタイムスイッチャーはセッションビューを1つに絞り込み、クリーンに深掘りできます。

## 任意のSDKエージェントをトラッキング — ループ外のコスト帰属

上記のランタイムはすべてセッションをディスクに書き込みます。あなた自身が構築した**本番エージェント** — OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の `httpx` ループで作ったもの — はそうではありません。ClawMetryのゼロ設定インターセプターは、`httpx`/`requests` をモンキーパッチすることで、そのLLM呼び出し(コスト、トークン、レイテンシ、エラー)をそれでも捕捉します。

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()`(または `CLAWMETRY_SOURCE=support-agent` 環境変数)は各呼び出しに**名前付きソース**でタグ付けするため、実行するすべてのプロダクトがダッシュボードのOverviewにある**🔌 Out-loop sources**カードに、それぞれ独立したコスト帰属可能な行として表示されます。呼び出し数、プロバイダー、レイテンシ、エージェントごとのエラー率です。ソースが設定されていない場合でも呼び出しは引き続きトラッキングされますが、そのカードは非表示のままです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプターが供給しているのと同じデータ層(DuckDB → クラウドスナップショット)なので、Out-loopソースも他のすべてと同様にE2E暗号化された状態でクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラルに、あなたのトレースをどこへでも

ClawMetryは**GenAIセマンティック規約**を用いて双方向で**OpenTelemetry**を話すため、あなたのエージェントトレースが特定のツールにロックインされることはありません。

各セッション(LLM呼び出し、ツール、サブエージェント、トークン、コスト)を、任意のコレクター(Datadog、Grafana、Honeycomb、または独自のOTel Collector)へOTLP/HTTPのGenAIスパンとして**エクスポート**します。

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

**取り込み** — 組み込みのOTLPレシーバーは、`/v1/traces` と `/v1/metrics` で他のあらゆるソースからのトレースとメトリクスを受け付けます(protobuf取り込みには `pip install clawmetry[otel]`)。

ゼロ設定・ローカルファーストのClawMetryダッシュボード**と**、チームがすでに運用しているバックエンドへのデータ送信の両方を、ロックインなし・2つ目のエージェント不要で手に入れられます。

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

## サポートされているチャンネル

ClawMetryは、設定済みのすべてのOpenClawチャンネルについてライブアクティビティを表示します。`openclaw.json` で実際に設定されているチャンネルのみがFlow図に表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャンネルノードをクリックすると、送受信メッセージ数付きのライブチャットバブルビューが表示されます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db` を直接読み取り |
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

> **自動検出:** ClawMetryはあなたの `~/.openclaw/openclaw.json` を読み取り、実際に設定されているチャンネルのみを描画します。手動設定は不要です。

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

> **注意:** Dockerで実行する場合、ClawMetryがセットアップを自動検出できるよう、エージェントのデータ+ログディレクトリ(例: `~/.openclaw`、`~/.claude`、`~/.codex`)をマウントしてください。

## 必要要件

- Python 3.8以上
- Flask(pip経由で自動インストール)
- 同一マシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8nのいずれか(Dockerの場合はマウントされたボリューム)
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは、サンドボックス化されたOpenShellコンテナ内でエージェントを実行するNVIDIAのOpenClaw向けエンタープライズセキュリティラッパーである[NemoClaw](https://github.com/NVIDIA/NemoClaw)を自動検出します。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の `~/.openclaw/` にあるか、OpenShellコンテナ内にあるかに関わらず自動的に検出します。

### 仕組み

ClawMetryは2つの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの存在を確認し、`nemoclaw status` を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを `openshell`、`nemoclaw`、または `ghcr.io/nvidia/` イメージについてスキャンし、ボリュームマウントまたは `docker cp` 経由でセッションを読み取り

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボード上で `runtime=nemoclaw` と `container_id` メタデータがタグ付けされるため、標準のOpenClawセッションと一目で区別できます。

### 推奨セットアップ: 同期デーモンをホスト上で実行

最良の体験のためには、ClawMetryの同期デーモンを(サンドボックス内ではなく)**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中の任意のOpenShellコンテナ内のセッションを自動的に検出します。

### オプション: サンドボックス名を明示的に指定

自動検出が機能しない場合は、ClawMetryに正しいサンドボックスを指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内で実行する場合(上級者向け)

同期デーモンをOpenShellサンドボックス**内**で実行する必要がある場合は、NemoClawのネットワークポリシーに以下のegressルールを追加し、ClawMetryのingest APIに到達できるようにしてください。

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
| `ingest.clawmetry.com` | 443 | HTTPS | 必須(同期デーモン → クラウド) |
| `localhost:8900` | 8900 | HTTP | 必須(ローカルダッシュボードUI) |
| Dockerソケット(`/var/run/docker.sock`) | — | Unixソケット | コンテナセッション検出用 |

同期デーモンは `ingest.clawmetry.com` へのアウトバウンドHTTPS呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**をご覧ください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリー

ClawMetryは、新しいマシンで初めて `clawmetry` CLIを実行した際に、匿名の「初回実行」pingを1回だけ `https://app.clawmetry.com/api/install` に送信します。これは、インストール数をカウントするため(OSSプロジェクトとして私たちが持つ唯一のマーケティング指標です)、そしてユーザーがどのエージェントフレームワークをインストールしているかを把握するために使用します。

**インストールごとに正確に1回のPOST**で、以下を含みます。

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` に保存されるランダムなUUID | 重複排除用。メールやapi_keyとは紐付けられない |
| `version` | `0.12.167` | どのバージョンが実際に使われているか |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位付け |
| `python` | `3.11.15` | Pythonバージョンのサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと連携すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの分離 |

**送信しないもの**: IPアドレス(クラウド側はサーバー上でリクエストから国コードのみを導出し、その後IPは破棄します)、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤー上のペイロードは [`clawmetry/telemetry.py`](clawmetry/telemetry.py) で監査可能です。

**オプトアウト**(以下のいずれか1つで永続的に無効化されます):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ネットワーク障害が発生しても `clawmetry` の実行がブロックされることはありません。このpingは3秒のタイムアウトを持つデーモンスレッド上でfire-and-forgetです。

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
