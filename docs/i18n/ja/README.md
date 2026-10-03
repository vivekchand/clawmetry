<!-- i18n-src:c99ac0512cae -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**エージェントは進捗がないまま何百回もツール呼び出しを行うことがあります。** ClawMetryは、コーディングエージェントが既に書き出しているセッションファイルを読み取り、タイムライン、ツール呼び出し、そしてランタイムが公開しているトークンとコストのデータを1つのビューにまとめます。これにより、順調に進んでいる長時間の実行と、詰まってしまっている実行を見分けられます。

**33種類のAIエージェントランタイム**に対応 — Claude Code、OpenAI Codex、Hermes、OpenClaw、その他29種。エージェントフリート全体を1つのダッシュボードで。([完全なリスト](SUPPORTED_RUNTIMES.txt)、カタログから生成。)

> 🌐 **言語を選択:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [もっと見る →](docs/i18n/)

コマンド1つ。設定ゼロ。すべてを自動検出します。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定は不要です。すでにお使いのエージェントランタイムを見つけ、読み取り専用で読み込み、動作には何も変更を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## インストール前に

| | |
|---|---|
| **できること** | お使いのエージェントが既に書き出しているセッションファイルとログを読み取ります。SDKも、コード変更も、アプリへの計測コードの追加も不要です。 |
| **見えるもの** | ランタイムごとのセッションタイムライン、ツール単位のリプレイ、トークン/コストの内訳、そして軌道上の兆候(ループ、繰り返しの失敗)。 |
| **無料の範囲** | `pip install clawmetry` は **OpenClaw、NVIDIA NemoClaw、Goose、Qwen Code** をアカウント不要・キー不要・ネットワーク通信なしで読み取ります。残りの28種 — Claude Code、Codex、Cursorなど — はクローズドソースの `clawmetry-pro` コンパニオンが読み取り、これは7日間の無料トライアルまたは有料プランで利用できます。正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)を参照してください。 |
| **始め方** | `pip install clawmetry && clawmetry` を実行し、localhost:8900を開きます。このマシンにまだエージェントがない場合は、`clawmetry --sample` でラベル付きの合成セッション3つを使って開けます。 |
| **マシンから外部に送られるもの** | `clawmetry connect` を実行しない限り、セッションデータは送信されません。デフォルトで動作するものが2つあり、いずれもオプトアウト可能でセッション内容は含みません: 匿名のインストールピングと、PyPIバージョンチェックです。すべての送信先は[docs/EGRESS.md](docs/EGRESS.md)に記録されており、コメントを読んで作ったものではなく、ワイヤーキャプチャから再構築されています。 |

出力を評価する前に知っておくべき制限が2つあります: ランタイムが公開するデータは大きく異なります(コストを一切公開しないものもあります — どのランタイムかは[マトリクス](docs/compatibility.md)に記載)、そして、動作を観察できることと、それを止められることは同じではありません([ランタイムごとに実際に使える制御機能](docs/APPROVALS.md))。


## 33種のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**有料プランで:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

すべてのランタイムで同じダッシュボードが使えます。複数のランタイムを同時に実行していれば、ヘッダーのスイッチャーでどのタブもそのランタイムに合わせて切り替えられます。

