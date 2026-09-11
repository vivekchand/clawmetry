<!-- i18n-src:12b97259721e -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**エージェントは進捗のないまま何百回もツール呼び出しを行うことがあります。** ClawMetryはコーディングエージェントがすでに書き出しているセッションファイルを読み込み、タイムライン、ツール呼び出し、そしてランタイムが公開しているトークンやコストのデータを一つのビューにまとめます。これにより、うまくいっている長時間実行と、行き詰まっている実行とを見分けられます。

**31種類のAIエージェントランタイム**に対応 — Claude Code、OpenAI Codex、Hermes、OpenClawほか27種。エージェント群全体を一つのダッシュボードで管理できます。([全リストはこちら](SUPPORTED_RUNTIMES.txt)、カタログから自動生成)

> 🌐 **この言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [他の言語 →](docs/i18n/)

コマンド一つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定は不要です。すでにお使いのエージェントランタイムを見つけ出し、読み取り専用でアクセスし、その動作方法には一切手を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## インストール前に

| | |
|---|---|
| **何をするか** | エージェントがすでに書き出しているセッションファイルとログを読み取ります。SDKもコード変更も、あなたのアプリへの計装も不要です。 |
| **何が見えるか** | セッションのタイムライン、ツールごとのリプレイ、トークンとコストの内訳、そして軌道シグナル(ループ、繰り返される失敗)をランタイムごとに表示します。 |
| **無料の範囲** | `pip install clawmetry` で**OpenClaw、NVIDIA NemoClaw、Goose**をアカウント不要・キー不要・ネットワーク通信なしで読み取れます。残り27種 — Claude Code、Codex、Cursorなど — はクローズドソースの`clawmetry-pro`コンパニオンが読み取ります。これは7日間の試用またはプランに付属します。正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)を参照してください。 |
| **始め方** | `pip install clawmetry && clawmetry` を実行し、localhost:8900を開きます。このマシンにまだエージェントがない場合は、`clawmetry --sample` を実行するとラベル付きの合成セッション3件で起動します。 |
| **マシンの外に出るもの** | `clawmetry connect` を実行しない限り、セッションデータは一切出ていきません。デフォルトで実行される2つの通信があり、いずれもオプトアウト可能でセッション内容は含みません — 匿名のインストールping、PyPIバージョンチェックです。すべての送信先は[docs/EGRESS.md](docs/EGRESS.md)に一覧化されており、コメントを読んだ内容ではなく通信キャプチャから再構築されています。 |

出力を判断する前に知っておくべき制約が2つあります。ランタイムによって公開されるデータは大きく異なり(コストを一切公開しないものもあります — [対応表](docs/compatibility.md)にランタイムごとの詳細があります)、また動作を観測できることとそれを止められることは同じではありません([ランタイムごとの実際に使える制御手段](docs/APPROVALS.md))。


## 31種のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プラン:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数同時に実行しても、ヘッダーのスイッチャーで各タブの対象をいずれか一つに切り替えられます。

