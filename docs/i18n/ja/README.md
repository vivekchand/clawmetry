<!-- i18n-src:7cfb63716507 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を見る。** **14種類のAIエージェントランタイム**をリアルタイムで観測: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他10種類。エージェント群全体をひとつのダッシュボードで。

> 🌐 **多言語版:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [その他 →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開けば、それで完了です。

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14種類のエージェントランタイムに対応

ClawMetryはOpenClawの観測ツールとして始まりましたが、今では**エージェント群全体**をひとつのダッシュボードで計測し、マシン上の各ランタイムを自動検出します。

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClawとNemoClawはオープンソース版アプリで無料で使えます。それ以外のランタイムはClawMetry Cloud、またはセルフホストのProライセンスで利用可能になります。ヘッダーからランタイムを切り替えると、コスト・トークン・ツール・トレースなど各タブの表示がそのランタイムに絞り込まれます。正確な無料/有料の分け方、ティア表、`/api/entitlement`の形式、`clawmetry license` CLIについては**[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**を参照してください。

## 得られるもの

- **Flow** — チャネル、ブレイン、ツールを通ってメッセージが流れる様子をリアルタイムでアニメーション表示
- **Overview** — ヘルスチェック、アクティビティのヒートマップ、セッション数、モデル情報
- **Usage** — 日次/週次/月次で内訳を確認できるトークンおよびコストのトラッキング
- **Sessions** — モデル、トークン数、最終アクティビティを含むアクティブなエージェントセッション
- **Crons** — ステータス、次回実行時刻、所要時間を含むスケジュールジョブ
- **Logs** — 色分けされたリアルタイムのログストリーミング
- **Memory** — SOUL.md、MEMORY.md、AGENTS.md、デイリーノートを閲覧
- **Transcripts** — セッション履歴を読むためのチャットバブルUI
- **Alerts** — 予算上限、エラー率トリガー、エージェントオフライン検知。Slack、Discord、PagerDuty、Telegram、Emailへ通知
- **Approvals** — 破壊的な削除、force push、DBの変更、sudo、パッケージインストール、ネットワーク呼び出しをワンクリックの承認でゲート

## スクリーンショット

### 🧠 Brain — ライブエージェントイベントストリーム
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — トークン使用量とセッションサマリー
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — リアルタイムのツール呼び出しフィード
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — モデル・セッション別のコスト内訳
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ワークスペースのファイルブラウザ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — セキュリティ態勢と監査ログ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — 予算上限、エラー率トリガー、Slack / Discord / PagerDuty / Emailへのwebhook
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — リスクのあるツール呼び出しを手動承認でゲート。ポリシーに基づく保護ルール
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Codeの実行前ブロッキング** — コマンド1つで、該当するツール呼び出しを*実行前*に一時停止し、あなたの判断を待つPreToolUseフックをインストールできます([cloud push notifications](https://app.clawmetry.com/push)を有効にすればスマートフォンからワンタップで対応可能):

```bash
clawmetry hooks install     # ~/.claude/settings.json に書き込み(冪等)
clawmetry hooks status      # 何が接続されているか、有効なポリシー数を表示
clawmetry hooks uninstall   # ClawMetryが追加したエントリのみ削除
```

拒否(deny)はそのツール呼び出し1件のみをブロックします。エージェントはセッションを維持したまま、別のアプローチを試すことができます。スマートフォンで承認するとClaude Code自体の権限プロンプトはスキップされます(すでに回答済みのため)。Claude Code自体があなたの応答を待っている場合(`permission_prompt` / `idle_prompt` 通知)にもスマートフォンにプッシュ通知が届きます。

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

v2のReactアプリは`frontend/`にあり、v2を有効にしてFlaskサーバーを起動すると`/v2`で配信されます。

開発時はターミナルを2つ使用します。

```bash
# ターミナル1: :8900でFlask API/サーバーを起動
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ターミナル2: :5173でViteの開発サーバーを起動
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/`を開いてください。Viteが`/api`リクエストを`http://localhost:8900`にプロキシするため、追加のCORS設定なしでReactアプリがローカルのFlaskサーバーと通信できます。

Pythonパッケージに同梱するビルドバンドルを作成するには:

```bash
cd frontend
npm run build
```

本番用バンドルは`clawmetry/static/v2/dist/`に書き出されます。

## ランタイム/エージェント互換性

ClawMetryはOpenClawだけでなく、多くのAIエージェントランタイムを観測します。OpenClaw以外の各ランタイムには専用のリーダーアダプタが用意されており、そのランタイム固有のセッション形式をClawMetryの統一フォーマットに変換します。デーモンはこれらを同じDuckDBストア+クラウドスナップショットに取り込み、ランタイムでタグ付けします。複数のランタイムが存在する場合、Session replayタブに**ランタイム切り替え**が表示されます。全体のマトリクスとランタイム追加ガイドは[`docs/compatibility.md`](docs/compatibility.md)を、OpenClawファミリーの入門解説は[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)を参照してください。

[Perplexityのnumbat](https://github.com/perplexityai/numbat)エージェントセキュリティツールを利用していますか? ClawMetryはそのfindingsと enforcement decisionsをそのまま取り込めます。詳しくは[`docs/NUMBAT.md`](docs/NUMBAT.md)を参照してください。

| ランタイム/エージェント | ステータス | 備考 |
|---|---|---|
| **OpenClaw** | ネイティブ | リファレンスランタイム、自動検出 |
| **PicoClaw** | Betaアダプタ | フラットな`providers.Message`のJSONL(`~/.picoclaw/workspace/sessions`)。トランスクリプト、モデル、ツール呼び出し。 |
| **NanoClaw** | Betaアダプタ | セッションごとのSQLite(`data/v2-sessions`)。トランスクリプト+メッセージ数。 |
| **Hermes** | Betaアダプタ | SQLite `~/.hermes/state.db`。トランスクリプト、モデル、トークン/コスト。 |
| **Claude Code** | Betaアダプタ | JSONL `~/.claude/projects/.../<id>.jsonl`。トランスクリプト、モデル、ツール呼び出し+thinking、トークン使用量。 |
| **Codex** | Betaアダプタ | Rollout JSONL `~/.codex/sessions/...`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Cursor** | Betaアダプタ | SQLite `state.vscdb`。チャット/コンポーザーのトランスクリプト、モデル。 |
| **Aider** | Betaアダプタ | プロジェクトごとの`.aider.chat.history.md`。トランスクリプト、モデル、トークン数。 |
| **Goose** | Betaアダプタ | SQLite `~/.local/share/goose`。トランスクリプト、モデル、ツール呼び出し、トークン合計。 |
| **opencode** | Betaアダプタ | SQLite `~/.local/share/opencode`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **Qwen Code** | Betaアダプタ | JSONL `~/.qwen/projects/.../chats`。トランスクリプト、モデル、ツール呼び出し、トークン使用量。 |
| **Pi** | Betaアダプタ | JSONL `~/.pi/agent/sessions`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **Deep Agents** | Betaアダプタ | SQLite `~/.deepagents/.state/sessions.db`。トランスクリプト、モデル、ツール呼び出し、トークン+コスト。 |
| **n8n** | Betaアダプタ | SQLite `~/.n8n/database.sqlite`。ワークフロー実行、ノード実行、AI Agentプロンプト、n8nが記録している場合はモデル+トークン。 |
| **Antigravity** | Betaアダプタ | `~/.gemini/<flavor>/brain/`以下のBrain JSONL。会話、ツールステップ、thinking、生成ごとのGemini token分割+コスト、バックグラウンド生成の消費量。 |
| **GitHub Copilot** | Betaアダプタ | Copilot CLIの`events.jsonl`(`~/.copilot/session-state/`以下)+呼び出しごとの使用量台帳`session-store.db`。会話、ツール呼び出し、モデルルーティング、キャッシュを考慮したトークン分割、ベンダー請求のAIクレジットコスト。 |
| **Grok** | Betaアダプタ | xAI Grok Build CLI(`~/.grok/bin/grok`のRustバイナリ): グローバルイベントログ`~/.grok/logs/unified.jsonl`+セッションごとの`~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`。会話、ターンごとのトークン分割、モデルルーティング、そしてマシンから外に出たものを確認できるよう`~/.grok/upload_queue/`にステージされるCLIの送信リポジトリペイロード。 |

「Betaアダプタ」とは、そのランタイムの実際のディスク上フォーマット用にClawMetryがリーダーを提供していることを意味し、それぞれ実機での実インストールに対してビルド・検証されています(`tests/fixtures/runtimes/<rt>/`参照)。アダプタは読み取り専用であり、それぞれ自分のランタイムが実際に何を保存しているかについて正直です(例: PicoClaw/NanoClaw/Cursorはトークンコストをディスクに書き込みません)。1つのノードで複数のランタイムが動作している場合、ランタイム切り替えでセッションビューを1つに絞り込み、クリーンに深掘りできます。

## 任意のSDKエージェントを追跡 — アウトループのコスト帰属

上記のランタイムはすべてセッションをディスクに書き込みます。あなた自身の**本番エージェント**、つまりOpenAI Agents SDK、LangChain、Vercel AI SDK、LlamaIndex、E2B、あるいは素の`httpx`ループの上に構築したものは、そうではありません。ClawMetryのゼロコンフィグ・インターセプタは、`httpx`/`requests`へのモンキーパッチによって、そうしたエージェントのLLM呼び出し(コスト、トークン、レイテンシ、エラー)もそのまま捕捉します。

```python
import clawmetry.track            # インターセプタを有効化
clawmetry.track.set_source("support-agent")   # このプロダクトに名前を付ける

# ...エージェントは通常どおり動作します。すべてのLLM呼び出しが追跡・帰属されます。
```

`set_source()`(または`CLAWMETRY_SOURCE=support-agent`環境変数)は各呼び出しに**名前付きソース**をタグ付けするため、実行している各プロダクトがダッシュボードのOverviewにある**🔌 Out-loop sources**カードに、それぞれ独立したコスト帰属可能な行として表示されます。呼び出し数、プロバイダー、レイテンシ、エージェントごとのエラー率が確認できます。ソースを設定しなくても呼び出しは追跡されますが、その場合カードは非表示のままです。

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

これはランタイムアダプタが供給するのと同じデータレイヤー(DuckDB → クラウドスナップショット)を使うため、アウトループのソースも他のすべてと同様にE2E暗号化された状態でクラウドダッシュボードに同期されます。

## OpenTelemetry — ベンダーニュートラルに、トレースをどこへでも送信

ClawMetryは**GenAIセマンティック規約**を用いて双方向で**OpenTelemetry**を話すため、あなたのエージェントのトレースが特定のツールにロックインされることはありません。

各セッション(LLM呼び出し、ツール、サブエージェント、トークン、コスト)を、OTLP/HTTPのGenAIスパンとして任意のコレクター(Datadog、Grafana、Honeycomb、あるいは自前のOTel Collector)へ**エクスポート**:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# 同等の指定方法:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

認証ヘッダーとポーリング間隔は任意の環境変数で指定できます。

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # 追加のHTTPヘッダー
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # 秒単位(デフォルト60)
```

**取り込み** — 組み込みのOTLPレシーバーは、`/v1/traces`と`/v1/metrics`で他の任意のソースからのトレースとメトリクスを受け付けます(protobuf取り込みには`pip install clawmetry[otel]`が必要)。

ゼロコンフィグでローカルファーストなClawMetryダッシュボード**と**、チームがすでに運用しているバックエンドへのデータ送信の**両方**を得られます。ロックインもなく、2つ目のエージェントをインストールする必要もありません。

## 設定

ほとんどの人には設定は不要です。ClawMetryはワークスペース、ログ、セッション、cronを自動検出します。

カスタマイズが必要な場合:

```bash
clawmetry --port 9000              # カスタムポート(デフォルト: 8900)
clawmetry --host 127.0.0.1         # localhostのみにバインド
clawmetry --workspace ~/mybot      # カスタムワークスペースパス
clawmetry --name "Alice"           # Flowビジュアライゼーションでのあなたの名前
```

全オプション: `clawmetry --help`

## 対応チャネル

ClawMetryは、設定済みのすべてのOpenClawチャネルについてライブアクティビティを表示します。`openclaw.json`で実際に設定されているチャネルのみがFlow図に表示され、未設定のものは自動的に非表示になります。

Flow内の任意のチャネルノードをクリックすると、受信/送信メッセージ数を含むライブのチャットバブルビューが表示されます。

| チャネル | ステータス | ライブポップアップ | 備考 |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ フル対応 | ✅ | メッセージ、統計、10秒ごとの更新 |
| 💬 **iMessage** | ✅ フル対応 | ✅ | `~/Library/Messages/chat.db`を直接読み取り |
| 💚 **WhatsApp** | ✅ フル対応 | ✅ | WhatsApp Web(Baileys)経由 |
| 🔵 **Signal** | ✅ フル対応 | ✅ | signal-cli経由 |
| 🟣 **Discord** | ✅ フル対応 | ✅ | ギルド+チャネル検出 |
| 🟪 **Slack** | ✅ フル対応 | ✅ | ワークスペース+チャネル検出 |
| 🌐 **Webchat** | ✅ フル対応 | ✅ | 組み込みのWeb UIセッション |
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

> **自動検出:** ClawMetryは`~/.openclaw/openclaw.json`を読み取り、実際に設定されているチャネルのみを描画します。手動設定は不要です。

## Dockerデプロイ

コンテナでClawMetryを実行したいですか? 問題ありません! 🐳

**Dockerでのクイックスタート:**

```bash
# イメージをビルド
docker build -t clawmetry .

# デフォルト設定で実行
docker run -p 8900:8900 clawmetry

# あるいはエージェントのデータディレクトリをマウント(例: OpenClawの~/.openclaw)
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

> **注:** Docker上で実行する場合、ClawMetryが自動検出できるようエージェントのデータ+ログディレクトリ(例: `~/.openclaw`、`~/.claude`、`~/.codex`)をマウントしてください。

## 必要要件

- Python 3.8以上
- Flask(pipで自動インストール)
- 同一マシン上のAIエージェントランタイム: OpenClaw、NVIDIA NemoClaw、Claude Code、Codex、Cursor、Goose、Hermes、opencode、Qwen Code、Aider、NanoClaw、PicoClaw、Pi、Deep Agents、n8n、Antigravity、GitHub Copilot、Grok、またはQM(Dockerの場合はマウントされたボリュームでも可)
- LinuxまたはmacOS

## NemoClaw / OpenShellサポート

ClawMetryは、サンドボックス化されたOpenShellコンテナ内でエージェントを実行する、NVIDIAのOpenClaw向けエンタープライズセキュリティラッパーである[NemoClaw](https://github.com/NVIDIA/NemoClaw)を自動検出します。

ほとんどの場合、追加設定は不要です。同期デーモンは、セッションファイルがホスト上の`~/.openclaw/`にあるか、OpenShellコンテナ内にあるかに関わらず自動的に検出します。

### 動作の仕組み

ClawMetryは2つの方法でNemoClawを検出します。

1. **バイナリ検出** — `nemoclaw` CLIの有無を確認し、`nemoclaw status`を実行してサンドボックス情報を取得
2. **コンテナ検出** — 実行中のDockerコンテナを`openshell`、`nemoclaw`、`ghcr.io/nvidia/`のイメージについてスキャンし、ボリュームマウントまたは`docker cp`経由でセッションを読み取る

NemoClawコンテナから同期されたセッションファイルには、クラウドダッシュボード上で`runtime=nemoclaw`と`container_id`のメタデータがタグ付けされるため、標準的なOpenClawセッションと一目で区別できます。

### 推奨セットアップ: 同期デーモンをホスト側で実行

最良の体験のためには、ClawMetryの同期デーモンをサンドボックスの内側ではなく**ホストマシン**上で実行してください。これによりNemoClawのネットワークポリシー制限を回避できます。

```bash
# ホスト側で(サンドボックスの外)
pip install clawmetry
clawmetry connect
clawmetry sync
```

同期デーモンは、実行中のOpenShellコンテナ内のセッションを自動的に検出します。

### 任意: サンドボックス名の明示

自動検出がうまくいかない場合は、正しいサンドボックスをClawMetryに指定してください。

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### サンドボックス内での実行(上級者向け)

同期デーモンをOpenShellサンドボックスの**内側**で実行する必要がある場合は、ClawMetryのingest APIに到達できるよう、NemoClawのネットワークポリシーに以下のegressルールを追加してください。

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
| Dockerソケット(`/var/run/docker.sock`) | — | Unixソケット | コンテナ内セッション検出用 |

同期デーモンは`ingest.clawmetry.com`へのアウトバウンドHTTPS呼び出しのみを行います。インバウンドポートは不要です。

---

## クラウドデプロイ

SSHトンネル、リバースプロキシ、Dockerについては**[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**を参照してください。

## テスト

このプロジェクトはBrowserStackでテストされています。

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## テレメトリ

ClawMetryは匿名のインストールライフサイクルのpingを`https://app.clawmetry.com/api/install`に送信します。新しいマシンで初めて`clawmetry` CLIを実行したときの`install` ping、新しいバージョンへのアップグレード後の初回実行時の`update` ping、ダッシュボード内のオンボーディング選択を完了したときの`onboarded` pingです。これは実際のインストール数を数えるため(PyPIの生のダウンロード数の約98%はミラー、CI、自動更新の再ダウンロードです)、また実際にどのエージェントフレームワークとバージョンが使われているかを把握するために使用します。

**ライフサイクルイベント・バージョンごとに最大1回のPOST**で、以下を含みます。

| フィールド | 例 | 理由 |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`に保存されたランダムUUID | 重複排除。Cloud syncを明示的に接続するまでは匿名(その後は認証済みデーモンのハートビートがこれを運び、このインストールをあなたのアカウントに紐付けます) |
| `event` | `install` / `update` / `onboarded` | 新規インストールか、既存インストールのアップグレードか |
| `version` | `0.12.167` | 実際に使われているバージョン |
| `os` / `os_version` | `Darwin` / `25.3.0` | プラットフォームサポートの優先順位 |
| `python` | `3.11.15` | Pythonバージョンのサポートマトリクス |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | 次に統合すべきエージェント |
| `is_ci` / `ci_provider` | `true` / `github_actions` | 人間によるインストールとCIノイズの区別 |

**送信しないもの**: IP(クラウドはリクエストからサーバー側で国コードのみを導出し、IPは破棄します)、ホスト名、ユーザー名、ワークスペースパス、ファイル内容、あなたのapi_key、あなたのメールアドレス、その他PIIやワークスペース固有の情報。実際の送信内容は[`clawmetry/telemetry.py`](clawmetry/telemetry.py)で確認できます。

**オプトアウト**(以下のいずれか1つで恒久的に無効化できます):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # シェルごと
export DO_NOT_TRACK=1                          # W3Cのクロスツール標準
touch ~/.clawmetry/notelemetry                 # 永続的なファイルマーカー
```

ネットワーク障害が発生しても`clawmetry`の実行がブロックされることはありません。このpingはデーモンスレッド上でfire-and-forgetとして送信され、タイムアウトは3秒です。

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
  <strong>🦞 エージェントの思考を見る</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
