<!-- i18n-src:9767c8001c9c -->
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

**エージェントの思考が見える。** **30種類のAIエージェントランタイム**をリアルタイムで観測: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他26種。エージェントフリート全体を1つのダッシュボードで。

> 🌐 **他の言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [その他 →](docs/i18n/)

コマンド一つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定不要で、すでにお使いのエージェントランタイムを見つけ出し、読み取り専用でアクセスし、動作には一切手を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30種類のエージェントランタイムに対応

**オープンソース版で無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで対応:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数を同時に実行すれば、ヘッダーのスイッチャーで各タブの対象を切り替えられます。

SDKで自作したエージェントの場合も、インターセプターがLLM呼び出しを追跡します。詳細は[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## できること

- **セッションとトランスクリプト**: 各エージェントが行ったことをターンごとに、リプレイ付きで確認
- **コストとトークン**: ランタイム、モデル、セッション、日別で集計し、異常検知フラグも表示
- **フロー**: チャネル、モデル、ツールを移動するメッセージのライブ図
- **ブレイン**: 発生した推論とツール呼び出しのイベントストリームをそのまま表示
- **コンテキストの逼迫**: プロバイダーごとに正しくサイズ計算したウィンドウ使用率、圧縮と強制オーバーフローの区別、さらにランタイムごとに「見えていない部分」のマップ([詳細](docs/CONTEXT_BLOWOUT.md))
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフラインを検知し、Slack、Discord、PagerDuty、Telegram、メールへルーティング
- **承認**: リスクのあるツール呼び出しを実行*前*に一時停止し、スマートフォンから承認([詳細](docs/APPROVALS.md))

## コンテキストの逼迫と、監視にかかるコスト

どんなエージェント比較ツールを信頼するかを決める前に、答えておく価値のある2つの問いです。

**ランタイムをまたいだコンテキストウィンドウの逼迫をどう扱うか?**

利用率という数値は、その分母が正しくなければ意味がありません。ClawMetryは[誰でも読んでPRできる表](clawmetry/context_windows.py)をもとに、プロバイダーごとにウィンドウサイズを算出します。対象はAnthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMです。26種類のランタイム全部を、1社の物差しで測ることはしません。これは重要な点です。300KトークンのGPT-5ターンをAnthropicの200Kという物差しで測ると「100%超え、逼迫」と表示されますが、実際にはGPT-5の400Kウィンドウの75%にすぎません。同じ物差しでは、実際にオーバーフローしている130KのDeepSeekターンが、余裕のある65%として隠れてしまいます。

すべてのウィンドウには出所が付きます: `model_table`、`explicit_marker`、`observed_floor`、あるいはモデルが分からない場合は正直に`default`と表示されます。推測に基づくゲージが、実際の参照表に基づくものと同じ権威を持って表示されることはありません。

ClawMetryが圧縮イベントを確認できるのは一部のランタイムのみです。そのため`GET /api/context-coverage`は、ランタイムごとに、**「0」が「正常に完了した」ことを意味するのか、それとも「見えていない」ことを意味するのか**を報告します。実際は見えていないだけの「0」は、そう明記されます。[詳細はこちら](docs/CONTEXT_BLOWOUT.md)

**計装のコストはどれくらいか?**

| 経路 | エージェントへの追加コスト | デフォルトか? |
|---|---|---|
| セッションファイルのtail監視(全30ランタイム) | **0**。別プロセスで動作し、ClawMetryのコードはエージェント内に一切入らない | オン |
| HTTPインターセプター(`CLAWMETRY_INTERCEPT=1`) | LLM呼び出し1回あたり**+0.44ミリ秒**(5秒の呼び出しの0.009%) | オフ |
| ツール実行前フック(ウォームキャッシュ時) | ゲート対象のツール呼び出し1回あたり**+44ミリ秒**(インタープリタの下限36ミリ秒に加えて) | オフ |
| 強制プロキシ | LLM呼び出し1回あたり**+9.7ミリ秒** | オフ |

デーモンのホストコスト: 取り込みは**毎秒2,762イベント**、ディスク上は**1イベントあたり710バイト**(10万イベントあたり67.7MB)、そして稼働中のインストールで持続的に**1コアの約12%**を消費します。この最後の数値は、当プロジェクトが掲げる5〜10%の予算を超えているため、隠さずに「追いかけるべきバグ」として公開しています。

Apple M2 Proで`benchmarks/overhead.py`を使って計測しています。このハーネスは各条件を別プロセスで実行し、実行順序を入れ替え、**ラウンド間で符号が一致しない数値は出力しません**。自分のマシンでも1分で実行できます。

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートや強制プロキシも含め、すべての経路が計測対象で、このハーネスはCI上でLinux、macOS、Windowsで実行されます。知っておく価値のある2つの結果: プロキシのコストはWindowsでLinuxの約7倍かかること、そしてデーモンは現在1コアの約12%を持続的に消費しており、これは当プロジェクト自身が掲げる5〜10%の予算を超えていることです。生のJSON、計測方法、そしてまだ計測されていない項目は[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 価格

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外のすべてのランタイム、フリートビュー、クラウド同期 | ノードあたり月額$9 |
| **Pro** | Starterに加えて制御と評価: 承認、ツールリスクポリシー、評価、異常検知、コストオプティマイザー、OTelエクスポート、改ざん検知可能な監査ログ | ノードあたり月額$19 |

年間プラン、Enterpriseプラン、最新の価格は
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**にあります。セルフホスト用のライセンス
キーはクラウドなしでも動作します(`clawmetry license`)。無料/有料の正確な区分は
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)にあります。

## データはあなたのマシンから出ません

ClawMetryはローカルのセッションファイルとログを読み取ります。**`clawmetry connect`を実行しない限り、セッションデータがあなたのマシンから外に出ることはありません**。プロンプト、返信、ツールの引数、ファイル内容、ログ行のいずれも送信されません。接続した場合も、スナップショットはあなたのマシンから外に出ない鍵でエンドツーエンド暗号化され、ブラウザ上で復号されます。ノードに鍵がない場合、アップロードは平文で送信されるのではなくスキップされ、この動作をサーバー側からオフにすることはできません。

接続前でもデフォルトで動作するものが2つありますが、いずれもオプトアウト可能で、セッションデータは一切含みません。匿名のインストールピングと、PyPIに対するバージョンチェックです。デフォルトのインストールでは、起動時バナーの1行のためにパブリックIPを一度だけ調べます。それぞれの送信先、内容、無効化の方法はすべて
[docs/EGRESS.md](docs/EGRESS.md)に記載されています。セルフホスト、送信先を変更した構成、エアギャップ環境でのインストールでは、任意の外部通信は一切発生しません。

復号はブラウザ内で、こちらが配信するコード上で行われます。これは以前は「約束」でしたが、今では確認できるものになりました。あなたの鍵に触れるすべての行は1つの読みやすいファイル、
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)にまとまっており、
これはwheelに同梱されてそのまま配信され、Subresource
Integrityハッシュで固定されています。ブラウザが実際に公開版と同じものを実行しているか確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これで証明できないこと: ファイルを読み込むページ自体はこちらが配信しているため、別のページを配信することも可能ではあります。Integrityハッシュが守ってくれるのは、CDNが侵害された場合であって、配信元自体からではありません。得られるのは、差し替えを行うなら意図的かつページのソース上で可視な形で行う必要があり、しかも誰でも取得できるPyPI上の成果物とは異なる内容になるということです。セルフホストまたはローカル運用に留めれば、この依存関係自体をなくせます。

