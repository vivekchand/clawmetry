<!-- i18n-src:a855a14295b0 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**エージェントは、進捗を何ひとつ生まないまま100回ツールを呼び出すことがあります。** ClawMetryは、あなたのコーディングエージェントがすでに書き出しているセッションファイルを読み込み、タイムライン、ツール呼び出し、そしてランタイムが公開しているトークン・コストデータを1つのビューにまとめます。これにより、うまく進んでいる長時間の実行と、行き詰まっている実行を見分けられるようになります。

**32のAIエージェントランタイム**に対応 — Claude Code、OpenAI Codex、Hermes、OpenClaw、その他28種。あなたのエージェント群全体を1つのダッシュボードで。(カタログから生成される[全リスト](SUPPORTED_RUNTIMES.txt))

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [その他 →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定不要で、すでに手元にあるエージェントランタイムを見つけ出し、読み取り専用でアクセスし、実行方法には一切手を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## インストール前に

| | |
|---|---|
| **何をするか** | あなたのエージェントがすでに書き出しているセッションファイルとログを読み込みます。SDKもコード変更も、アプリへの計測コードの組み込みも不要です。 |
| **何が見えるか** | セッションのタイムライン、ツール単位のリプレイ、トークンとコストの内訳、そして軌跡シグナル(ループ、繰り返しの失敗)がランタイムごとに表示されます。 |
| **何が無料か** | `pip install clawmetry` は、アカウントもキーもネットワーク通信も不要で**OpenClaw、NVIDIA NemoClaw、Goose**を読み込みます。それ以外の27種 — Claude Code、Codex、Cursorなど — は、クローズドソースの`clawmetry-pro`コンパニオンによって読み込まれ、7日間のトライアルまたはプランに付属します。詳しい振り分けは[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)を参照してください。 |
| **始め方** | `pip install clawmetry && clawmetry` を実行し、localhost:8900を開くだけです。このマシンにまだエージェントがない場合は、`clawmetry --sample` でラベル付きの合成セッション3つを表示できます。 |
| **マシンの外に出るもの** | `clawmetry connect` を実行しない限り、セッションデータは一切出ていきません。デフォルトで動作するものが2つあり、どちらもオプトアウト可能で、セッション内容は含みません — 匿名のインストールping、そしてPyPIバージョンチェックです。すべての送信先は[docs/EGRESS.md](docs/EGRESS.md)に、コメントを読むのではなくワイヤーキャプチャから再構築した形で一覧化されています。 |

出力を評価する前に知っておくべき制約が2つあります。ランタイムごとに公開されるデータはまったく異なり(コストを一切公開しないものもあります — [その一覧](docs/compatibility.md)にランタイムごとの詳細があります)、また行動を観測できることと、それを止められることは同じではありません([ランタイムごとにどの制御が実際に機能するか](docs/APPROVALS.md))。


## 32のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数を同時に実行すると、ヘッダーのスイッチャーがすべてのタブを1つのランタイムに合わせて切り替えます。

自前でSDKからエージェントを構築した場合はどうなるでしょうか。インターセプターがそのLLM呼び出しも追跡します。詳しくは[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## 何が得られるか

- **セッションとトランスクリプト**: 各エージェントがターンごとに何をしたか、リプレイ付きで
- **コストとトークン**: ランタイム、モデル、セッション、日単位で、異常フラグ付き
- **フロー**: チャネル、モデル、ツールの間をメッセージが移動していく様子のライブ図
- **ブレイン**: 推論とツール呼び出しのイベントストリームをリアルタイムで
- **コンテキストブロウアウト**: プロバイダーごとにサイズ調整されたウィンドウ使用率、圧縮と強制オーバーフローの比較、そして「見えないもの」のランタイムごとのマップ([詳細](docs/CONTEXT_BLOWOUT.md))
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レートリミット、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインをSlack、Discord、PagerDuty、Telegram、Eメールへ
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認([詳細](docs/APPROVALS.md))

## コンテキストブロウアウトと、監視にかかるコスト

どのエージェント比較ツールを信頼するかを決める前に、答えておくべき問いが2つあります。

**ランタイムをまたいだコンテキストウィンドウのブロウアウトをどう扱うか?**

使用率のパーセンテージは、それが何を分母にしているかによってしか正直になれません。ClawMetryは、[読んでPRできるテーブル](clawmetry/context_windows.py)からプロバイダーごとにウィンドウサイズを決めており、これはAnthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMをカバーしています。32のランタイムすべてを1社のものさしで測ることはしません。これは重要な違いです。300KトークンのGPT-5のターンをAnthropicの200Kで採点すると「100%超え、破綻」と読めますが、実際はGPT-5の400Kのうち75%にすぎません。同じものさしは、本当にオーバーフローした130KのDeepSeekターンを、余裕のある65%に見せかけてしまいます。

すべてのウィンドウには、その出所として`model_table`、`explicit_marker`、`observed_floor`、あるいはモデルが不明な場合は正直に`default`が付与されます。推測に基づくゲージが、ルックアップに基づくゲージと同じ権威を持つ見た目でレンダリングされることはありません。

ClawMetryが圧縮イベントを確認できるのは一部のランタイムに限られます。そのため`GET /api/context-coverage`は、ランタイムごとに**ゼロが「正常に完走した」を意味するのか、「見えていない」を意味するのか**を報告します。実際には見えていないだけの`0`は、その旨をはっきり示します。[詳細](docs/CONTEXT_BLOWOUT.md)

**計測にかかるコストは?**

| パス | あなたのエージェントへの追加分 | デフォルトか? |
|---|---|---|
| セッションファイルのtail読み(全32ランタイム) | **0**。別プロセスで動作し、あなたのエージェントにClawMetryのコードは一切入りません | オン |
| HTTPインターセプター(`CLAWMETRY_INTERCEPT=1`) | LLM呼び出し1回あたり**+0.44ms**、5秒の呼び出しの0.009% | オフ |
| ツール実行前フック(ウォームキャッシュ) | ゲートされたツール呼び出し1回あたり**+44ms**、インタプリタの36msという下限の上に | オフ |
| エンフォースメントプロキシ | LLM呼び出し1回あたり**+9.7ms** | オフ |

デーモンのホストコスト: 取り込み**2,762イベント/秒**、ディスク上**710バイト/イベント**(10万イベントあたり67.7MB)、稼働の激しいインストールで持続的に**1コアの約12%**。この最後の数字は、私たち自身が掲げた5〜10%の予算を超えているため、ページから隠さず、追いかけるべきバグとして公開しています。

Apple M2 Proで`benchmarks/overhead.py`を使って計測しています。このハーネスは各条件を別プロセスで実行し、実行順序を入れ替え、**ラウンド間で符号が一致しない場合は数値を出力しません**。自分のマシンで1分もあれば実行できます。

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートやエンフォースメントプロキシを含め、すべてのパスが計測されており、ハーネスはCI上でLinux、macOS、Windowsで実行されます。知っておく価値のある結果が2つあります。プロキシはWindowsではLinuxのおよそ7倍のコストがかかること、そしてデーモンは現在1コアの約12%を持続的に消費しており、これは私たち自身が掲げた5〜10%の予算を超えているということです。生のJSON、計測方法、そしてまだ計測できていないものは[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 料金

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外のすべてのランタイム、フリートビュー、クラウド同期 | ノードあたり月$9 |
| **Pro** | Starter + 制御と評価: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート、改ざん検知監査ログ | ノードあたり月$19 |

年間プラン、Enterprise、最新の料金は**[clawmetry.com/pricing](https://clawmetry.com/pricing)**にあります。セルフホスト型のライセンスキーはクラウドなしでも動作します(`clawmetry license`)。無料/有料の正確な線引きは[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)にあります。

## データはあなたのマシンにとどまります

ClawMetryはローカルのセッションファイルとログを読み込みます。**`clawmetry connect`を実行しない限り、セッションデータがあなたのマシンから出ていくことはありません** — プロンプト、返信、ツールの引数、ファイル内容、ログ行のいずれもです。接続した場合でも、スナップショットはマシンから一切出ないキーでエンドツーエンド暗号化され、あなたのブラウザ内で復号されます。ノードにキーがない場合、アップロードは平文で送られるのではなくスキップされ、サーバー側のいかなる応答もこれを無効化することはできません。

接続前でもデフォルトで動作するものが2つあり、どちらもオプトアウト可能で、セッションデータは含みません — 匿名のインストールpingと、PyPIに対するバージョンチェックです。デフォルトのインストールでは、起動時のバナー表示のために公開IPアドレスを一度だけ調べます。すべての送信先、そこに含まれる内容、そして無効化する方法は[docs/EGRESS.md](docs/EGRESS.md)に一覧化されています。セルフホスト、リポイント、エアギャップされたインストールでは、任意送信の通信は一切発生しません。

復号はあなたのブラウザ内で、私たちが提供するコードによって行われます。かつてはそれが単なる約束でしたが、今では検証可能なものになっています。あなたのキーに触れる行はすべて1つの読みやすいファイル[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)にまとまっており、これはwheelの中に同梱されてそのまま配信され、サブリソース整合性(Subresource Integrity)ハッシュで固定されています。ブラウザが実際に私たちの公開したものを実行しているか確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これで証明されないこともあります。ファイルを読み込むページ自体を私たちが配信しているため、別のページを配信することも理論上は可能です。整合性ハッシュはCDNが侵害された場合からあなたを守りますが、提供元自身から守るものではありません。得られるのは、いかなる差し替えも意図的であり、ページソース上で可視であり、そして誰でも取得できるPyPI上の成果物とは異なる、という保証です。セルフホストまたはローカル限定運用にすれば、この依存関係自体をなくすことができます。

## インストール

```bash
pip install clawmetry     # 続けて: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、WindowsでPython 3.8以上が必要で、同じマシン上に少なくとも1つのエージェントランタイムが必要です。Dockerでの手順は[docs/DOCKER.md](docs/DOCKER.md)にあります。

エージェントにセットアップを任せることもできます。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)スキルは、Claude Code、Codex、Cursor、Gemini CLI、Copilot、OpenCodeに対して、ClawMetryのインストール、マシン上のエージェントが何をしていくら使っているかの報告、リクエストに応じたセッションの停止、リスクのあるツール呼び出しの承認待ち保留を教えます。

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが何を読み込むか、ランタイムの追加方法 |
| [コンテキストブロウアウト](docs/CONTEXT_BLOWOUT.md) | プロバイダーごとのウィンドウ、圧縮とオーバーフローの比較、ランタイムごとのカバレッジ |
| [オーバーヘッド](docs/OVERHEAD.md) | 計測にかかるコスト、実測値、再現用ハーネス |
| [エンタイトルメント](docs/ENTITLEMENTS.md) | 無料 vs 有料、ティアマトリクス、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォンでの承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | どこへでもトレースをエクスポート、何からでもOTLPを取り込み |
| [自前のエージェントを持ち込む](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChainをエンドツーエンドで、実行可能なサンプル付き |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自分で構築したエージェントのコスト帰属 |
| [チャットチャネル](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行方法 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動pingと、その無効化方法 |

## スクリーンショット

以下の数値はすべて、何も仕込んでいない実際の1台のマシンから、読み取り専用で取得したものです。

**何かがうまくいっていないときに、それを教えてくれます。それだけでなく、何が起きたかも。**
上部に2つの異常バナー: 支出が日次平均の7倍で推移していること、そして4.2倍のコスト急増。その下には、直近667セッションのうち324セッションが無駄なシグナルを伴っており、原因別に内訳が示されています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこへ行ったかを、あらゆる期間で示します。**
今日$252.47、今週$513.15、今月$1,312.92、それぞれ背後のトークン数と、サブスクリプションがすでにカバーしている割合とともに。その下には、回収可能とされる約$1,128/月分の内訳と、キャッシュ再利用によりすでに節約された$17,256/月分。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージがどのように答えへと変わっていくかを描きます。**
ライブフロー図: あなた、メッセージが届いたチャネル、ゲートウェイ、今まさに応答しているモデル、そしてそのモデルが呼び出したすべてのツール。作業がそこを通過するたびにノードが点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを、1つのテーブルで。**
実行しているもの、直近24時間と生涯の合計コスト、最終確認日時、所有者、そしてサブスクリプションが料金をカバーしているかどうか。ここでは14のエージェント、3セッションが稼働中、13が待機中です。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とお金がどこへ行ったかを、ツールごとに示します。**
実際のセッションの1ターン: 11.2分で11個のツールを使い、$1.16。すべてのBash呼び出しとモデル呼び出しがタイムライン上に独自のバーを持つため、4.1分かかったコマンドと226msで終わったコマンドを一目で見分けられます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、成果そのものを評価します。**
今週の評価はA: 54件のタスクが問題なく完了し、2件の粗雑な実行に$48.57かかり、判断するには活動量が少なすぎる実行は成功としてカウントされず評価から除外されます。それぞれの粗雑な実行はそのトレースにリンクしています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**コンテキストウィンドウがなぜ埋まり続けるのかを示します。**
最新ターンで1Mトークンのウィンドウのうち715Kを使用、ピーク83.3%、オーバーフローではなくすべて予防的に発火した4回の圧縮、そしてその背後にあるすべてのターンの使用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**検知は、あなたが何も設定しなくても動作します。**
組み込みの検知器はインストール直後からオンです: エージェントが沈黙した、テレメトリフィードが停止した、コスト急増、トークンバースト、エラー増加、エラー急増、予算しきい値、脅威シグネチャの一致、セキュリティツールの検出、セキュリティ姿勢の変化。独自ルールはその上にオプションで追加できます。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しの保留はオプトインで、デフォルトではオフになっています。**
再帰的な削除、force push、sudo、シークレット、パッケージのインストール、送信通信のそれぞれに、オンにできるルールがあります。オンにするまで、ClawMetryは監視するだけで何も変更しません。1つでもオンにすると、該当する呼び出しはここ(またはあなたのスマートフォン)で承認または拒否を待ちます。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとの追加スクリーンショット: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)

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
