<!-- i18n-src:61beb8393e2f -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**エージェントは進捗を生まないまま何百回もツール呼び出しを行うことがあります。** ClawMetryは、あなたのコーディングエージェントがすでに書き出しているセッションファイルを読み取り、タイムライン、ツール呼び出し、そしてランタイムが公開しているトークンやコストのデータを一つのビューにまとめます。これにより、うまく機能している長時間の実行と、行き詰まっている実行を見分けられるようになります。

**30種類のAIエージェントランタイム**に対応 — Claude Code、OpenAI Codex、Hermes、OpenClaw、その他26種類。あなたのエージェントフリート全体を1つのダッシュボードで。（[全リスト](SUPPORTED_RUNTIMES.txt)はカタログから生成されています。）

> 🌐 **他の言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [もっと見る →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定不要で、すでにお使いのエージェントランタイムを自動的に見つけ出し、読み取り専用でアクセスし、実行方法には一切手を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## インストール前に

| | |
|---|---|
| **何をするか** | あなたのエージェントがすでに書き出しているセッションファイルとログを読み取ります。SDKもコード変更も、アプリへの計測導入も不要です。 |
| **何が見えるか** | セッションのタイムライン、ツールごとのリプレイ、トークンとコストの内訳、そして軌道シグナル（ループ、繰り返しの失敗）を、ランタイムごとに確認できます。 |
| **何が無料か** | `pip install clawmetry` は、アカウントもキーもネットワーク通信も不要で **OpenClaw、NVIDIA NemoClaw、Goose** を読み取ります。他の27種類 — Claude Code、Codex、Cursorなど — は、クローズドソースの `clawmetry-pro` コンパニオンによって読み取られます。これは7日間のトライアルまたはプランに付属します。正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)を参照してください。 |
| **始め方** | `pip install clawmetry && clawmetry` を実行し、localhost:8900を開きます。このマシンにまだエージェントがない場合は、`clawmetry --sample` で3つのラベル付き合成セッションが開きます。 |
| **マシンから外に出るもの** | `clawmetry connect` を実行しない限り、セッションデータは外に出ません。デフォルトで実行される2つのものがありますが、どちらもオプトアウト可能で、セッション内容は一切含まれません: 匿名のインストールpingと、PyPIバージョンチェックです。すべての送信先は、コメントを読むのではなくワイヤーキャプチャから再構築された形で[docs/EGRESS.md](docs/EGRESS.md)に一覧化されています。 |

出力結果を判断する前に知っておく価値のある2つの制約があります。ランタイムによって公開されるデータは大きく異なり（コストを一切公開しないものもあります — [対応表](docs/compatibility.md)にランタイムごとの詳細があります）、また、あるアクションを観測できることと、それをブロックできることは同じではありません（[ランタイムごとに実際に有効なコントロール](docs/APPROVALS.md)）。


## 30種類のエージェントランタイムに対応

**オープンソースアプリで無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数を同時に実行すると、ヘッダーのスイッチャーがすべてのタブを選んだランタイムに合わせて再スコープします。

