<!-- i18n-src:d21bea5161e0 -->
> 日本語 translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**エージェントの思考を見る。** **30種類のAIエージェントランタイム**向けのリアルタイム可観測性ツールです: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他26種類。エージェントフリート全体を1つのダッシュボードで確認できます。

> 🌐 **他言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定不要で、すでにお使いのエージェントランタイムを見つけ出し、読み取り専用でそれらを読み込みます。動作自体には一切変更を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30種類のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで対応:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数のランタイムを同時に実行している場合、ヘッダーのスイッチャーですべてのタブをそのランタイムに切り替えられます。

SDKを使って独自のエージェントを構築した場合も、インターセプターがそのLLM呼び出しを追跡します。詳しくは[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## できること

- **セッションとトランスクリプト**: 各エージェントがターンごとに何を行ったか、リプレイ付きで確認
- **コストとトークン**: ランタイム、モデル、セッション、日単位で集計し、異常フラグ付き
- **フロー**: チャネル、モデル、ツールを通過するメッセージのライブダイアグラム
- **Brain**: 推論とツール呼び出しのイベントストリームをリアルタイムで表示
- **コンテキストブローアウト**: プロバイダーごとにサイズ調整されたウィンドウ利用率、コンパクションと強制オーバーフローの区別、さらにランタイムごとに「見えない部分」を可視化するマップ([詳細](docs/CONTEXT_BLOWOUT.md))
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レートリミット、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインなどをSlack、Discord、PagerDuty、Telegram、Emailにルーティング
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認([詳細](docs/APPROVALS.md))

## コンテキストブローアウトと、監視にかかるコスト

どのエージェント比較ツールを信頼するかを決める前に、答えておく価値のある2つの疑問があります。

**ランタイムをまたいだコンテキストウィンドウのブローアウトをどう扱っているか?**

利用率のパーセンテージは、何で割っているかが誠実でなければ意味がありません。ClawMetryは、[誰でも読んでPRできるテーブル](clawmetry/context_windows.py)を使い、Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMを網羅したうえで、プロバイダーごとにウィンドウサイズを決定します。26種類すべてのランタイムを1社のものさしで測ることはしません。これは重要なポイントです。300KトークンのGPT-5のターンをAnthropicの200Kの基準で採点すると「100%超、破綻」と表示されますが、実際にはGPT-5の400Kウィンドウの75%に過ぎません。同じものさしでは、実際にオーバーフローしている130KのDeepSeekのターンが、快適な65%として隠されてしまいます。

すべてのウィンドウには、その出所として `model_table`、`explicit_marker`、`observed_floor`、あるいはモデルが不明な場合は正直に `default` のいずれかが付与されます。推測に基づくゲージが、ルックアップに基づくゲージと同じ権威を持って表示されることはありません。

ClawMetryはランタイムによってはコンパクションイベントの一部しか見えません。そのため `GET /api/context-coverage` は、ランタイムごとに**ゼロが「問題なく実行された」ことを意味するのか、「見えていない」ことを意味するのか**を報告します。実際には見えていないだけの `0` は、そのように明記されます。[詳細はこちら](docs/CONTEXT_BLOWOUT.md)

**計測自体にどれだけコストがかかるか?**

| パス | エージェントへの追加負荷 | デフォルト? |
|---|---|---|
| セッションファイルのテーリング (全30ランタイム) | **0**。別プロセスで動作し、エージェント側にClawMetryのコードは含まれない | オン |
| HTTPインターセプター (`CLAWMETRY_INTERCEPT=1`) | LLM呼び出し1回あたり**+0.44ms**、5秒の呼び出しに対して0.009% | オフ |
| プリツールフック・ゲート (ウォームキャッシュ時) | ゲート対象のツール呼び出し1回あたり**+44ms**、インタープリターの床値36msに追加 | オフ |
| エンフォースメントプロキシ | LLM呼び出し1回あたり**+9.7ms** | オフ |

デーモンのホストコスト: 取り込みで**毎秒2,762イベント**、ディスク上で**1イベントあたり710バイト**(10万イベントあたり67.7MB)、稼働中のインストールで持続的に**1コアの約12%**。この最後の数字は自分たちが掲げている5〜10%の予算を超えており、ページから外すのではなく、追いかけるべきバグとして公開しています。

Apple M2 Proで `benchmarks/overhead.py` を使って計測しました。このハーネスは各条件を別プロセスで実行し、実行順序を入れ替え、**ラウンド間で符号が一致しない場合は数値を出力しません**。自分のマシンで1分もかからず実行できます。

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートやエンフォースメントプロキシを含め、すべてのパスが計測されており、このハーネスはCI上でLinux、macOS、Windowsで実行されています。知っておく価値のある2つの結果: プロキシのコストはLinuxよりWindowsの方が約7倍高いこと、そしてデーモンは現在1コアの約12%を持続的に消費しており、自分たちが掲げる5〜10%の予算を超えていることです。生のJSON、計測方法、まだ計測できていない部分は[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 料金

| プラン | カバー範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外の全ランタイム、フリートビュー、クラウド同期 | ノードあたり月額$9 |
| **Pro** | Starter + 制御と評価: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート、改ざん検知監査ログ | ノードあたり月額$19 |

年間プラン、Enterprise、最新の価格は
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** に掲載されています。セルフホスト版のライセンス
キーはクラウドなしでも動作します(`clawmetry license`)。無料/有料の正確な区分は
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)に記載されています。

## データはあなたのマシンに留まります

ClawMetryはローカルのセッションファイルとログを読み取ります。**`clawmetry connect` を実行しない限り、
セッションデータがあなたのマシンから出ることはありません** — プロンプト、返信、ツールの引数、ファイル
内容、ログ行なども含まれません。接続した場合でも、スナップショットはあなたのマシンから出ることのない
鍵でエンドツーエンド暗号化され、ブラウザ側で復号されます。ノードに鍵がない場合、アップロードは平文で
送信されるのではなくスキップされ、この挙動をサーバー側のレスポンスで無効化することはできません。

接続前でもデフォルトで動作する2つの通信があります。どちらもオプトアウト可能で、セッションデータは
含まれません: 匿名のインストールping、およびPyPIに対するバージョンチェックです。デフォルトのインストール
では、起動時のバナー表示のためにパブリックIPも一度だけ照会されます。それぞれの送信先、含まれる内容、
無効化する方法はすべて[docs/EGRESS.md](docs/EGRESS.md)に記載されています。セルフホスト、リポイント、
エアギャップ環境のインストールでは、任意の外向き通信は一切発生しません。

復号処理は、私たちが配信するコードを使ってあなたのブラウザ内で行われます。かつてはそれは単なる約束
でしたが、今では確認可能なものになっています。あなたの鍵に触れるすべての行は、ホイールに同梱され、
Subresource Integrityハッシュで固定された状態でそのまま配信される、可読な1つのファイル
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)にあります。ブラウザが私たちの公開した
ものを実行していることを確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これで証明できないこと: 私たちはそのファイルを読み込むページ自体も配信しているため、異なるページを
配信することも可能ではあります。整合性ハッシュは、侵害されたCDNからは保護しますが、開発元自体からは
保護しません。得られるのは、いかなる差し替えも意図的でなければならず、ページソース上で可視化され、
誰でも取得できるPyPI上の成果物とは異なるものになる、という点です。セルフホストまたはローカル限定運用
にすれば、この依存関係自体をなくすことができます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、Windowsで Python 3.8以上が必要で、同じマシン上に少なくとも1つのエージェントランタイムが
必要です。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが読み取る内容と、ランタイムを追加する方法 |
| [コンテキストブローアウト](docs/CONTEXT_BLOWOUT.md) | プロバイダーごとのウィンドウ、コンパクション対オーバーフロー、ランタイムごとのカバレッジ |
| [オーバーヘッド](docs/OVERHEAD.md) | 計測にかかるコストと、それを再現するためのハーネス |
| [Entitlements](docs/ENTITLEMENTS.md) | 無料と有料の区分、ティア一覧表、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォンでの承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | どこへでもトレースをエクスポートし、どこからでもOTLPを取り込む |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自作エージェントのコスト帰属 |
| [チャットチャネル](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行方法 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動ping、その無効化方法 |

## スクリーンショット

以下の数値はすべて、シードなしの実際の1台のマシンから、読み取り専用で取得されたものです。

**問題が起きたことだけでなく、何かが「おかしい」ときにそれを教えてくれます。**
上部に2つの異常バナー: 支出が日次平均の7倍、コストが4.2倍に急増。その下には、直近667セッション中324
件が浪費シグナルを含んでおり、原因別に一覧化されています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこへ流れたかを、あらゆる期間で示します。**
今日$252.47、今週$513.15、今月$1,312.92。それぞれ背後にあるトークン数と、サブスクリプションで
既にカバーされている割合も表示されます。その下には、回収可能とされる約$1,128/月と、キャッシュ再利用
によって既に節約された$17,256/月が項目別に示されています。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージが答えになるまでの流れを描き出します。**
ライブフローダイアグラム: あなた、メッセージが届いたチャネル、ゲートウェイ、現在応答しているモデル、
そしてそのモデルが呼び出したすべてのツール。作業が進むにつれてノードが点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを1つの表で確認できます。**
実行内容、直近24時間および累計のコスト、最終確認時刻、所有者、サブスクリプションで支払いがカバーされて
いるかどうか。ここでは14エージェント中3セッションが稼働中、13が待機中です。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とコストがツールごとにどこへ使われたかを示します。**
実際のセッションの1ターン: 11.2分で11個のツールを使い、$1.16。すべてのBash呼び出しとモデル呼び出しが
タイムライン上で独自のバーを持つため、4.1分かかったコマンドと226msで終わったコマンドを一目で見分け
られます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、作業の質を評価します。**
今週の評価はA: 54件のタスクがクリーンに完了し、2件の粗い実行に$48.57かかりました。判断材料となる
活動が不足しているランがある場合、それらは勝ちとしてカウントされるのではなく評価から除外されます。
粗い実行はそれぞれトレースへのリンクが張られています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**なぜコンテキストウィンドウが埋まり続けるのかを示します。**
最新ターンで1Mトークンウィンドウのうち715K使用、ピーク83.3%、4回のコンパクションはすべてオーバー
フローではなくプロアクティブに発生。その背後にある各ターンの利用率も表示されます。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**設定なしで検知が動作します。**
組み込みの検知機能はインストール時からオンになっています: エージェントの無応答、テレメトリフィードの
停止、コスト急増、トークンバースト、エラー増加、エラー急増、予算閾値超過、脅威シグネチャの一致、
セキュリティツールの検出、セキュリティ体制の変化。独自ルールの追加はオプションです。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しの保留はオプトインで、デフォルトはオフです。**
再帰的な削除、強制プッシュ、sudo、シークレット、パッケージインストール、外向き通信のそれぞれに
オンにできるルールがあります。有効化するまで、ClawMetryは監視するだけで何も変更しません。有効化すると、
一致する呼び出しはここ(またはスマートフォン上)で承認または拒否を待ちます。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとのその他の情報: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · [@vivekchand](https://github.com/vivekchand)が開発 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