## インストール

```bash
pip install clawmetry     # then: clawmetry
```

またはワンライナーで: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、Windowsで Python 3.8以上が必要で、同じマシン上に少なくとも1つのエージェントランタイムが動作している必要があります。Dockerでの手順: [docs/DOCKER.md](docs/DOCKER.md)。

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが何を読み取るか、新しいランタイムの追加方法 |
| [コンテキストの逼迫](docs/CONTEXT_BLOWOUT.md) | プロバイダー別のウィンドウ、圧縮とオーバーフローの区別、ランタイムごとのカバレッジ |
| [オーバーヘッド](docs/OVERHEAD.md) | 計装のコストを実測し、再現用ハーネスも公開 |
| [権限(Entitlements)](docs/ENTITLEMENTS.md) | 無料と有料の区分、ティア表、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォン承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | トレースをどこへでもエクスポート、どこからでもOTLPを取り込み |
| [自作エージェントを持ち込む](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChainを実行例付きで一通り解説 |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自作エージェントのコスト帰属 |
| [チャットチャネル](docs/CHANNELS.md) | フローに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawの構成 |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行方法 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動ピング、その無効化方法 |

## スクリーンショット

以下の数値はすべて、何も仕込んでいない実際の1台のマシンから、読み取り専用で取得したものです。

**単なる出来事の記録ではなく、何がおかしいかを教えてくれます。**
上部に2つの異常検知バナー: 支出が日次平均の7倍で推移していること、そして4.2倍のコスト急増。その下には、直近667セッションのうち324セッションに無駄の兆候があり、原因別に一覧表示されています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこへ流れたかを、あらゆる期間で示します。**
今日は$252.47、今週は$513.15、今月は$1,312.92で、それぞれ背後のトークン数とサブスクリプションでカバー済みの割合が付きます。その下には、回収可能な支出として月額約$1,128、キャッシュ再利用ですでに節約された月額$17,256が項目別に表示されます。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージが回答になるまでの流れを描きます。**
ライブフロー図: あなた、メッセージが届いたチャネル、ゲートウェイ、現在応答しているモデル、そして呼び出されたすべてのツール。処理が通過するたびにノードが点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを、1つの表にまとめます。**
何を実行しているか、直近24時間と累計でいくらかかっているか、最後に確認された時刻、所有者、そしてサブスクリプションでカバーされているかどうか。ここでは14個のエージェントのうち3セッションが稼働中、13個が待機中です。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とコストが、ツールごとにどこへ費やされたかを示します。**
実際のセッションの1ターン: 11個のツールを11.2分かけて実行し、$1.16。それぞれのBash呼び出しとモデル呼び出しがタイムライン上に独自のバーを持つため、4.1分かかったコマンドと226ミリ秒で終わったコマンドを一目で見分けられます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、作業そのものを評価します。**
今週の評価はA: 54件のタスクがきれいに完了し、荒れた2件には$48.57かかり、判断材料となる活動量が不足しているものは、勝ちとしてカウントされるのではなく評価対象から除外されます。荒れた各実行はそのトレースにリンクしています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**コンテキストウィンドウがなぜ埋まっていくのかを示します。**
最新ターンで1Mトークンのウィンドウのうち715Kを使用、ピーク使用率83.3%、4回の圧縮はすべてオーバーフローではなく事前に発動しており、その背後にある各ターンの利用率も表示されます。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**検知は、何も設定しなくても動作します。**
インストール直後から有効な組み込み検知項目: エージェントの沈黙、テレメトリフィードの停止、コスト急増、トークンバースト、エラー増加、エラー急増、予算しきい値、脅威シグネチャの一致、セキュリティツールの検知結果、セキュリティ姿勢の変化。独自ルールは、その上にオプションで追加できます。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しの保留はオプトイン方式で、デフォルトではオフで出荷されます。**
再帰的な削除、強制プッシュ、sudo、シークレット、パッケージインストール、外部呼び出しには、それぞれオンにできるルールがあります。オンにするまでは、ClawMetryは監視するだけで何も変更しません。一度オンにすると、該当する呼び出しはここで(またはスマートフォン上で)承認または拒否を待ちます。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとのより詳しいスクリーンショット: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## スター履歴

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · 開発: [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