SDKで独自のエージェントを構築した場合も、インターセプターがそのLLM呼び出しを追跡します。詳しくは[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## 得られるもの

- **セッションとトランスクリプト**: 各エージェントがターンごとに何をしたか、リプレイ付きで
- **コストとトークン**: ランタイム、モデル、セッション、日ごとに、異常フラグ付きで
- **フロー**: チャネル、モデル、ツールの間を移動するメッセージのライブダイアグラム
- **ブレイン**: 発生した通りの推論とツール呼び出しのイベントストリーム
- **コンテキスト枯渇**: プロバイダーごとに正しくサイズ調整されたウィンドウ利用率、圧縮と強制オーバーフローの区別、そして見えない部分をランタイムごとに示すマップ([仕組み](docs/CONTEXT_BLOWOUT.md))
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインをSlack、Discord、PagerDuty、Telegram、Emailへルーティング
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認([仕組み](docs/APPROVALS.md))

## コンテキスト枯渇と、監視にかかるコスト

どんなエージェント比較ツールでも、信頼する前に答えておくべき質問が2つあります。

**ランタイムをまたいでコンテキストウィンドウの枯渇をどう扱っているか?**

利用率のパーセンテージは、何で割っているかが正確であって初めて意味を持ちます。ClawMetryは、[読める・PRできるテーブル](clawmetry/context_windows.py)からプロバイダーごとにウィンドウサイズを決めており、Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMを対象としています。33種すべてのランタイムを1社の基準で測ることはしません。これは重要です: 30万トークンのGPT-5ターンをAnthropicの20万トークン基準で評価すると「100%超、枯渇」と表示されますが、実際にはGPT-5の40万トークンの75%です。同じ基準では、実際には枯渇している13万トークンのDeepSeekターンが、安心できる65%として隠れてしまいます。

ウィンドウにはそれぞれ出典が記録されます: `model_table`、`explicit_marker`、`observed_floor`、またはモデルが不明な場合の正直な `default` です。推測で作られたゲージは、検索で作られたゲージと同じ権威を持って表示されることはありません。

ClawMetryが圧縮イベントを確認できるのは一部のランタイムだけです。そのため `GET /api/context-coverage` は、ランタイムごとに、**ゼロが「問題なく実行できた」ことを意味するのか、「見えていない」ことを意味するのか**を報告します。実際には見えていないことを意味するゼロは、そのように表示されます。[詳細](docs/CONTEXT_BLOWOUT.md)

**計測にはどれくらいコストがかかるか?**

| 経路 | エージェントに加わる負荷 | デフォルト? |
|---|---|---|
| セッションファイルのtail監視(全33ランタイム) | **0**。別プロセスで動作し、エージェント内にClawMetryのコードは存在しない | オン |
| HTTPインターセプター(`CLAWMETRY_INTERCEPT=1`) | LLM呼び出し1回あたり **+0.44 ms**、5秒の呼び出しの0.009% | オフ |
| プレツールフックゲート(ウォームキャッシュ) | ゲートされたツール呼び出し1回あたり **+44 ms**(インタープリタの基準値36 msに加えて) | オフ |
| エンフォースメントプロキシ | LLM呼び出し1回あたり **+9.7 ms** | オフ |

デーモンのホストコスト: 取り込み **2,762イベント/秒**、ディスク上で **710バイト/イベント**(10万イベントあたり67.7MB)、稼働中のインストールで常時 **1コアの約12%**。この最後の数字は、私たちが掲げている5〜10%の予算を超えているため、追いかけるべきバグとしてこのページに公開しています。

Apple M2 Pro上で `benchmarks/overhead.py` を使って計測しています。このハーネスは各条件を別プロセスで実行し、実行順序を交互に変え、**ラウンド間で符号が一致しない場合は数値を表示しません**。自分のマシンで1分で実行できます:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートやエンフォースメントプロキシを含め、すべての経路が計測されており、このハーネスはCI上でLinux、macOS、Windowsで動作します。知っておくべき結果が2つあります: プロキシのコストはWindowsではLinuxの約7倍かかること、そしてデーモンは現在1コアの約12%を常時使用しており、私たちが掲げる5〜10%の予算を超えています。生のJSON、手法、そしてまだ計測されていない部分は[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 価格

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code、ダッシュボード全機能、ローカルのみ | $0 |
| **Starter** | 上記以外のすべてのランタイム、フリートビュー、クラウド同期 | ノードあたり月$9 |
| **Pro** | Starterに加えて制御と評価: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート、改ざん検知可能な監査ログ | ノードあたり月$19 |

年間プラン、Enterprise、最新の価格は**[clawmetry.com/pricing](https://clawmetry.com/pricing)**にあります。セルフホスト用のライセンスキーはクラウドなしでも機能します(`clawmetry license`)。無料/有料の正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)にあります。

## データはあなたのマシンに留まります

ClawMetryはローカルのセッションファイルとログを読み取ります。**`clawmetry connect` を実行しない限り、セッションデータがマシンから外に出ることはありません** — プロンプト、返信、ツールの引数、ファイル内容、ログ行も含めてです。接続した場合、スナップショットはマシンから一度も出ないキーでエンドツーエンド暗号化され、ブラウザ内で復号されます。ノードにキーがない場合、アップロードは平文で送られるのではなくスキップされ、サーバー側のレスポンスでこれをオフにすることはできません。

接続前にデフォルトで動作するものが2つあり、いずれもオプトアウト可能でセッションデータは含みません: 匿名のインストールピングと、PyPIに対するバージョンチェックです。デフォルトのインストールでは、起動時のバナー表示のために、公開IPアドレスを一度だけ確認します。すべての送信先、送信内容、オフにする方法は[docs/EGRESS.md](docs/EGRESS.md)に一覧化されています。セルフホスト、リポイント、エアギャップ環境のインストールでは、任意の外部通信は一切行われません。

復号はブラウザ内で、私たちが提供するコードによって行われます。これは以前は単なる約束でしたが、今では確認できるものになっています。あなたのキーに触れるすべての行は読みやすい1つのファイル、[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)にまとめられており、wheelパッケージ内に同梱されそのまま提供され、サブリソースインテグリティハッシュで固定されています。ブラウザが実際に私たちが公開したものを実行しているか確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これが証明しないこと: ファイルを読み込むページ自体は私たちが配信しているため、別のページを配信することも可能です。インテグリティハッシュは、侵害されたCDNからは守りますが、ベンダー自身からは守りません。得られるのは、改ざんが行われる場合は意図的でなければならず、ページソース上で可視であり、誰でも取得できるPyPI上のアーティファクトと異なるものになる、ということです。セルフホストまたはローカル専用運用を選べば、この依存関係自体をなくせます。

## インストール

```bash
pip install clawmetry     # その後: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、WindowsでPython 3.8以上が必要で、同じマシン上に少なくとも1つのエージェントランタイムが必要です。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

あるいは、エージェントに設定を任せることもできます。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)スキルは、Claude Code、Codex、Cursor、Gemini CLI、Copilot、OpenCodeに対して、ClawMetryのインストール、マシン上のエージェントの動作と費用の報告、リクエストに応じた1セッションの停止、リスクのあるツール呼び出しの承認保留を教えます:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが読み取る内容と、ランタイムを追加する方法 |
| [コンテキスト枯渇](docs/CONTEXT_BLOWOUT.md) | プロバイダーごとのウィンドウ、圧縮とオーバーフローの区別、ランタイムごとのカバレッジ |
| [オーバーヘッド](docs/OVERHEAD.md) | 計測された計測コストと、再現するためのハーネス |
| [権限(Entitlements)](docs/ENTITLEMENTS.md) | 無料と有料の区分、ティアマトリクス、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォンでの承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | どこへでもトレースをエクスポートし、どこからでもOTLPを取り込む |
| [独自のエージェントを持ち込む](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChainを実行可能な例とともにエンドツーエンドで |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自分で構築したエージェントのコスト帰属 |
| [チャットチャネル](docs/CHANNELS.md) | フローに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールとデスクトップオープンのピング、そのオフにする方法 |

## スクリーンショット

以下の数値はすべて、何も仕込んでいない実際の1台のマシンから、読み取り専用で取得したものです。

**何が起きたかだけでなく、何が間違っているかを教えてくれます。**
上部に2つの異常バナー: 支出が日次平均の7倍で推移していること、そして4.2倍のコストスパイク。その下には、直近667セッションのうち324セッションが浪費の兆候を示しており、原因別に項目化されています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこに流れたか、どの時間窓でも見せてくれます。**
今日 $252.47、今週 $513.15、今月 $1,312.92、それぞれの裏にあるトークン数と、サブスクリプションがすでにカバーしている割合。その下には、回収可能として項目化された約$1,128/月と、キャッシュ再利用によってすでに節約された$17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージがどのように答えになるかを描き出します。**
ライブフローダイアグラム: あなた、メッセージが届いたチャネル、ゲートウェイ、今まさに答えているモデル、そしてそれが使ったすべてのツール。作業がノードを通過するたびにノードが点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを1つの表に。**
実行しているもの、過去24時間と生涯のコスト、最後に確認された時刻、所有者、サブスクリプションが費用をカバーしているかどうか。ここには14のエージェント、3セッションが稼働中、13が静止中。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とお金がどこに流れたかを、ツールごとに見せてくれます。**
実際のセッションの1ターン: 11.2分間に11個のツールで$1.16。すべてのBash呼び出しとモデル呼び出しがタイムライン上に独自のバーを持つため、4.1分かかったコマンドと226msで終わったコマンドを一目で区別できます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、作業そのものを評価します。**
今週はA評価: 54件のタスクがクリーンに完了し、2件の粗いタスクが$48.57のコストとなり、判断に十分な活動量がない実行は評価から除外され、成功としてカウントされることはありません。粗い実行はそれぞれトレースにリンクされています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**なぜコンテキストウィンドウが埋まり続けるのかを見せてくれます。**
直近のターンで100万トークンウィンドウのうち71.5万トークンを使用、ピーク83.3%、オーバーフローではなくすべて事前対応的に発火した4回の圧縮、そしてその背後にあるすべてのターンの利用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**検知は何も設定しなくても動作します。**
組み込みの検知器はインストール直後からオンになっています: エージェントが静止した、テレメトリフィードが停止した、コストスパイク、トークンバースト、エラー増加、エラースパイク、予算しきい値、脅威シグネチャの検出、セキュリティツールの検出結果、セキュリティ態勢の変化。独自のルールは、その上にオプションで追加できます。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しの保留はオプトイン方式で、デフォルトではオフです。**
再帰的な削除、強制プッシュ、sudo、秘密情報、パッケージのインストール、外部への通信、それぞれにオンにできるルールがあります。オンにするまでは、ClawMetryは監視するだけで何も変更しません。一度オンにすると、該当する呼び出しはここ(またはスマートフォン)で承認または拒否を待ちます。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとのさらに多くの例: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 受賞歴

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## スター履歴

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · [@vivekchand](https://github.com/vivekchand) が開発 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
