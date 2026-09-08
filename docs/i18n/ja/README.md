<!-- i18n-src:88be2deff5d5 -->
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

**エージェントの思考を見る。** **30種類のAIエージェントランタイム**向けのリアルタイム可観測性: [OpenClaw](https://github.com/openclaw/openclaw)、[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)、Claude Code、OpenAI Codex、その他26種類。エージェント群全体を1つのダッシュボードで。

> 🌐 **他の言語で読む:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

コマンド1つ。設定不要。すべて自動検出。

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** で開きます。設定不要: すでに使っているエージェントランタイムを見つけ、読み取り専用で読み込み、動作には一切手を加えません。

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30種類のエージェントランタイムに対応

**オープンソースアプリで無料:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**有料プランで対応:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

どのランタイムでも同じダッシュボードが使えます。複数を同時に実行すれば、ヘッダーのスイッチャーで各タブの対象を切り替えられます。

SDKで独自のエージェントを構築した場合も、インターセプターがそのLLM呼び出しを追跡します。詳細は[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)を参照してください。

## 得られるもの

- **セッションとトランスクリプト**: 各エージェントが何をしたか、ターンごとにリプレイ付きで
- **コストとトークン**: ランタイム、モデル、セッション、日ごとに、異常フラグ付きで
- **フロー**: チャンネル、モデル、ツールを通じて動くメッセージのライブ図
- **ブレイン**: 起きている推論とツール呼び出しのイベントストリーム
- **コンテキスト枯渇**: プロバイダごとにサイズ調整されたウィンドウ利用率、圧縮 vs 強制オーバーフロー、そして見えていない部分をランタイムごとにマップ化([方法](docs/CONTEXT_BLOWOUT.md))
- **メモリとスキル**: 各ランタイムが実際に読み込んだファイルとスキル
- **ヘルスとログ**: ディスク、メモリ、エラー率、レート制限、ライブログストリーム
- **アラート**: 予算上限、エラー急増、エージェントオフライン。Slack、Discord、PagerDuty、Telegram、Emailへ通知
- **承認**: リスクのあるツール呼び出しを実行**前**に一時停止し、スマートフォンから承認([方法](docs/APPROVALS.md))

## コンテキスト枯渇、そして監視にかかるコスト

どんなエージェント比較ツールを信頼する前にも答えておく価値がある2つの質問。

**ランタイムをまたいだコンテキストウィンドウの枯渇をどう扱っているか?**

利用率のパーセンテージは、何で割っているかが正直でなければ意味がありません。ClawMetryは、Anthropic、OpenAI、Google、xAI、DeepSeek、Kimi、Qwen、Mistral、Llama、GLMを対象に、読んでPRできる[1つのテーブル](clawmetry/context_windows.py)からプロバイダごとにウィンドウサイズを決めています。30種類すべてのランタイムを1社の物差しで測ることはしません。これは重要な点です。300KトークンのGPT-5のターンをAnthropicの200Kに照らして採点すると「100%超、枯渇」と表示されますが、実際にはGPT-5の400Kの75%にすぎません。同じ物差しは、実際にオーバーフローしている130KのDeepSeekのターンを、安心できる65%として隠してしまいます。

すべてのウィンドウには出所が付いています: `model_table`、`explicit_marker`、`observed_floor`、そしてモデルが分からない場合は正直な`default`。推測に基づくゲージが、参照に基づくものと同じ信頼度で表示されることはありません。

ClawMetryは一部のランタイムでしか圧縮イベントを見ることができません。そのため`GET /api/context-coverage`は、ランタイムごとに**0が「問題なく実行された」を意味するのか、それとも「見えていない」を意味するのか**を報告します。実際には見えていないことを意味する`0`は、その旨を報告します。[詳細](docs/CONTEXT_BLOWOUT.md)

**この計測にかかるコストは?**

| パス | あなたのエージェントへの追加分 | デフォルト? |
|---|---|---|
| セッションファイルのtail読み(全30ランタイム) | **0**。別プロセスで動作、あなたのエージェントにClawMetryのコードは入らない | on |
| HTTPインターセプター(`CLAWMETRY_INTERCEPT=1`) | LLM呼び出し1回あたり**+0.44 ms**、5秒の呼び出しの0.009% | off |
| 事前ツールフックゲート(ウォームキャッシュ) | ゲートされたツール呼び出し1回あたり**+44 ms**、インタプリタの床36 msに上乗せ | off |
| エンフォースメントプロキシ | LLM呼び出し1回あたり**+9.7 ms** | off |

デーモンのホストコスト: 取り込みで**2,762イベント/秒**、ディスク上で1イベントあたり**710バイト**(10万イベントあたり67.7 MB)、そして稼働の多いインストールで持続的に**1コアの約12%**。この最後の数字は自分たちが掲げた5〜10%の予算を超えているため、伏せておくのではなく、追いかけるべきバグとして公開しています。

Apple M2 Proで`benchmarks/overhead.py`を使って測定しました。このハーネスは各条件を別プロセスで実行し、順序を入れ替え、**ラウンド間で符号が食い違う場合は数値を出力しません**。自分のマシンで1分で実行できます。

```bash
pip install clawmetry && python -m benchmarks.overhead
```

フックゲートやエンフォースメントプロキシを含め、すべてのパスが計測されており、このハーネスはCI上のLinux、macOS、Windowsで動作します。知っておく価値のある結果が2つあります。プロキシはWindowsでLinuxの約7倍のコストがかかること、そしてデーモンは現在1コアの約12%を持続的に消費しており、自分たちの5〜10%の予算を超えていることです。生のJSON、手法、そしてまだ計測されていないものは[docs/OVERHEAD.md](docs/OVERHEAD.md)にあります。

## 料金

| プラン | 対象範囲 | 価格 |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose、フルダッシュボード、ローカルのみ | $0 |
| **Starter** | 上記以外の全ランタイム、フリートビュー、クラウド同期 | ノードあたり月$9 |
| **Pro** | Starter + 制御と評価: 承認、ツールリスクポリシー、評価、異常検知、コスト最適化、OTelエクスポート、改ざん検知監査ログ | ノードあたり月$19 |

年間プラン、Enterprise、最新の価格は**[clawmetry.com/pricing](https://clawmetry.com/pricing)**にあります。セルフホストのライセンスキーはクラウドなしでも機能します(`clawmetry license`)。無料/有料の正確な区分は[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)にあります。

## データはあなたのマシンに留まる

ClawMetryはローカルのセッションファイルとログを読み取ります。**`clawmetry connect`を実行しない限り、セッションデータがあなたのマシンから出ることはありません** —— プロンプト、返信、ツール引数、ファイル内容、ログ行のいずれも送信されません。接続すると、スナップショットはあなたのマシンから外に出ることのない鍵でエンドツーエンド暗号化され、ブラウザ内で復号されます。ノードに鍵がない場合、アップロードは平文で送信されるのではなくスキップされ、どんなサーバー応答もこれを解除することはできません。

接続前でもデフォルトで動作するものが2つあり、どちらもオプトアウト可能で、どちらもセッションデータを含みません: 匿名のインストールping と、PyPIに対するバージョンチェックです。デフォルトのインストールでは、起動時のバナー行のために公開IPを1回だけ調べます。すべての宛先、そこに含まれるもの、それを止める方法は[docs/EGRESS.md](docs/EGRESS.md)に記載されています。セルフホスト、宛先を変更したインストール、およびエアギャップ環境のインストールは、任意の外向き呼び出しを一切行いません。

復号処理は、私たちが提供するコードによってあなたのブラウザ内で行われます。これはかつては単なる約束でしたが、今では確認できることです。あなたの鍵に触れるすべての行は1つの読みやすいファイル、[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)にあり、これはwheelの中に同梱され、そのまま提供され、Subresource Integrityハッシュで固定されています。ブラウザが実際に公開されたものを実行しているかを確認するには:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

これが証明しないこと: 私たちはこのファイルを読み込むページ自体を配信しているため、別のページを配信することも可能です。整合性ハッシュはCDNの侵害からあなたを守るものであり、ベンダー自身から守るものではありません。得られるのは、いかなる差し替えも意図的で、ページソース上に見える形で行われ、誰でも取得できるPyPI上の成果物とは異なるものになる、ということです。セルフホスティングまたはローカル限定運用にすれば、この依存自体をなくせます。

## インストール

```bash
pip install clawmetry     # 続けて: clawmetry
```

またはワンライナー: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS、Linux、Windows上でPython 3.8+が必要で、同じマシン上に少なくとも1つのエージェントランタイムが必要です。Dockerの手順: [docs/DOCKER.md](docs/DOCKER.md)。

あるいはエージェントにセットアップさせることもできます。[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)スキルは、Claude Code、Codex、Cursor、Gemini CLI、Copilot、OpenCodeに、ClawMetryのインストール、マシン上のエージェントが何をして何を消費しているかの報告、要求に応じたセッション1つの停止、そして承認待ちのリスクあるツール呼び出しの保留を教えます。

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ドキュメント

| | |
|---|---|
| [ランタイム互換性](docs/compatibility.md) | 各アダプターが何を読み取るか、ランタイムを追加する方法 |
| [コンテキスト枯渇](docs/CONTEXT_BLOWOUT.md) | プロバイダごとのウィンドウ、圧縮 vs オーバーフロー、ランタイムごとのカバレッジ |
| [オーバーヘッド](docs/OVERHEAD.md) | 計測済みの計測コスト、再現用のハーネス付き |
| [権限](docs/ENTITLEMENTS.md) | 無料 vs 有料、ティアマトリクス、ライセンスCLI |
| [承認とポリシー](docs/APPROVALS.md) | 実行前ゲーティング、リスクスコアリング、スマートフォン承認 |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | どこへでもトレースをエクスポート、何からでもOTLPを取り込み |
| [自分のエージェントを持ち込む](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore、Pydantic AI、LangChainをエンドツーエンドで、実行可能な例付き |
| [SDKトラッキング](docs/SDK_TRACKING.md) | 自分で構築したエージェントのコスト帰属 |
| [チャットチャンネル](docs/CHANNELS.md) | Flowに表示されるチャットアダプター |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | サンドボックス化されたNVIDIA NemoClawのセットアップ |
| [Docker](docs/DOCKER.md) | イメージ、compose、ボリュームマウント |
| [アーキテクチャ](ARCHITECTURE.md) · [開発](docs/DEVELOPMENT.md) | 内部の仕組み、ソースからの実行 |
| [テレメトリ](docs/TELEMETRY.md) | 匿名のインストールおよびデスクトップ起動ping、そして無効化する方法 |

## スクリーンショット

以下の数値はすべて、何も仕込んでいない読み取り専用の実マシン1台から取得したものです。

**何かが問題であることを教えてくれる。単に何が起きたかだけではない。**
上部に2つの異常バナー: 支出が日次平均の7倍で推移していること、そして4.2倍のコスト急増。その下には、直近667セッションのうち324件が原因別に内訳された無駄シグナルを抱えています。

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**お金がどこへ行ったかを、あらゆる期間で見せてくれる。**
今日$252.47、今週$513.15、今月$1,312.92、それぞれの背後にあるトークン数と、サブスクリプションがすでにカバーしている分。その下には、約$1,128/月の回収可能分の内訳と、キャッシュ再利用によってすでに節約された$17,256/月。

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**メッセージがどう答えになるかを描く。**
ライブフロー図: あなた、メッセージが届いたチャンネル、ゲートウェイ、現在応答しているモデル、そしてそれが呼び出したすべてのツール。ノードは作業がそこを通るたびに点灯します。

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**マシン上のすべてのエージェントを1つの表に。**
それが何を実行し、直近24時間と生涯でいくらかかっているか、最後に確認されたのはいつか、誰が所有しているか、そしてサブスクリプションが料金をカバーしているかどうか。ここでは14のエージェント、稼働中3セッション、休止中13。

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**1ターンの時間とお金がどこへ行ったかを、ツールごとに見せてくれる。**
実際のセッションの1ターン: 11.2分で11個のツール、$1.16。すべてのBash呼び出しとモデル呼び出しがタイムライン上に独自のバーを持つため、4.1分かかったコマンドと226msで終わったコマンドを一目で見分けられます。

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**支出だけでなく、作業そのものを採点する。**
今週はA評価: 54件のタスクがクリーンに完了し、2件の粗い結果に$48.57かかり、判断するには活動量が少なすぎる実行は勝ちとしてカウントされる代わりに評価から除外されています。粗い実行はそれぞれ自分のトレースにリンクしています。

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**コンテキストウィンドウがなぜ埋まり続けるかを見せてくれる。**
最新ターンで100万トークンのウィンドウのうち71.5万トークン、ピーク83.3%、すべてオーバーフローではなく先回りで発火した4回の圧縮、そしてその背後にあるすべてのターンの利用率。

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**何も設定しなくても検知は動作する。**
組み込みの検知器はインストール時からオン: エージェントが静かになった、テレメトリフィードが停止した、コスト急増、トークンバースト、エラー増加、エラー急増、予算閾値、脅威シグネチャ一致、セキュリティツールの検出、セキュリティ姿勢の変化。独自ルールはその上にオプションで追加できます。

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**リスクのある呼び出しの保留はオプトインで、無効の状態で出荷される。**
再帰的な削除、フォースプッシュ、sudo、シークレット、パッケージインストール、そして外向きの呼び出しには、それぞれオンにできるルールがあります。有効にするまでは、ClawMetryは監視するだけで何も変更しません。1つでもオンにすると、一致した呼び出しはここで(またはあなたのスマートフォンで)承認または拒否を待ちます。

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ランタイムごとのさらなる例: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)。

## スター履歴

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ライセンス

MIT · [@vivekchand](https://github.com/vivekchand) が構築 · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