SDKを使って独自のエージェントを構築した場合でも、インターセプターがそのLLM呼び出しを追跡します。詳しくは[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## できること

- **セッションとトランスクリプト**: 各エージェントがターンごとに何をしたかをリプレイ付きで確認
- **コストとトークン**: ランタイム、モデル、セッション、日ごとに、異常検知フラグ付きで
- **フロー**: チャネル、モデル、ツールの間を移動するメッセージのライブ図
- **ブレイン**: 推論とツール呼び出しのイベントストリームをリアルタイムで
- **コンテキスト逼迫**: プロバイダーごとに正しくサイズ計算されたウィンドウ利用率、圧縮と強制オーバーフローの区別、さらにランタイムごとに「見えていない部分」のマップ（[方法](docs/CONTEXT_BLOWOUT.md)）
- **メモリとスキル**: 各ランタイムが実際にロードしたファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントのオフライン化を、Slack、Discord、PagerDuty、Telegram、Emailにルーティング
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認する（[方法](docs/APPROVALS.md)）

## コンテキスト逼迫と、監視にかかるコスト

どんなエージェント比較ツールを信頼する前にも答える価値のある2つの問いがあります。

**ランタイムをまたいだコンテキストウィンドウの逼迫をどう扱うか？**

利用率のパーセンテージは、その分母がどれだけ正直かによってのみ信頼できます。ClawMetryは、[誰でも読んでPRできるテーブル](clawmetry/context_windows.py)からプロバイダーごとにウィンドウサイズを算出しており、Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMをカバーしています。30種類すべてのランタイムを1社のものさしで測ることはしません。これは重要な点です。300KトークンのGPT-5のターンをAnthropicの200Kと比較すると「>100%、逼迫」と読めてしまいますが、実際にはGPT-5の400Kのうち75%にすぎません。同じものさしは、実際にオーバーフローした130KのDeepSeekのターンを、余裕のある65%として隠してしまいます。

各ウィンドウには出所が記載されています: `model_table`、`explicit_marker`、`observed_floor`、あるいはモデルが不明な場合は正直に `default` です。推測に基づくゲージが、ルックアップに基づくものと同じ権威を持つように表示されることはありません。

ClawMetryは、一部のランタイムでしか圧縮イベントを見ることができません。そのため `GET /api/context-coverage` は、ランタイムごとに、**ゼロが「正常に完走した」ことを意味するのか「見えていない」ことを意味するのか**を報告します。実際には見えていないことを意味する `0` は、そのように示されます。[詳細はこちら](docs/CONTEXT_BLOWOUT.md)

**計測にかかるコストは？**

| パス | エージェントへの追加分 | デフォルトか？ |
|---|---|---|
| セッションファイルのtail読み取り（全30ランタイム） | **0**。別プロセスで動作し、ClawMetryのコードはあなたのエージェントには含まれません | オン |
| HTTPインターセプター（`CLAWMETRY_INTERCEPT=1`） | LLM呼び出し1回あたり **+0.44ms**、5秒の呼び出しの0.009% | オフ |
| プレツールフック ゲート（ウォームキャッシュ） | ゲートされたツール呼び出し1回あたり **+44ms**（インタープリタの床36msを上乗せ） | オフ |
| エンフォースメントプロキシ | LLM呼び出し1回あたり **+9.7ms** | オフ |

デーモンのホストコスト: 取り込み **2,762イベント/秒**、ディスク上で**イベントあたり710バイト**（10万イベントあたり67.7MB）、そして繁忙なインストールで持続的に**1コアの約12%**。この最後の数字は自ら定めた5〜10%の予算を超えているため、隠さずに追いかけるべきバグとして公開しています。

Apple M2 Proで `benchmarks/overhead.py` を使って計測しました。このハーネスは各条件を別プロセスで実行し、その順序を入れ替え、**ラウンド間で符号が一致しない場合は数値を出力しません**。自分のマシンで1分もかからずに実行できます。

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートやエンフォースメントプロキシを含め、すべてのパスが計測されており、このハーネスはCI上でLinux、macOS、Windowsで実行されます。知っておく価値のある2つの結果: プロキシのコストはWindowsではLinuxのおよそ7倍かかり、デーモンは現在1コアの約12%を持続的に消費していて、自ら定めた5〜10%の予算を超えています。生のJSON、計測方法、そしてまだ計測されていない部分は[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 価格

| プラン | カバー範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外のすべてのランタイム、フリートビュー、クラウド同期 | ノードあたり月額$9 |
| **Pro** | Starter + コントロールと評価: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート、改ざん検知可能な監査ログ | ノードあたり月額$19 |

年間プラン、Enterprise、最新の価格は**[clawmetry.com/pricing](https://clawmetry.com/pricing)**にあります。セルフホスト型のライセンスキーはクラウドなしでも動作します（`clawmetry license`）。無料/有料の正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)にあります。

## データはあなたのマシンに留まります

ClawMetryはローカルのセッションファイルとログを読み取ります。**`clawmetry connect` を実行しない限り、セッションデータがあなたのマシンから外に出ることはありません** — プロンプト、応答、ツールの引数、ファイル内容、ログ行のいずれも含まれません。接続した場合、スナップショットはあなたのマシンから外に出ることのない鍵でエンドツーエンド暗号化され、ブラウザ側で復号されます。ノードに鍵がない場合、アップロードは平文で送信されるのではなくスキップされ、これはどんなサーバー応答によっても無効化できません。

接続前にデフォルトで実行されるものが2つありますが、どちらもオプトアウト可能で、セッションデータは含まれません: 匿名のインストールpingと、PyPIに対するバージョンチェックです。デフォルトのインストールでは、起動時のバナー行のためにあなたのパブリックIPを一度だけ検索します。すべての送信先、それが何を含むか、どう無効化するかは[docs/EGRESS.md](docs/EGRESS.md)に一覧化されています。セルフホスト、リポイント済み、エアギャップされたインストールは、任意の送信通信を一切行いません。

復号はあなたのブラウザ内で、私たちが提供するコードによって行われます。かつてはこれは単なる約束でしたが、今は検証可能なものになっています。あなたの鍵に触れるすべての行は1つの読みやすいファイル、[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)にあり、これはwheelに同梱されてそのまま配信され、サブリソース整合性ハッシュでピン留めされています。ブラウザが公開されたものと同じものを実行しているか確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これが証明しないこと: 私たちはそのファイルを読み込むページ自体も配信しているため、別のページを配信することもできてしまいます。整合性ハッシュは、侵害されたCDNからは守ってくれますが、ベンダー自身からは守ってくれません。得られるのは、置き換えを行うなら意図的かつページソース上で可視である必要があり、誰でも取得できるPyPI上の成果物とは異なるものになる、という点です。セルフホストまたはローカルのみでの運用は、この依存関係そのものを取り除きます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、WindowsでPython 3.8以上が必要で、同じマシンに少なくとも1つのエージェントランタイムが必要です。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

あるいは、エージェントにセットアップさせることもできます。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)スキルは、Claude Code、Codex、Cursor、Gemini CLI、Copilot、OpenCodeに対して、ClawMetryをインストールし、マシン上のエージェントが何をしていて何を消費しているかを報告し、要求に応じて特定のセッションを停止し、リスクのあるツール呼び出しを承認待ちで保留する方法を教えます:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ドキュメント

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | 各アダプターが読み取るもの、ランタイムを追加する方法 |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | プロバイダーごとのウィンドウ、圧縮とオーバーフローの区別、ランタイムごとのカバレッジ |
| [Overhead](docs/OVERHEAD.md) | 計測にかかる実測コストと、それを再現するためのハーネス |
| [Entitlements](docs/ENTITLEMENTS.md) | 無料と有料の区分、ティアマトリックス、ライセンスCLI |
| [Approvals & policies](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォンでの承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | どこへでもトレースをエクスポートし、どこからでもOTLPを取り込む |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChainをエンドツーエンドで、実行可能な例付きで |
| [SDK tracking](docs/SDK_TRACKING.md) | 自分で構築したエージェントのコスト帰属 |
| [Chat channels](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行方法 |
| [Telemetry](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動ping、それらを無効化する方法 |

## スクリーンショット

以下の数字はすべて、何も仕込んでいない読み取り専用の実マシン1台からのものです。

**何かが起きたことだけでなく、何かが間違っていることを教えてくれます。**
上部に2つの異常検知バナー: 支出が日次平均の7倍で推移していること、そして4.2倍のコストスパイク。その下には、直近667セッションのうち324セッションが原因別に項目化された無駄シグナルを持っていることが表示されています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこへ行ったかを、どの期間でも示します。**
今日$252.47、今週$513.15、今月$1,312.92、それぞれの背後にあるトークン数と、サブスクリプションがすでにどれだけをカバーしているかも表示されます。その下には、回収可能として項目化された約$1,128/月と、キャッシュ再利用によってすでに節約された$17,256/月があります。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージがどのように答えになるかを描き出します。**
ライブフロー図: あなた、メッセージが届いたチャネル、ゲートウェイ、現在応答しているモデル、そしてそれが利用したすべてのツール。作業がそれらを通過するにつれ、ノードが点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを1つのテーブルで。**
何を実行しているか、直近24時間と全期間でのコスト、最後に見られたのはいつか、誰が所有しているか、サブスクリプションが費用をカバーしているかどうか。ここには14エージェント、稼働中の3セッション、静止中の13。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とお金がツールごとにどこへ行ったかを示します。**
実セッションの1ターン: 11.2分で11個のツール、$1.16。すべてのBash呼び出しとモデル呼び出しはタイムライン上に独自のバーを持つため、4.1分かかったコマンドと226msで終わったコマンドが一目で見分けられます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、成果そのものを採点します。**
今週の評価はA: 54件のタスクがクリーンに完了し、2件の粗い実行が$48.57のコストとなり、判断するには活動が少なすぎた実行は勝ちとしてカウントされるのではなく評価から除外されます。それぞれの粗い実行はそのトレースにリンクされています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**なぜコンテキストウィンドウが埋まり続けるのかを示します。**
最新ターンで100万トークンのウィンドウのうち71.5万トークン、83.3%のピーク、オーバーフローではなくすべてプロアクティブに発火した4回の圧縮、そしてその背後にあるすべてのターンの利用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**設定不要で検知が動作します。**
組み込みの検知器はインストール時からオンになっています: エージェントが静かになった、テレメトリフィードが停止した、コストスパイク、トークンバースト、エラーの増加、エラースパイク、予算しきい値、脅威シグネチャの一致、セキュリティツールの検出結果、セキュリティ体制の変化。独自のルールは追加でオプションとして設定できます。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しの保留はオプトインで、デフォルトはオフです。**
再帰的な削除、force push、sudo、シークレット、パッケージのインストール、外部への通信呼び出しには、それぞれオンにできるルールがあります。オンにするまでは、ClawMetryは監視するだけで何も変更しません。一度オンにすると、一致する呼び出しはここ（またはあなたのスマートフォン）で承認または拒否を待ちます。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとの詳細: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 評価・受賞

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · Built by [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
