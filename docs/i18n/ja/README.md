<!-- i18n-src:02b789586c7d -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**あなたのエージェントの思考を見る。** **14種類のAIエージェントランタイム**にわたるリアルタイムの可観測性: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類以上。エージェント群全体を1つのダッシュボードで。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [もっと見る →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それだけで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClawの可観測性ツールとして始まりましたが、現在ではマシン上の各ランタイムを自動検出し、1つのダッシュボードで**エージェント群全体**を計測します:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClawとNemoClawはオープンソースアプリで無料です。その他のランタイムはClawMetry Cloud、またはセルフホストのProライセンスで有効になります。ヘッダーからランタイムを切り替えると、コスト、トークン、ツール、トレースなどすべてのタブがそのランタイムに絞り込まれます。正確な無料/有料の区分、ティア表、`/api/entitlement` の形式、`clawmetry license` CLIについては **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** を参照してください。

## できること

- **Flow** — チャンネル、ブレイン、ツール間を流れるメッセージをライブでアニメーション表示する図
- **Overview** — ヘルスチェック、アクティビティのヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次の内訳付きトークン・コスト追跡
- **Sessions** — モデル、トークン、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行時刻、実行時間付きのスケジュールジョブ
- **Logs** — 色分けされたリアルタイムログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートの閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、Emailへルーティング
- **Approvals** — 破壊的な削除、force push、DB変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリックの承認でゲート

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッション概要
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムツール呼び出しフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデル・セッション別のコスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — セキュリティ姿勢と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Email へのWebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツール呼び出しを手動承認でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code向けの実行前ブロッキング** — コマンド1つで、一致するツール呼び出しを実行*前*に一時停止し、あなたの判断を待つPreToolUseフックをインストールします（[クラウドプッシュ通知](https://app.clawmetry.com/push)を有効にすればスマートフォンからワンタップで対応可能）:

```bash
clawmetry hooks install     # ~/.claude/settings.json に書き込み(冪等)
clawmetry hooks status      # どのフックが組み込まれているか、有効なポリシー数
clawmetry hooks uninstall   # ClawMetryのエントリのみを削除
```

拒否はそのツール呼び出し1件のみをブロックします。エージェントはセッションを維持したまま別のアプローチを試せます。スマートフォンでの承認はClaude Code自体の権限プロンプトをスキップします(すでに回答済みのため)。一致しないツールは約40msのコストで、Claude Codeの通常の権限フローにそのままフォールスルーします。Claude Code自体があなたの対応待ちのときも(`permission_prompt` / `idle_prompt` 通知)、スマートフォンにプッシュ通知が届きます。

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

## v2 フロントエンド開発

v2のReactアプリは `frontend/` にあり、Flaskサーバーがv2有効の状態で起動されると `/v2` で配信されます。

開発中はターミナルを2つ使用してください:

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

`http://localhost:5173/v2/` を開いてください。Viteが `/api` へのリクエストを `http://localhost:8900` にプロキシするため、Reactアプリは追加のCORS設定なしでローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するバンドルをビルドするには:

```bash
cd frontend
npm run build
```

本番用バンドルは `clawmetry/static/v2/dist/` に書き出されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムには専用のリーダーアダプタが同梱されており、それぞれのネイティブなセッション形式をClawMetryの統一シェイプに変換します。デーモンはそれらをランタイムでタグ付けした上で同じDuckDBストア + クラウドスナップショットに取り込み、複数のランタイムが存在する場合はSession replayタブに**ランタイム切り替え**が表示されます。完全な対応表とランタイム追加ガイドは[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門は[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | ベータアダプタ | フラットな `providers.Message` JSONL(`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | ベータアダプタ | セッションごとのSQLite(`data/v2-sessions`)。トランスクリプト + メッセージ数。 |
| **Hermes** | ベータアダプタ | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | ベータアダプタ | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出し + 思考、トークン使用量。 |
| **Codex** | ベータアダプタ | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | ベータアダプタ | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | ベータアダプタ | プロジェクトごとの `.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | ベータアダプタ | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |
| **opencode** | ベータアダプタ | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **Qwen Code** | ベータアダプタ | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Pi** | ベータアダプタ | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **Deep Agents** | ベータアダプタ | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツール呼び出し、トークン + コスト。 |
| **n8n** | ベータアダプタ | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録している場合はモデル + トークン。 |
| **Antigravity** | ベータアダプタ | `~/.gemini/<flavor>/brain/` 配下のBrain JSONL。会話、ツールステップ、思考、生成ごとのGemini トークン内訳 + コスト、バックグラウンド生成のバーン。 |

「ベータアダプタ」とは、ClawMetryがそのランタイムの実際のディスク上フォーマット向けのリーダーを同梱していることを意味し、それぞれが実マシン上の実インストールに対して構築・検証されています(`tests/fixtures/runtimes/<rt>/` を参照)。アダプタは読み取り専用で、それぞれがそのランタイムが実際にディスクに保存している内容について正直です(例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません)。1つのノード上で複数のランタイムが動作している場合、ランタイム切り替えでセッションビューを1つに絞り込み、クリーンな深掘りができます。

## あらゆるSDKエージェントの追跡 — アウトループのコスト帰属

上記のランタイムはいずれもセッションをディスクに書き込みます。あなた自身が構築した**本番エージェント** — OpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の `httpx` ループの上に構築したもの — は書き込みません。ClawMetryの設定不要なインターセプタは、`httpx`/`requests` をモンキーパッチすることで、そうしたエージェントのLLM呼び出し(コスト、トークン、レイテンシ、エラー)もそのまま捕捉します:

```python
import clawmetry.track            # インターセプタを有効化
clawmetry.track.set_source("support-agent")   # このプロダクトに名前を付ける

# ...エージェントは通常どおり実行され、すべてのLLM呼び出しが追跡・帰属されます。
```

`set_source()`(または `CLAWMETRY_SOURCE=support-agent` 環境変数)は各呼び出しに**名前付きソース**をタグ付けするため、実行しているプロダクトそれぞれが、Overviewの**🔌 アウトループソース**カードに、コスト帰属可能な独立した行として表示されます — エージェントごとの呼び出し数、プロバイダ、レイテンシ、エラー率。ソースを設定していない場合でも呼び出しは追跡されますが、カードは表示されないままです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプタが供給しているのと同じデータ層(DuckDB → クラウドスナップショット)なので、アウトループソースも他のすべてと同様にE2E暗号化されてクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラル、トレースをどこへでも送信

ClawMetryは双方向で**OpenTelemetry**を話し、**GenAIセマンティック規約**を使用するため、あなたのエージェントトレースが特定のツールにロックインされることはありません。

各セッション — LLM呼び出し、ツール、サブエージェント、トークン、コスト — をOTLP/HTTPのGenAIスパンとして、任意のコレクタ(Datadog、Grafana、Honeycomb、または独自のOTel Collector)に**エクスポート**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 同等の指定方法:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔は任意の環境変数です:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 追加のHTTPヘッダー
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒(デフォルト60)
```

**インジェスト** — 組み込みのOTLPレシーバーは、`/v1/traces` と `/v1/metrics` で他の任意のソースからのトレースとメトリクスを受け付けます(protobufインジェストには `pip install clawmetry[otel]` が必要)。

設定不要でローカルファーストなClawMetryダッシュボードと、あなたのチームがすでに運用しているバックエンドへのデータの両方が手に入ります — ロックインなし、2つ目のエージェントのインストールも不要です。

## 設定

ほとんどの人には設定は不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合:

```bash
clawmetry --port 9000              # カスタムポート(デフォルト: 8900)
clawmetry --host 127.0.0.1         # localhostのみにバインド
clawmetry --workspace ~/mybot      # カスタムワークスペースパス
clawmetry --name "Alice"           # Flow可視化に表示されるあなたの名前
```

すべてのオプション: `clawmetry --help`

## 対応チャンネル

ClawMetryは設定済みのすべてのOpenClawチャンネルについてライブアクティビティを表示します。`openclaw.json` で実際に設定されているチャンネルのみがFlow図に表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャンネルノードをクリックすると、受信/送信メッセージ数付きのライブチャットバブルビューが表示されます。

| チャンネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒リフレッシュ |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db` を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web(Baileys)経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド + チャンネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース + チャンネル検出 |
| 🌐 **Webchat** | ✅ フル対応 | ✅ | 組み込みWeb UIセッション |
| 📡 **IRC** | ✅ フル対応 | ✅ | ターミナル風バブルUI |
| 🍏 **BlueBubbles** | ✅ フル対応 | ✅ | BlueBubbles REST API経由のiMessage |
| 🔵 **Google Chat** | ✅ フル対応 | ✅ | Chat API Webhook経由 |
| 🟣 **MS Teams** | ✅ フル対応 | ✅ | Teams botプラグイン経由 |
| 🔷 **Mattermost** | ✅ フル対応 | ✅ | セルフホスト型チームチャット |
| 🟩 **Matrix** | ✅ フル対応 | ✅ | 分散型、E2EE対応 |
| 🟢 **LINE** | ✅ フル対応 | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ フル対応 | ✅ | 分散型NIP-04 DM |
| 🟣 **Twitch** | ✅ フル対応 | ✅ | IRC接続経由のチャット |
| 🔷 **Feishu/Lark** | ✅ フル対応 | ✅ | WebSocketイベント購読 |
| 🔵 **Zalo** | ✅ フル対応 | ✅ | Zalo Bot API |

> **自動検出:** ClawMetryは `~/.openclaw/openclaw.json` を読み取り、実際に設定されているチャンネルのみを描画します。手動設定は不要です。

## Dockerデプロイ

ClawMetryをコンテナで実行したいですか?問題ありません!🐳

**Dockerでのクイックスタート:**

```bash
# イメージをビルド
docker build -t clawmetry .

# デフォルト設定で実行
docker run -p 8900:8900 clawmetry

# あるいはエージェントのデータディレクトリをマウント(例: OpenClawの ~/.openclaw)
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

> **注:** Docker内で実行する場合は、ClawMetryがセットアップを自動検出できるよう、エージェントのデータ + ログディレクトリ(例: `~/.openclaw`、`~/.claude`、`~/.codex`)をマウントしてください。

## 必要条件

- Python 3.8+
- Flask(pip経由で自動インストール)
- 同一マシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravityのいずれか(またはDocker用のマウントボリューム)
- LinuxまたはmacOS

## NemoClaw / OpenShell 対応

ClawMetryは[NemoClaw](https://github.com/NVIDIA/NemoClaw) — サンドボックス化されたOpenShellコンテナ内でエージェントを実行する、NVIDIAのOpenClaw向けエンタープライズセキュリティラッパー — を自動検出します。

ほとんどの場合、追加の設定は不要です。同期デーモンは、セッションファイルがホスト上の `~/.openclaw/` にあるか、OpenShellコンテナ内にあるかにかかわらず自動的に検出します。

### 仕組み

ClawMetryは2つの方法でNemoClawを検出します:

1. **バイナリ検出** — `nemoclaw` CLIの存在を確認し、`nemoclaw status` を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを `openshell`、`nemoclaw`、`ghcr.io/nvidia/` イメージについてスキャンし、ボリュームマウントまたは `docker cp` 経由でセッションを読み取り

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボードで `runtime=nemoclaw` と `container_id` のメタデータがタグ付けされるため、標準的なOpenClawセッションと一目で区別できます。

### 推奨セットアップ: ホスト上での同期デーモン

最良の体験のために、ClawMetryの同期デーモンは(サンドボックス内ではなく)**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# ホスト上で(サンドボックスの外)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中の任意のOpenShellコンテナ内のセッションを自動的に発見します。

### オプション: サンドボックス名を明示指定

自動検出がうまくいかない場合は、ClawMetryに正しいサンドボックスを指定します:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行(上級者向け)

同期デーモンをOpenShellサンドボックス**内**で実行する必要がある場合は、ClawMetryのインジェストAPIに到達できるよう、NemoClawのネットワークポリシーに次のegressルールを追加してください。

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
| `ingest.clawmetry.com` | 443 | HTTPS | はい(同期デーモン → クラウド) |
| `localhost:8900` | 8900 | HTTP | はい(ローカルダッシュボードUI) |
| Dockerソケット(`/var/run/docker.sock`) | — | Unixソケット | コンテナセッション検出用 |

同期デーモンは `ingest.clawmetry.com` へのアウトバウンドHTTPS呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[クラウドテストガイド](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetryは匿名のインストールライフサイクルpingを `https://app.clawmetry.com/api/install` に送信します。新しいマシンで `clawmetry` CLIを初めて実行したときに1回の `install` ping、新バージョンへのアップグレード後の初回実行時に1回の `update` ping、ダッシュボード内のオンボーディング選択を完了したときに1回の `onboarded` pingです。これは実際のインストール数を数えるため(PyPIの生のダウンロード数の約98%はミラー、CI、自動更新の再ダウンロードです)、そしてどのエージェントフレームワークとバージョンが実際に使われているかを把握するために使用します。

**バージョンごと・ライフサイクルイベントごとに最大1回のPOST**で、以下を含みます:

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` に保存されたランダムUUID | 重複排除。Cloud syncを明示的に接続するまでは匿名(その後は認証済みデーモンのハートビートがこれを運び、このインストールをあなたのアカウントに紐づけます) |
| `event` | `install` / `update` / `onboarded` | 新規インストールか、既存インストールのアップグレードか |
| `version` | `0.12.167` | 実際に使われているバージョン |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位 |
| `python` | `3.11.15` | Pythonバージョンのサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次にどのエージェントと統合すべきか |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの分離 |

**送信しないもの**: IP(クラウドはリクエストからサーバー側で国コードを導出した後、IPを破棄します)、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。ワイヤーペイロードは[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で監査可能です。

**オプトアウト**(以下のいずれか1つで永続的に無効化):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # シェルごと
export DO_NOT_TRACK=1                          # W3Cのツール横断標準
touch ~/.clawmetry/notelemetry                 # 永続的なファイルマーカー
```

ネットワーク障害がこの処理で `clawmetry` の実行をブロックすることはありません。このpingはデーモンスレッド上でfire-and-forget方式、タイムアウト3秒です。

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
  <strong>🦞 あなたのエージェントの思考を見る</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