SDKを使って自分でエージェントを構築した場合はどうでしょうか。インターセプターがそのLLM呼び出しも追跡します。詳細は[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## 得られるもの

- **セッションとトランスクリプト**: 各エージェントがターンごとに何を行ったか、リプレイ付きで
- **コストとトークン**: ランタイム、モデル、セッション、日ごとに、異常フラグ付きで
- **Flow**: チャンネル、モデル、ツールを通じて動くメッセージのライブダイアグラム
- **Brain**: 推論とツール呼び出しのイベントストリームをリアルタイムで
- **コンテキスト逼迫(blowout)**: プロバイダーごとにサイズ調整されたウィンドウ利用率、圧縮と強制オーバーフローの区別、さらに見えない範囲をランタイムごとにマップ([詳細](docs/CONTEXT_BLOWOUT.md))
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レートリミット、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインをSlack、Discord、PagerDuty、Telegram、Emailにルーティング
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認([詳細](docs/APPROVALS.md))

## コンテキストの逼迫と、監視にかかるコスト

どのエージェント比較ツールを信頼するかを判断する前に、答えておく価値のある2つの問いがあります。

**ランタイム間でのコンテキストウィンドウの逼迫をどう扱っているか?**

利用率のパーセンテージは、何で割っているかが正しくなければ意味がありません。ClawMetryは[読んでPRできるテーブル](clawmetry/context_windows.py)からプロバイダーごとにウィンドウのサイズを決めており、Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMをカバーしています。31種すべてのランタイムを一社のものさしで測ることはしません。これは重要な違いです。300KのGPT-5ターンをAnthropicの200Kで採点すると「>100%、逼迫」と読めますが、実際にはGPT-5の400Kの75%にすぎません。同じものさしは、本当にオーバーフローした130KのDeepSeekターンを、快適な65%として隠してしまいます。

すべてのウィンドウには出どころが付きます — `model_table`、`explicit_marker`、`observed_floor`、あるいはモデルが分からない場合は正直に`default`です。推測に基づくゲージが、ルックアップに基づくものと同じ権威を持って表示されることはありません。

ClawMetryが圧縮イベントを確認できるのは一部のランタイムだけです。そのため`GET /api/context-coverage`は、ランタイムごとに**ゼロが「問題なく実行された」ことを意味するのか、それとも「見えていない」ことを意味するのか**を報告します。実際には見えていないだけの`0`は、そう明示されます。
[詳細](docs/CONTEXT_BLOWOUT.md)

**計装のコストは?**

| パス | エージェントへの追加負荷 | デフォルトか? |
|---|---|---|
| セッションファイルのtailing(全31ランタイム) | **0**。別プロセスで動作し、ClawMetryのコードはエージェント内に一切入らない | オン |
| HTTPインターセプター(`CLAWMETRY_INTERCEPT=1`) | LLM呼び出し1回あたり**+0.44ミリ秒**、5秒の呼び出しに対して0.009% | オフ |
| ツール実行前フックゲート(ウォームキャッシュ) | ゲート対象のツール呼び出し1回あたり**+44ミリ秒**、インタープリタの36ミリ秒フロアに上乗せ | オフ |
| エンフォースメントプロキシ | LLM呼び出し1回あたり**+9.7ミリ秒** | オフ |

デーモンのホストコスト: 取り込みが**毎秒2,762イベント**、ディスク上で**イベントあたり710バイト**(10万イベントあたり67.7MB)、そして稼働中のインストールで**1コアの約12%**を持続的に消費します。この最後の数字は、私たち自身が掲げる5〜10%の予算を超えているため、ページから外すのではなく、追いかけるべきバグとして公開しています。

Apple M2 Proで`benchmarks/overhead.py`により計測。このハーネスは各条件を別プロセスで実行し、実行順序を入れ替え、**ラウンド間で符号が一致しない場合は数値を出力しません**。ご自身のマシンでも1分で実行できます。

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートやエンフォースメントプロキシを含め、すべてのパスが計測対象であり、ハーネスはLinux、macOS、WindowsでCI上で実行されます。知っておく価値のある結果が2つあります — プロキシのコストはWindowsではLinuxの約7倍かかること、そしてデーモンは現在1コアの約12%を持続的に消費しており、これは私たち自身が掲げる5〜10%の予算を超えているということです。生のJSON、計測方法、そしてまだ計測されていない部分は[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 価格

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外のすべてのランタイム、フリートビュー、クラウド同期 | $9 / ノード / 月 |
| **Pro** | Starter + 制御と評価: 承認、ツールリスクポリシー、評価(evals)、異常検知、コストオプティマイザー、OTelエクスポート、改ざん検知監査ログ | $19 / ノード / 月 |

年間プラン、Enterprise、最新の価格は**[clawmetry.com/pricing](https://clawmetry.com/pricing)**にあります。セルフホストのライセンスキーはクラウドなしで動作します(`clawmetry license`)。無料/有料の正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)にあります。

## あなたのデータはあなたのマシンにとどまります

ClawMetryはローカルのセッションファイルとログを読み取ります。**`clawmetry connect`を実行しない限り、セッションデータがあなたのマシンから出ていくことはありません** — プロンプト、応答、ツール引数、ファイル内容、ログ行のいずれも送信されません。接続した場合でも、スナップショットはあなたのマシンから外に出ることのない鍵でエンドツーエンド暗号化され、ブラウザ内で復号されます。ノードに鍵がない場合、アップロードは平文で送信されるのではなくスキップされ、どのサーバーからの応答もこれを解除することはできません。

接続前にもデフォルトで実行される2つの通信があり、いずれもオプトアウト可能でセッションデータは含みません — 匿名のインストールpingと、PyPIに対するバージョンチェックです。デフォルトのインストールでは、起動時のバナー行のために一度だけあなたのパブリックIPも照会します。すべての送信先、そこに含まれる内容、無効化する方法は[docs/EGRESS.md](docs/EGRESS.md)に一覧化されています。セルフホスト、リポイント済み、エアギャップ環境のインストールでは、任意の外部通信は一切発生しません。

復号処理はあなたのブラウザ内で、私たちが提供するコードによって行われます。かつてはそれは約束にすぎませんでしたが、今では確認できるものになっています。あなたの鍵に触れるすべてのコードは1つの読みやすいファイル、[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)に収められており、これはwheelの中に同梱され、そのまま配信され、Subresource Integrityハッシュでピン留めされています。ブラウザが実際に私たちが公開したものを実行しているかを確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これが証明しないこと: 私たちはそのファイルを読み込むページ自体も配信しているため、別のページを配信することも可能です。Integrityハッシュはあなたを侵害されたCDNから守るものであり、ベンダー自身から守るものではありません。得られるのは、いかなる差し替えも意図的でなければならず、ページソース上で目に見え、誰でも取得できるPyPI上の成果物とは異なるものになる、ということです。セルフホストまたはローカルのみで運用すれば、この依存関係自体をなくすことができます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、WindowsでPython 3.8以降が必要で、同じマシン上に少なくとも1つのエージェントランタイムが必要です。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

あるいはエージェントにセットアップさせることもできます。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)スキルは、Claude Code、Codex、Cursor、Gemini CLI、CopilotまたはOpenCodeに、ClawMetryのインストール、マシン上のエージェントが何をしていくら使っているかの報告、要求に応じたセッションの停止、承認待ちとしてリスクのあるツール呼び出しを保留することを教えます。

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが読み取る内容、およびランタイムの追加方法 |
| [コンテキストの逼迫](docs/CONTEXT_BLOWOUT.md) | プロバイダーごとのウィンドウ、圧縮とオーバーフローの区別、ランタイムごとのカバレッジ |
| [オーバーヘッド](docs/OVERHEAD.md) | 計装にかかる実測コストと、それを再現するためのハーネス |
| [権限(Entitlements)](docs/ENTITLEMENTS.md) | 無料と有料の違い、ティア表、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォンでの承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | トレースをどこへでもエクスポートし、あらゆるものからOTLPを取り込む |
| [自前のエージェントを持ち込む](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChainをエンドツーエンドで、実行可能な例付きで |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自分で構築したエージェントのコスト帰属 |
| [チャットチャンネル](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み。ソースからの実行方法 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動ping、そしてその無効化方法 |

## スクリーンショット

以下の数値はすべて、何も仕込まれていない実マシンから読み取り専用で取得した実データです。

**何かが起きた時だけでなく、問題が起きていることを教えてくれます。**
上部に2つの異常バナー: 支出が日次平均の7倍で推移していること、4.2倍のコスト急増があったこと。その下には、直近667セッションのうち324件が、原因別に分類された無駄シグナルを持っていることが表示されています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこに使われたかを、あらゆる期間で示します。**
今日の$252.47、今週の$513.15、今月の$1,312.92、それぞれ背後にあるトークン数と、サブスクリプションがすでにカバーしている割合とともに表示されます。その下には、回収可能と分類された約$1,128/月と、キャッシュ再利用によってすでに節約された$17,256/月が内訳付きで示されています。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージがどのように回答になるかを描き出します。**
ライブフローダイアグラム: あなた、メッセージが届いたチャンネル、ゲートウェイ、現在応答しているモデル、そしてそれが呼び出したすべてのツール。作業が進むにつれてノードが点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを、一つのテーブルに。**
実行内容、直近24時間と累計のコスト、最終確認日時、所有者、サブスクリプションが費用をカバーしているかどうか。ここには14のエージェント、稼働中の3セッション、静止中の13セッションが表示されています。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とコストがどこに費やされたかを、ツールごとに示します。**
実際のセッションの1ターン: 11.2分で11個のツールを使い$1.16。すべてのBash呼び出しとモデル呼び出しがタイムライン上に自分のバーを持つため、4.1分かかったコマンドと226ミリ秒で終わったコマンドを一目で見分けられます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、作業の質を評価します。**
今週の評価はA: 54件のタスクがクリーンに完了し、2件の粗い実行に$48.57かかり、判断するには活動量が少なすぎる実行は成功として数えるのではなく評価から除外されています。粗い実行はそれぞれトレースにリンクしています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**コンテキストウィンドウが埋まり続ける理由を示します。**
直近のターンで1Mトークンウィンドウのうち715K、ピーク83.3%、いずれもオーバーフローではなく事前に発火した4回の圧縮、そしてその背後にあるすべてのターンの利用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**何も設定しなくても検知が動作します。**
組み込みの検知機能はインストール直後からオンです: エージェントの応答停止、テレメトリフィードの停止、コスト急増、トークンバースト、エラー増加、エラー急増、予算しきい値、脅威シグネチャの一致、セキュリティツールの検出結果、セキュリティ姿勢の変化。独自のルールはこれに加えて任意で設定できます。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しを保留するのはオプトインで、初期状態ではオフになっています。**
再帰的な削除、強制プッシュ、sudo、シークレット、パッケージインストール、外部通信のそれぞれに、オンにできるルールがあります。オンにするまでは、ClawMetryは監視するだけで何も変更しません。一度オンにすると、一致する呼び出しはここで(またはスマートフォンで)承認または拒否されるまで待機します。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとの詳細はこちら: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## 受賞歴

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

MIT · [@vivekchand](https://github.com/vivekchand)によって構築 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
